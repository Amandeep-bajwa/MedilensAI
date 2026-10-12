import sys
import os
import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_patient():
    email = f"dash_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Dashboard Patient A",
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
def secondary_patient():
    email = f"dash_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Dashboard Patient B",
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

# ----------------- DASHBOARD TESTS -----------------

def test_dashboard_summary_metrics(auth_patient):
    headers = auth_patient["headers"]

    # 1. Initially empty summary
    res_empty = client.get("/api/dashboard/summary", headers=headers)
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["total_reports"] == 0
    assert data_empty["active_medications_count"] == 0
    assert data_empty["upcoming_appointments_count"] == 0
    assert data_empty["unread_notifications_count"] == 0

    # 2. Add an active medication
    client.post(
        "/api/medications",
        headers=headers,
        json={
            "medicine_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily morning",
            "start_date": str(date.today()),
            "end_date": None,
            "notes": "BP maintenance"
        }
    )

    # 3. Add an upcoming appointment
    client.post(
        "/api/appointments",
        headers=headers,
        json={
            "doctor_name": "Dr. Emily Watson",
            "specialization": "Cardiologist",
            "appointment_date": str(date.today() + timedelta(days=2)),
            "appointment_time": "11:00 AM",
            "location": "Cardiology Suite",
            "notes": "Follow-up",
            "status": "Upcoming"
        }
    )

    # 4. Add an unread notification
    client.post(
        "/api/notifications",
        headers=headers,
        json={
            "title": "Welcome Alert",
            "message": "Welcome to MediLens AI dashboard.",
            "type": "SYSTEM"
        }
    )

    # 5. Verify updated summary metrics
    res_updated = client.get("/api/dashboard/summary", headers=headers)
    assert res_updated.status_code == 200
    data_updated = res_updated.json()
    assert data_updated["active_medications_count"] == 1
    assert len(data_updated["active_medications"]) == 1
    assert data_updated["active_medications"][0]["medicine_name"] == "Lisinopril"
    assert data_updated["upcoming_appointments_count"] == 1
    assert len(data_updated["upcoming_appointments"]) == 1
    assert data_updated["upcoming_appointments"][0]["doctor_name"] == "Dr. Emily Watson"
    assert data_updated["unread_notifications_count"] == 1


def test_dashboard_multi_tenant_isolation(auth_patient, secondary_patient):
    headers_a = auth_patient["headers"]
    headers_b = secondary_patient["headers"]

    # User A creates a medication
    client.post(
        "/api/medications",
        headers=headers_a,
        json={
            "medicine_name": "Metformin",
            "dosage": "500mg",
            "frequency": "Twice daily",
            "start_date": str(date.today()),
            "end_date": None
        }
    )

    # User B queries dashboard summary -> must see 0 active meds
    res_b = client.get("/api/dashboard/summary", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["active_medications_count"] == 0
    assert len(data_b["active_medications"]) == 0


# ----------------- NOTIFICATIONS TESTS -----------------

def test_notifications_crud_and_read_state(auth_patient):
    headers = auth_patient["headers"]

    # 1. Create notification
    create_res = client.post(
        "/api/notifications",
        headers=headers,
        json={
            "title": "Report Processed",
            "message": "CBC Blood Test report has been processed successfully.",
            "type": "REPORT_PROCESSED",
            "link": "/reports/test-123"
        }
    )
    assert create_res.status_code == 201
    notif = create_res.json()
    notif_id = notif["notification_id"]
    assert notif["is_read"] is False

    # 2. List notifications
    list_res = client.get("/api/notifications", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert list_data["unread_count"] >= 1

    # 3. Mark single notification as read
    read_res = client.patch(f"/api/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 4. Delete notification
    del_res = client.delete(f"/api/notifications/{notif_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify 404 after deletion
    verify_res = client.patch(f"/api/notifications/{notif_id}/read", headers=headers)
    assert verify_res.status_code == 404


def test_notifications_mark_all_read(auth_patient):
    headers = auth_patient["headers"]

    # Create 2 unread notifications
    client.post(
        "/api/notifications",
        headers=headers,
        json={"title": "Notice 1", "message": "First alert message", "type": "INFO"}
    )
    client.post(
        "/api/notifications",
        headers=headers,
        json={"title": "Notice 2", "message": "Second alert message", "type": "INFO"}
    )

    # Mark all read
    mark_res = client.post("/api/notifications/mark-all-read", headers=headers)
    assert mark_res.status_code == 200

    # Verify unread count is 0
    list_res = client.get("/api/notifications?unread_only=true", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) == 0
    assert list_res.json()["unread_count"] == 0


def test_notifications_automated_reminders_generation(auth_patient):
    headers = auth_patient["headers"]
    today = date.today()

    # Create an upcoming appointment within 3 days
    client.post(
        "/api/appointments",
        headers=headers,
        json={
            "doctor_name": "Dr. Sarah Adams",
            "specialization": "Endocrinologist",
            "appointment_date": str(today + timedelta(days=1)),
            "appointment_time": "14:00",
            "location": "Diabetes Care Clinic",
            "status": "Upcoming"
        }
    )

    # Create an active medication
    client.post(
        "/api/medications",
        headers=headers,
        json={
            "medicine_name": "Atorvastatin",
            "dosage": "20mg",
            "frequency": "Once daily at night",
            "start_date": str(today),
            "end_date": None
        }
    )

    # Trigger automated reminders generation
    gen_res = client.post("/api/notifications/generate-reminders", headers=headers)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["generated_count"] >= 2

    # Verify notifications were created
    notifs_res = client.get("/api/notifications", headers=headers)
    assert notifs_res.status_code == 200
    notifs_items = notifs_res.json()["items"]
    types = [n["type"] for n in notifs_items]
    assert "APPOINTMENT_REMINDER" in types
    assert "MEDICATION_REMINDER" in types

    # Calling again should not create duplicate reminders
    dup_res = client.post("/api/notifications/generate-reminders", headers=headers)
    assert dup_res.status_code == 200
    assert dup_res.json()["generated_count"] == 0


def test_notifications_bola_isolation(auth_patient, secondary_patient):
    headers_a = auth_patient["headers"]
    headers_b = secondary_patient["headers"]

    # User A creates a notification
    res = client.post(
        "/api/notifications",
        headers=headers_a,
        json={"title": "Private User A Notice", "message": "Sensitive notice", "type": "INFO"}
    )
    assert res.status_code == 201
    notif_id = res.json()["notification_id"]

    # User B attempts to mark User A's notification as read -> expect 404
    b_read = client.patch(f"/api/notifications/{notif_id}/read", headers=headers_b)
    assert b_read.status_code == 404

    # User B attempts to delete User A's notification -> expect 404
    b_del = client.delete(f"/api/notifications/{notif_id}", headers=headers_b)
    assert b_del.status_code == 404
