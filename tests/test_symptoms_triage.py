import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_patient():
    email = f"symptom_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Symptom Patient",
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

def test_emergency_red_flag_cardiac(auth_patient):
    headers = auth_patient["headers"]

    res = client.post(
        "/api/symptoms/analyze",
        headers=headers,
        json={
            "symptoms": "Experiencing crushing chest pain radiating to left arm and jaw with profuse sweating",
            "duration": "30 minutes",
            "severity": 9
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triage_level"] == "EMERGENCY"
    assert data["is_emergency"] is True
    assert len(data["red_flags"]) >= 1
    assert "Acute Coronary Syndrome" in data["red_flags"][0]["urgency_reason"]
    assert "911" in data["red_flags"][0]["action_required"]
    assert data["recommended_specialist"] == "Cardiologist"
    assert "disclaimer" in data

def test_emergency_red_flag_stroke(auth_patient):
    headers = auth_patient["headers"]

    res = client.post(
        "/api/symptoms/analyze",
        headers=headers,
        json={
            "symptoms": "Sudden slurred speech, facial drooping on the right side and right arm weakness",
            "duration": "15 minutes",
            "severity": 10
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triage_level"] == "EMERGENCY"
    assert data["is_emergency"] is True
    assert any("Stroke" in rf["urgency_reason"] for rf in data["red_flags"])
    assert data["recommended_specialist"] == "Neurologist"

def test_urgent_symptom_triage(auth_patient):
    headers = auth_patient["headers"]

    res = client.post(
        "/api/symptoms/analyze",
        headers=headers,
        json={
            "symptoms": "High fever with shivering and severe abdominal pain in the lower right area",
            "duration": "2 days",
            "severity": 8
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triage_level"] == "URGENT"
    assert data["is_emergency"] is False
    assert len(data["possible_causes"]) > 0
    assert len(data["doctor_questions"]) > 0

def test_routine_symptom_triage(auth_patient):
    headers = auth_patient["headers"]

    res = client.post(
        "/api/symptoms/analyze",
        headers=headers,
        json={
            "symptoms": "Mild tension headache and nasal congestion after working long hours",
            "duration": "1 day",
            "severity": 3
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triage_level"] == "ROUTINE"
    assert data["is_emergency"] is False
    assert len(data["supportive_care_tips"]) >= 3
    assert len(data["doctor_questions"]) >= 2
    assert "disclaimer" in data

def test_get_common_symptoms():
    res = client.get("/api/symptoms/common")
    assert res.status_code == 200
    categories = res.json()
    assert len(categories) >= 4
    category_names = [c["category"] for c in categories]
    assert "Respiratory" in category_names
    assert "Cardiovascular" in category_names

def test_symptom_history_and_isolation(auth_patient):
    headers_a = auth_patient["headers"]

    # Patient A analyzes symptoms
    client.post(
        "/api/symptoms/analyze",
        headers=headers_a,
        json={"symptoms": "Occasional joint stiffness in the morning", "severity": 4}
    )

    # Check Patient A history
    res_a = client.get("/api/symptoms/history", headers=headers_a)
    assert res_a.status_code == 200
    history_a = res_a.json()
    assert len(history_a) >= 1
    assert "joint stiffness" in history_a[0]["symptoms"]

    # Register Patient B
    email_b = f"patient_b_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "Patient B",
        "email": email_b,
        "password": "Password123!"
    })
    login_b = client.post("/api/auth/login", json={
        "email": email_b,
        "password": "Password123!"
    })
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Patient B history should be empty (strict multi-tenant isolation)
    res_b = client.get("/api/symptoms/history", headers=headers_b)
    assert res_b.status_code == 200
    history_b = res_b.json()
    assert len(history_b) == 0
