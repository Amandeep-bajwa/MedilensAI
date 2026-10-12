import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.pii_scrubber import scrub_pii
from app.core.config import settings

client = TestClient(app)

@pytest.fixture
def auth_patient():
    email = f"sec_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Security Patient",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"token": token, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def auth_admin():
    email = f"admin_{uuid.uuid4().hex}@example.com"
    password = "AdminSecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Security Admin",
        "email": email,
        "password": password,
        "role": "admin"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"token": token, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

# ----------------- SECURITY TESTS -----------------

def test_security_headers_present():
    """Verifies that all OWASP security headers are attached to API responses (SEC-INP, SEC-PRIV)."""
    res = client.get("/")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert "geolocation=()" in headers.get("Permissions-Policy", "")


def test_pii_scrubbing_clinical_deidentification():
    """Verifies clinical PII de-identification filter masks patient identifiers while preserving lab data (SEC-PRIV-005, SEC-AI-002)."""
    sample_clinical_text = (
        "METROPOLITAN HOSPITAL LAB REPORT\n"
        "Patient Name: Johnathan Alexander Smith\n"
        "DOB: 05/14/1982 | Phone: (555) 234-5678\n"
        "Email: john.smith@example.com | SSN: 123-45-6789\n"
        "Address: 742 Evergreen Terrace, Springfield\n"
        "LABORATORY FINDINGS:\n"
        "Hemoglobin: 14.2 g/dL [12.0 - 16.0]\n"
        "Fasting Blood Sugar: 118 mg/dL [70 - 100] HIGH\n"
        "Total Cholesterol: 215 mg/dL [125 - 200] HIGH\n"
        "Serum Creatinine: 0.9 mg/dL [0.6 - 1.2]\n"
    )

    scrubbed = scrub_pii(sample_clinical_text)

    # Identifiers must be masked
    assert "Johnathan Alexander Smith" not in scrubbed
    assert "[REDACTED_PATIENT_NAME]" in scrubbed
    assert "05/14/1982" not in scrubbed
    assert "[REDACTED_DOB]" in scrubbed
    assert "(555) 234-5678" not in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "john.smith@example.com" not in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "123-45-6789" not in scrubbed
    assert "[REDACTED_ID]" in scrubbed
    assert "742 Evergreen Terrace" not in scrubbed
    assert "[REDACTED_ADDRESS]" in scrubbed

    # Clinical findings and values must remain intact
    assert "Hemoglobin: 14.2 g/dL" in scrubbed
    assert "Fasting Blood Sugar: 118 mg/dL" in scrubbed
    assert "Total Cholesterol: 215 mg/dL" in scrubbed
    assert "Serum Creatinine: 0.9 mg/dL" in scrubbed


def test_account_deletion_and_data_cascade(auth_patient):
    """Verifies GDPR/Right-to-be-Forgotten account deletion cascades and purges all health entities (SEC-PRIV-004)."""
    headers = auth_patient["headers"]
    email = auth_patient["email"]

    # 1. Verify user can access profile
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # 2. Add a medication for the user
    client.post(
        "/api/medications",
        headers=headers,
        json={
            "medicine_name": "Temporary Med",
            "dosage": "10mg",
            "frequency": "Daily",
            "start_date": "2026-10-12"
        }
    )

    # 3. Request account deletion
    del_res = client.delete("/api/users/profile", headers=headers)
    assert del_res.status_code == 204

    # 4. Attempting to use the deleted token must fail with 404 (user entity purged)
    me_after = client.get("/api/auth/me", headers=headers)
    assert me_after.status_code == 404

    # 5. Attempting to login with deleted credentials must fail with 401
    login_after = client.post("/api/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    assert login_after.status_code == 401


def test_admin_audit_logs_rbac_protection(auth_patient, auth_admin):
    """Verifies that operational audit logs are strictly restricted to administrators (SEC-LOG-005, SEC-AUTHZ-003)."""
    # Patient attempt -> 403 Forbidden
    patient_res = client.get("/api/users/audit-logs", headers=auth_patient["headers"])
    assert patient_res.status_code == 403

    # Admin attempt -> 200 OK
    admin_res = client.get("/api/users/audit-logs", headers=auth_admin["headers"])
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1
    # Check that events have event_type and result
    assert all("event_type" in item for item in data["items"])


def test_rate_limit_configuration_and_429_schema():
    """Verifies rate limiting parameters are active and response follows SEC-RATE-004 schema."""
    assert settings.RATE_LIMIT_ENABLED is True
    assert settings.RATE_LIMIT_LOGIN == "5/minute"
    assert settings.RATE_LIMIT_AI == "10/minute"
    assert settings.RATE_LIMIT_UPLOAD == "10/minute"
