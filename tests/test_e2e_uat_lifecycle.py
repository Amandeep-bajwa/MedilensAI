import sys
import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)

CLINICAL_TEST_PDF = b"""%PDF-1.4
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
<< /Length 220 >>
stream
BT
/F1 12 Tf
72 712 Td
(METROPOLITAN HOSPITAL - COMPREHENSIVE METABOLIC PANEL) Tj
0 -20 Td
(Patient Name: Jane Doe | DOB: 1988-04-12 | ID: 98765) Tj
0 -20 Td
(Hemoglobin: 14.2 g/dL [12.0 - 16.0]) Tj
0 -20 Td
(Fasting Blood Sugar: 126 mg/dL [70 - 100] HIGH) Tj
0 -20 Td
(Total Cholesterol: 215 mg/dL [125 - 200] HIGH) Tj
0 -20 Td
(Serum Creatinine: 0.9 mg/dL [0.6 - 1.2]) Tj
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
570
%%EOF"""

def test_e2e_patient_full_clinical_journey():
    """
    SRS Section 20.7: End-to-End User Acceptance Test (UAT)
    Simulates the complete 10-step patient clinical lifecycle:
    1. Registration
    2. Authentication & JWT Token Acquisition
    3. Medical Report Upload
    4. OCR Extraction & Biomarker Parsing
    5. AI Clinical Report Explanation
    6. Grounded RAG Q&A with Citation Validation
    7. Symptom Assessment & Emergency Screening
    8. Medication Entry & Adherence Tracking
    9. Clinical Doctor Appointment Scheduling
    10. Clinical Dashboard Aggregation Verification
    """
    # ----------------------------------------------------
    # Step 1: User Registration (FR-AUTH-001)
    # ----------------------------------------------------
    patient_email = f"uat_patient_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_payload = {
        "name": "Jane UAT Doe",
        "email": patient_email,
        "password": password
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    user_id = reg_res.json()["user"]["user_id"]
    assert user_id is not None

    # ----------------------------------------------------
    # Step 2: Login & Session Authentication (FR-AUTH-002)
    # ----------------------------------------------------
    login_res = client.post("/api/auth/login", json={
        "email": patient_email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify session profile identity
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == patient_email

    # ----------------------------------------------------
    # Step 3: Medical Report Upload (FR-REP-001, FR-REP-002)
    # ----------------------------------------------------
    pdf_file = io.BytesIO(CLINICAL_TEST_PDF)
    upload_res = client.post(
        "/api/reports/upload",
        headers=auth_headers,
        files={"file": ("metabolic_panel.pdf", pdf_file, "application/pdf")}
    )
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    report_data = upload_res.json()
    report_id = report_data["report_id"]
    assert report_data["file_name"] == "metabolic_panel.pdf"
    assert report_data["processing_status"] == "Uploaded"

    # ----------------------------------------------------
    # Step 4: OCR Processing & Biomarker Parsing (FR-OCR-001, FR-OCR-002)
    # ----------------------------------------------------
    ocr_res = client.post(f"/api/reports/{report_id}/ocr/process", headers=auth_headers)
    assert ocr_res.status_code == 200, f"OCR processing failed: {ocr_res.text}"
    ocr_data = ocr_res.json()
    assert ocr_data["status"] == "Completed"
    assert "Hemoglobin" in ocr_data["extracted_text"]
    assert len(ocr_data["parameters"]) >= 1

    # Verify report status transitioned to Completed
    report_detail_res = client.get(f"/api/reports/{report_id}", headers=auth_headers)
    assert report_detail_res.status_code == 200
    assert report_detail_res.json()["processing_status"] == "Completed"

    # ----------------------------------------------------
    # Step 5: AI Clinical Report Explanation (FR-AI-001, FR-AI-003)
    # ----------------------------------------------------
    ai_res = client.post(f"/api/reports/{report_id}/explain", headers=auth_headers)
    assert ai_res.status_code == 200, f"AI explanation failed: {ai_res.text}"
    ai_data = ai_res.json()
    assert ai_data["report_id"] == report_id
    assert len(ai_data["summary"]) > 0
    # Must enforce safety disclaimer requirement
    assert len(ai_data["disclaimer"]) > 0

    # ----------------------------------------------------
    # Step 6: Grounded RAG Report Q&A (FR-RAG-001, FR-RAG-002)
    # ----------------------------------------------------
    rag_res = client.post(
        f"/api/reports/{report_id}/rag/query",
        headers=auth_headers,
        json={"question": "What does my Fasting Blood Sugar level indicate?"}
    )
    assert rag_res.status_code == 200, f"RAG Q&A failed: {rag_res.text}"
    rag_data = rag_res.json()
    assert "answer" in rag_data
    assert len(rag_data["answer"]) > 0
    assert isinstance(rag_data["citations"], list)
    assert rag_data["disclaimer"] is not None

    # ----------------------------------------------------
    # Step 7: Symptom Assessment & Triage (FR-SYM-001, FR-SYM-002)
    # ----------------------------------------------------
    symptom_res = client.post(
        "/api/symptoms/analyze",
        headers=auth_headers,
        json={
            "symptoms": "Mild occasional headache for the past 2 days after staring at computer screens.",
            "duration": "2 days",
            "severity": 3
        }
    )
    assert symptom_res.status_code == 200, f"Symptom triage failed: {symptom_res.text}"
    triage_data = symptom_res.json()
    assert triage_data["is_emergency"] is False
    assert triage_data["triage_level"] in ["ROUTINE", "URGENT", "SELF_CARE", "EMERGENCY"]
    assert "disclaimer" in triage_data

    # ----------------------------------------------------
    # Step 8: Prescription Medication Logging (FR-MED-001, FR-MED-002)
    # ----------------------------------------------------
    med_res = client.post(
        "/api/medications",
        headers=auth_headers,
        json={
            "medicine_name": "Metformin",
            "dosage": "500mg",
            "frequency": "Twice daily with meals",
            "start_date": "2026-10-12",
            "notes": "Prescribed for elevated fasting blood glucose management"
        }
    )
    assert med_res.status_code == 201, f"Medication creation failed: {med_res.text}"
    med_data = med_res.json()
    med_id = med_data["medication_id"]
    assert med_data["is_active"] is True

    # ----------------------------------------------------
    # Step 9: Doctor Appointment Scheduling (FR-APT-001, FR-APT-002)
    # ----------------------------------------------------
    apt_res = client.post(
        "/api/appointments",
        headers=auth_headers,
        json={
            "doctor_name": "Dr. Sarah Jenkins",
            "specialization": "Endocrinology",
            "appointment_date": "2026-10-25",
            "appointment_time": "10:30 AM",
            "location": "Metropolitan Medical Center, Room 402",
            "notes": "Follow-up consultation regarding fasting blood sugar and metabolic panel"
        }
    )
    assert apt_res.status_code == 201, f"Appointment scheduling failed: {apt_res.text}"
    apt_data = apt_res.json()
    apt_id = apt_data["appointment_id"]
    assert apt_data["status"] == "Upcoming"

    # ----------------------------------------------------
    # Step 10: Clinical Dashboard Aggregation Verification (FR-DASH-001)
    # ----------------------------------------------------
    dash_res = client.get("/api/dashboard/summary", headers=auth_headers)
    assert dash_res.status_code == 200, f"Dashboard retrieval failed: {dash_res.text}"
    dash = dash_res.json()

    assert dash["total_reports"] >= 1
    assert dash["reports_by_status"]["Completed"] >= 1
    assert dash["active_medications_count"] >= 1
    assert dash["upcoming_appointments_count"] >= 1
    assert len(dash["recent_reports"]) >= 1
    assert len(dash["active_medications"]) >= 1
    assert len(dash["upcoming_appointments"]) >= 1
    assert len(dash["recent_ai_activity"]) >= 1

    # Clean up created resources
    del_apt = client.delete(f"/api/appointments/{apt_id}", headers=auth_headers)
    assert del_apt.status_code == 204

    del_med = client.delete(f"/api/medications/{med_id}", headers=auth_headers)
    assert del_med.status_code == 204

    del_rep = client.delete(f"/api/reports/{report_id}", headers=auth_headers)
    assert del_rep.status_code in [200, 204]


def test_e2e_cross_tenant_isolation_boundary():
    """
    SRS Section 20.3 & 20.7: Cross-tenant isolation security verification.
    Ensures Patient B cannot inspect, mutate, or delete Patient A's assets.
    """
    # Create Patient A
    email_a = f"patient_a_{uuid.uuid4().hex}@example.com"
    pwd = "SecurePassword123!"
    reg_a = client.post("/api/auth/register", json={"name": "Patient A", "email": email_a, "password": pwd})
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create Patient B
    email_b = f"patient_b_{uuid.uuid4().hex}@example.com"
    reg_b = client.post("/api/auth/register", json={"name": "Patient B", "email": email_b, "password": pwd})
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Patient A creates a medication and appointment
    med_res = client.post("/api/medications", headers=headers_a, json={
        "medicine_name": "Confidential Med",
        "dosage": "50mg",
        "frequency": "Daily",
        "start_date": "2026-10-12"
    })
    med_id_a = med_res.json()["medication_id"]

    apt_res = client.post("/api/appointments", headers=headers_a, json={
        "doctor_name": "Dr. Confidential",
        "specialization": "Neurology",
        "appointment_date": "2026-10-28",
        "appointment_time": "09:00 AM"
    })
    apt_id_a = apt_res.json()["appointment_id"]

    # Patient B attempts unauthorized access to Patient A's resources
    get_med_b = client.get(f"/api/medications/{med_id_a}", headers=headers_b)
    assert get_med_b.status_code == 404, "BOLA violation: Patient B retrieved Patient A's medication"

    del_med_b = client.delete(f"/api/medications/{med_id_a}", headers=headers_b)
    assert del_med_b.status_code == 404, "BOLA violation: Patient B deleted Patient A's medication"

    del_apt_b = client.delete(f"/api/appointments/{apt_id_a}", headers=headers_b)
    assert del_apt_b.status_code == 404, "BOLA violation: Patient B deleted Patient A's appointment"

    # Verify Patient A's medication still exists untouched
    get_med_a = client.get(f"/api/medications/{med_id_a}", headers=headers_a)
    assert get_med_a.status_code == 200
