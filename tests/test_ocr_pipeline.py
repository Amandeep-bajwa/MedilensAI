import sys
import os
import io
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import SessionLocal
from app.models.entities import User, Report, OCR, ReportChunk, AuditLog
from app.services.ocr import clean_extracted_text, parse_clinical_lab_parameters

client = TestClient(app)

# Dummy clinical lab report PDF content containing real lab findings
CLINICAL_PDF_CONTENT = b"""%PDF-1.4
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
(METROPOLITAN CLINICAL LABORATORIES - DIAGNOSTIC REPORT) Tj
0 -20 Td
(Patient Name: Jane Doe | Age: 34 | Gender: Female) Tj
0 -20 Td
(Hemoglobin: 14.2 g/dL [12.0 - 16.0]) Tj
0 -20 Td
(Fasting Blood Sugar: 118 mg/dL [70 - 100]) Tj
0 -20 Td
(Total Cholesterol: 215 mg/dL [125 - 200]) Tj
0 -20 Td
(Serum Creatinine: 0.9 mg/dL [0.6 - 1.2]) Tj
0 -20 Td
(Platelets: 130 x10^3/mcL [150 - 450]) Tj
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
    email = f"ocr_patient_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "OCR Patient",
        "email": email,
        "password": "Password123!",
        "role": "user"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"token": token, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def auth_other_user():
    email = f"ocr_other_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "Other User",
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
            db.query(ReportChunk).delete()
            db.query(OCR).delete()
            db.query(Report).delete()
            db.query(AuditLog).delete()
            db.query(User).filter(User.email.like("%ocr%@example.com")).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    do_cleanup()
    yield
    do_cleanup()

def test_text_cleaning_unit():
    raw_dirty = "Clinical Report\r\nLine 1\xa0\xa0Value: 12\x00\x01\n\n\n\nLine 2   "
    cleaned = clean_extracted_text(raw_dirty)
    assert "\r" not in cleaned
    assert "\x00" not in cleaned
    assert "Line 1  Value: 12" in cleaned
    assert "\n\n\n" not in cleaned

def test_clinical_lab_parameter_parsing():
    sample_text = """
    Hemoglobin: 14.2 g/dL (12.0 - 16.0)
    Fasting Blood Sugar: 120 mg/dL (70 - 100)
    Platelets: 110 x10^3/mcL (150 - 450)
    Serum Creatinine: 0.8 mg/dL (0.6 - 1.2)
    """
    params = parse_clinical_lab_parameters(sample_text)
    assert len(params) >= 3

    # Hemoglobin normal check
    hb = next((p for p in params if "hemoglobin" in p.name.lower()), None)
    assert hb is not None
    assert hb.value == "14.2"
    assert hb.status == "NORMAL"

    # Blood sugar high check
    bs = next((p for p in params if "blood sugar" in p.name.lower() or "glucose" in p.name.lower()), None)
    assert bs is not None
    assert bs.value == "120"
    assert bs.status == "HIGH"

    # Platelets low check
    plt = next((p for p in params if "platelet" in p.name.lower()), None)
    assert plt is not None
    assert plt.value == "110"
    assert plt.status == "LOW"

def test_ocr_process_full_lifecycle(auth_patient):
    # Step 1: Upload Report
    files = {
        "file": ("lab_cbc_panel.pdf", io.BytesIO(CLINICAL_PDF_CONTENT), "application/pdf")
    }
    up_res = client.post("/api/reports/upload", files=files, data={"category": "CBC"}, headers=auth_patient["headers"])
    assert up_res.status_code == 201
    report_id = up_res.json()["report_id"]

    # Step 2: Trigger OCR Processing
    proc_res = client.post(f"/api/reports/{report_id}/ocr/process", headers=auth_patient["headers"])
    assert proc_res.status_code == 200
    ocr_data = proc_res.json()
    assert ocr_data["status"] == "Completed"
    assert ocr_data["confidence"] >= 0.80
    assert ocr_data["total_chunks"] >= 1
    assert "Hemoglobin" in ocr_data["extracted_text"] or len(ocr_data["extracted_text"]) > 10

    # Step 3: Verify Report Status in DB is Completed
    rep_res = client.get(f"/api/reports/{report_id}", headers=auth_patient["headers"])
    assert rep_res.status_code == 200
    assert rep_res.json()["processing_status"] == "Completed"

    # Step 4: Retrieve OCR Data via GET
    get_ocr = client.get(f"/api/reports/{report_id}/ocr", headers=auth_patient["headers"])
    assert get_ocr.status_code == 200
    assert get_ocr.json()["ocr_id"] == ocr_data["ocr_id"]

    # Step 5: Retrieve Chunks via GET
    chunks_res = client.get(f"/api/reports/{report_id}/chunks", headers=auth_patient["headers"])
    assert chunks_res.status_code == 200
    assert chunks_res.json()["total_chunks"] >= 1
    assert len(chunks_res.json()["chunks"]) >= 1

def test_ocr_bola_security_isolation(auth_patient, auth_other_user):
    # Patient uploads report
    files = {
        "file": ("confidential_report.pdf", io.BytesIO(CLINICAL_PDF_CONTENT), "application/pdf")
    }
    up_res = client.post("/api/reports/upload", files=files, headers=auth_patient["headers"])
    report_id = up_res.json()["report_id"]

    # Other user attempts to trigger OCR on patient's report
    unauth_proc = client.post(f"/api/reports/{report_id}/ocr/process", headers=auth_other_user["headers"])
    assert unauth_proc.status_code == 404

    # Other user attempts to get OCR results
    unauth_get = client.get(f"/api/reports/{report_id}/ocr", headers=auth_other_user["headers"])
    assert unauth_get.status_code == 404

    # Other user attempts to get chunks
    unauth_chunks = client.get(f"/api/reports/{report_id}/chunks", headers=auth_other_user["headers"])
    assert unauth_chunks.status_code == 404
