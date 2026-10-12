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
    email = f"patient_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Health Patient A",
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
    email = f"patient_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Health Patient B",
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

# ----------------- MEDICATION TESTS -----------------

def test_medication_crud_and_active_status(auth_patient):
    headers = auth_patient["headers"]
    today = date.today()
    tomorrow = today + timedelta(days=1)
    past_date = today - timedelta(days=10)
    past_end = today - timedelta(days=2)

    # 1. Create active medication (end_date in future)
    med1_res = client.post(
        "/api/medications",
        headers=headers,
        json={
            "medicine_name": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Three times daily with food",
            "start_date": str(today),
            "end_date": str(tomorrow),
            "notes": "Complete full 10-day course"
        }
    )
    assert med1_res.status_code == 201
    med1 = med1_res.json()
    assert med1["medicine_name"] == "Amoxicillin"
    assert med1["is_active"] is True
    med1_id = med1["medication_id"]

    # 2. Create expired medication (end_date in past)
    med2_res = client.post(
        "/api/medications",
        headers=headers,
        json={
            "medicine_name": "Ibuprofen",
            "dosage": "400mg",
            "frequency": "As needed for pain",
            "start_date": str(past_date),
            "end_date": str(past_end),
            "notes": "Short course for post-injury inflammation"
        }
    )
    assert med2_res.status_code == 201
    med2 = med2_res.json()
    assert med2["is_active"] is False

    # 3. List all medications
    all_res = client.get("/api/medications", headers=headers)
    assert all_res.status_code == 200
    all_data = all_res.json()
    assert all_data["total"] >= 2

    # 4. List only active medications
    active_res = client.get("/api/medications?active_only=true", headers=headers)
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert all(item["is_active"] is True for item in active_data["items"])

    # 5. Get single medication by ID
    get_res = client.get(f"/api/medications/{med1_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["medicine_name"] == "Amoxicillin"

    # 6. Update medication dosage
    update_res = client.put(
        f"/api/medications/{med1_id}",
        headers=headers,
        json={"dosage": "875mg", "notes": "Increased dosage per doctor instruction"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["dosage"] == "875mg"

    # 7. Delete medication
    del_res = client.delete(f"/api/medications/{med1_id}", headers=headers)
    assert del_res.status_code == 204

    # 8. Verify 404 after deletion
    verify_res = client.get(f"/api/medications/{med1_id}", headers=headers)
    assert verify_res.status_code == 404


def test_medication_bola_isolation(auth_patient, secondary_patient):
    headers_a = auth_patient["headers"]
    headers_b = secondary_patient["headers"]

    # User A creates a medication
    res = client.post(
        "/api/medications",
        headers=headers_a,
        json={
            "medicine_name": "Atorvastatin",
            "dosage": "20mg",
            "frequency": "Once daily at bedtime",
            "start_date": str(date.today()),
            "end_date": None,
            "notes": "Lipid management"
        }
    )
    assert res.status_code == 201
    med_id = res.json()["medication_id"]

    # User B attempts to read User A's medication -> expect 404 (BOLA masking)
    b_read = client.get(f"/api/medications/{med_id}", headers=headers_b)
    assert b_read.status_code == 404

    # User B attempts to update User A's medication -> expect 404
    b_update = client.put(
        f"/api/medications/{med_id}",
        headers=headers_b,
        json={"dosage": "40mg"}
    )
    assert b_update.status_code == 404

    # User B attempts to delete User A's medication -> expect 404
    b_delete = client.delete(f"/api/medications/{med_id}", headers=headers_b)
    assert b_delete.status_code == 404


# ----------------- APPOINTMENT TESTS -----------------

def test_appointment_lifecycle_and_filtering(auth_patient):
    headers = auth_patient["headers"]
    appt_date = date.today() + timedelta(days=7)

    # 1. Schedule appointment
    create_res = client.post(
        "/api/appointments",
        headers=headers,
        json={
            "doctor_name": "Dr. Sarah Jenkins",
            "specialization": "Cardiologist",
            "appointment_date": str(appt_date),
            "appointment_time": "10:30 AM",
            "location": "St. Jude Heart Center, Suite 402",
            "notes": "Comprehensive cardiovascular follow-up",
            "status": "Upcoming"
        }
    )
    assert create_res.status_code == 201
    appt = create_res.json()
    assert appt["doctor_name"] == "Dr. Sarah Jenkins"
    assert appt["status"] == "Upcoming"
    appt_id = appt["appointment_id"]

    # 2. List appointments filtered by Upcoming
    list_res = client.get("/api/appointments?status=Upcoming", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert any(a["appointment_id"] == appt_id for a in list_data["items"])

    # 3. Retrieve single appointment
    single_res = client.get(f"/api/appointments/{appt_id}", headers=headers)
    assert single_res.status_code == 200
    assert single_res.json()["specialization"] == "Cardiologist"

    # 4. Update appointment status to Completed
    update_res = client.put(
        f"/api/appointments/{appt_id}",
        headers=headers,
        json={
            "status": "Completed",
            "notes": "Consultation completed. Recommended lipid panel recheck in 3 months."
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Completed"

    # 5. List with Completed filter
    completed_res = client.get("/api/appointments?status=Completed", headers=headers)
    assert completed_res.status_code == 200
    assert any(a["appointment_id"] == appt_id for a in completed_res.json()["items"])

    # 6. Delete appointment
    del_res = client.delete(f"/api/appointments/{appt_id}", headers=headers)
    assert del_res.status_code == 204

    # 7. Verify 404 after deletion
    verify_res = client.get(f"/api/appointments/{appt_id}", headers=headers)
    assert verify_res.status_code == 404


def test_appointment_bola_isolation(auth_patient, secondary_patient):
    headers_a = auth_patient["headers"]
    headers_b = secondary_patient["headers"]
    appt_date = date.today() + timedelta(days=3)

    # User A schedules appointment
    res = client.post(
        "/api/appointments",
        headers=headers_a,
        json={
            "doctor_name": "Dr. Marcus Bell",
            "specialization": "Endocrinologist",
            "appointment_date": str(appt_date),
            "appointment_time": "14:15",
            "location": "Metabolic Care Center",
            "notes": "HbA1c evaluation",
            "status": "Upcoming"
        }
    )
    assert res.status_code == 201
    appt_id = res.json()["appointment_id"]

    # User B attempts to read User A's appointment -> expect 404
    b_read = client.get(f"/api/appointments/{appt_id}", headers=headers_b)
    assert b_read.status_code == 404

    # User B attempts to update User A's appointment -> expect 404
    b_update = client.put(
        f"/api/appointments/{appt_id}",
        headers=headers_b,
        json={"status": "Cancelled"}
    )
    assert b_update.status_code == 404

    # User B attempts to delete User A's appointment -> expect 404
    b_delete = client.delete(f"/api/appointments/{appt_id}", headers=headers_b)
    assert b_delete.status_code == 404
