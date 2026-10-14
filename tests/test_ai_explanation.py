import sys
import os
import io
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import SessionLocal
from app.models.entities import User, Report, OCR, ReportChunk, AIInteraction, AuditLog

client = TestClient(app)

CLINICAL_REPORT_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
72 712 Td
(METROPOLITAN DIAGNOSTICS - CLINICAL PATHOLOGY) Tj
0 -20 Td
(Patient Name: Alex Mercer | Age: 42 | Gender: Male) Tj
0 -20 Td
(Hemoglobin: 14.5 g/dL [12.0 - 16.0]) Tj
0 -20 Td
(Fasting Blood Sugar: 135 mg/dL [70 - 100]) Tj
0 -20 Td
(Platelets: 105 x10^3/mcL [150 - 450]) Tj
0 -20 Td
(Total Cholesterol: 220 mg/dL [125 - 200]) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000216 00000 n 
0000000293 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
550
%%EOF"""

import uuid

@pytest.fixture
def auth_patient():
    email = f"ai_patient_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "Alex Mercer",
        "email": email,
        "password": "Password123!",
        "role": "user"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"token": token, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def auth_intruder():
    email = f"ai_intruder_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "Intruder User",
        "email": email,
        "password": "Password123!",
        "role": "user"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"token": token, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture(autouse=True)
def cleanup():
    def do_cleanup():
        db = SessionLocal()
        try:
            reports = db.query(Report).all()
            for r in reports:
                if r.file_path and os.path.exists(r.file_path):
                    try:
                        os.remove(r.file_path)
                    except OSError:
                        pass
            db.query(AIInteraction).delete()
            db.query(ReportChunk).delete()
            db.query(OCR).delete()
            db.query(Report).delete()
            db.query(AuditLog).delete()
            db.query(User).filter(User.email.like("%ai_%@example.com")).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    do_cleanup()
    yield
    do_cleanup()

def test_generate_ai_explanation_success(auth_patient):
    # Step 1: Upload Report
    files = {
        "file": ("blood_panel.pdf", io.BytesIO(CLINICAL_REPORT_BYTES), "application/pdf")
    }
    up_res = client.post("/api/reports/upload", files=files, data={"category": "Lipid & Metabolic"}, headers=auth_patient["headers"])
    assert up_res.status_code == 201
    report_id = up_res.json()["report_id"]

    # Step 2: Trigger AI Report Explanation
    exp_res = client.post(
        f"/api/reports/{report_id}/explain",
        json={"focus_areas": "Metabolic health and blood sugar"},
        headers=auth_patient["headers"]
    )
    assert exp_res.status_code == 200
    data = exp_res.json()

    assert data["report_id"] == report_id
    assert len(data["summary"]) > 20
    assert len(data["doctor_questions"]) >= 3
    assert "MediLens AI is an educational clinical assistant" in data["disclaimer"]

    # Verify abnormal findings detected
    abnormal_names = [a["parameter_name"].lower() for a in data["abnormal_findings"]]
    assert any("sugar" in name or "glucose" in name for name in abnormal_names)
    assert any("platelet" in name for name in abnormal_names)

    # Check database persistence
    db = SessionLocal()
    try:
        interaction = db.query(AIInteraction).filter(AIInteraction.report_id == report_id).first()
        assert interaction is not None
        audit = db.query(AuditLog).filter(AuditLog.event_type == "AI_EXPLANATION_GENERATED").first()
        assert audit is not None
    finally:
        db.close()

def test_get_existing_or_ondemand_explanation(auth_patient):
    files = {
        "file": ("panel.pdf", io.BytesIO(CLINICAL_REPORT_BYTES), "application/pdf")
    }
    up_res = client.post("/api/reports/upload", files=files, headers=auth_patient["headers"])
    report_id = up_res.json()["report_id"]

    # Request explanation directly via GET (triggers on-demand if none exists)
    get_res = client.get(f"/api/reports/{report_id}/explanation", headers=auth_patient["headers"])
    assert get_res.status_code == 200
    assert len(get_res.json()["summary"]) > 20

def test_ask_question_about_report(auth_patient):
    files = {
        "file": ("metabolic.pdf", io.BytesIO(CLINICAL_REPORT_BYTES), "application/pdf")
    }
    up_res = client.post("/api/reports/upload", files=files, headers=auth_patient["headers"])
    report_id = up_res.json()["report_id"]

    # Ask specific question regarding blood sugar
    ask_res = client.post(
        f"/api/reports/{report_id}/ask",
        json={"question": "What is my fasting blood sugar level?"},
        headers=auth_patient["headers"]
    )
    assert ask_res.status_code == 200
    ans_data = ask_res.json()
    assert "blood sugar" in ans_data["answer"].lower() or "glucose" in ans_data["answer"].lower()
    assert "disclaimer" in ans_data

def test_ai_bola_isolation(auth_patient, auth_intruder):
    files = {
        "file": ("confidential_patient.pdf", io.BytesIO(CLINICAL_REPORT_BYTES), "application/pdf")
    }
    up_res = client.post("/api/reports/upload", files=files, headers=auth_patient["headers"])
    report_id = up_res.json()["report_id"]

    # Intruder calls explain -> 404
    unauth_exp = client.post(f"/api/reports/{report_id}/explain", headers=auth_intruder["headers"])
    assert unauth_exp.status_code == 404

    # Intruder calls get explanation -> 404
    unauth_get = client.get(f"/api/reports/{report_id}/explanation", headers=auth_intruder["headers"])
    assert unauth_get.status_code == 404

    # Intruder calls ask -> 404
    unauth_ask = client.post(
        f"/api/reports/{report_id}/ask",
        json={"question": "What are the patient's results?"},
        headers=auth_intruder["headers"]
    )
    assert unauth_ask.status_code == 404
