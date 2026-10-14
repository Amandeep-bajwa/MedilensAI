import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend package resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import SessionLocal
from app.models.entities import User, AuditLog

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_users():
    """Ensure test users are cleaned up before and after tests."""
    def do_clean():
        db = SessionLocal()
        try:
            db.query(AuditLog).filter(
                (AuditLog.user_id.in_(
                    db.query(User.user_id).filter(User.email.like("%test%@example.com"))
                ))
            ).delete(synchronize_session=False)
            db.query(User).filter(User.email.like("%test%@example.com")).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    do_clean()
    yield
    do_clean()

def test_user_registration_success():
    payload = {
        "name": "Jane Doe",
        "email": "testjane@example.com",
        "password": "Password123!",
        "role": "user"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "testjane@example.com"
    assert data["user"]["role"] == "user"

def test_user_registration_duplicate_email():
    payload = {
        "name": "Jane Duplicate",
        "email": "testduplicate@example.com",
        "password": "Password123!"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

def test_login_success_and_failure():
    email = "testauth@example.com"
    password = "CorrectPassword123!"
    
    # Register user first
    reg = client.post("/api/auth/register", json={
        "name": "Auth Tester",
        "email": email,
        "password": password
    })
    assert reg.status_code == 201

    # Login with right credentials
    login_ok = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_ok.status_code == 200
    token = login_ok.json()["access_token"]
    assert token is not None

    # Login with wrong password
    login_bad = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword999!"
    })
    assert login_bad.status_code == 401
    assert login_bad.json()["error"]["code"] == "INVALID_CREDENTIALS"

def test_auth_me_endpoint():
    email = "testme@example.com"
    reg = client.post("/api/auth/register", json={
        "name": "Me Tester",
        "email": email,
        "password": "Password123!"
    })
    token = reg.json()["access_token"]

    # Request without token
    unauth = client.get("/api/auth/me")
    assert unauth.status_code == 401

    # Request with Bearer token
    auth_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_res.status_code == 200
    assert auth_res.json()["email"] == email
    assert auth_res.json()["name"] == "Me Tester"

def test_password_change_flow():
    email = "testpw@example.com"
    old_pw = "OldPassword123!"
    new_pw = "NewSecretPassword456!"

    reg = client.post("/api/auth/register", json={
        "name": "Password Changer",
        "email": email,
        "password": old_pw
    })
    token = reg.json()["access_token"]

    # Attempt change with incorrect current password
    bad_change = client.post(
        "/api/auth/change-password",
        json={"current_password": "WrongCurrentPassword!", "new_password": new_pw},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_change.status_code == 400
    assert bad_change.json()["error"]["code"] == "INVALID_PASSWORD"

    # Successful password change
    ok_change = client.post(
        "/api/auth/change-password",
        json={"current_password": old_pw, "new_password": new_pw},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ok_change.status_code == 200

    # Verify old password fails and new password works
    fail_login = client.post("/api/auth/login", json={"email": email, "password": old_pw})
    assert fail_login.status_code == 401

    succ_login = client.post("/api/auth/login", json={"email": email, "password": new_pw})
    assert succ_login.status_code == 200

def test_rbac_admin_protection():
    # Register standard user
    user_reg = client.post("/api/auth/register", json={
        "name": "Regular User",
        "email": "testuser@example.com",
        "password": "Password123!",
        "role": "user"
    })
    user_token = user_reg.json()["access_token"]

    # Register admin user
    admin_reg = client.post("/api/auth/register", json={
        "name": "Admin User",
        "email": "testadmin@example.com",
        "password": "Password123!",
        "role": "admin"
    })
    admin_token = admin_reg.json()["access_token"]

    # Regular user trying to access admin endpoint /api/users/
    forbidden_res = client.get("/api/users/", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # Admin user accessing admin endpoint /api/users/
    admin_res = client.get("/api/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)

def test_user_profile_crud():
    reg = client.post("/api/auth/register", json={
        "name": "Profile User",
        "email": "testprofile@example.com",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]

    # Get profile
    prof_res = client.get("/api/users/profile", headers={"Authorization": f"Bearer {token}"})
    assert prof_res.status_code == 200
    prof_data = prof_res.json()
    assert prof_data["name"] == "Profile User"
    assert prof_data["total_reports"] == 0

    # Update profile
    upd_res = client.put(
        "/api/users/profile",
        json={"name": "Updated Profile Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["name"] == "Updated Profile Name"
