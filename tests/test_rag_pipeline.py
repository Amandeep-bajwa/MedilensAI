import sys
import os
import io
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)


def create_sample_lab_pdf() -> bytes:
    """Generates an in-memory clinical lab report PDF for testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()

SAMPLE_CLINICAL_TEXT = (
    "METABOLIC & LIPID CLINICAL PANEL\n"
    "Patient: John Doe | Age: 42 | Gender: Male\n"
    "Fasting Blood Sugar: 142 mg/dL (Normal Range: 70 - 99 mg/dL) [HIGH]\n"
    "Serum Creatinine: 1.1 mg/dL (Normal Range: 0.6 - 1.2 mg/dL) [NORMAL]\n"
    "Total Cholesterol: 245 mg/dL (Normal Range: 125 - 200 mg/dL) [HIGH]\n"
    "Hemoglobin: 14.5 g/dL (Normal Range: 13.8 - 17.2 g/dL) [NORMAL]\n"
    "Platelet Count: 230 x10^3/uL (Normal Range: 150 - 450 x10^3/uL) [NORMAL]\n"
    "Clinical Notes: Elevated fasting blood glucose indicates impaired fasting glycaemia. "
    "Total cholesterol is elevated. Patient advised to adopt dietary lifestyle changes."
)

import uuid

@pytest.fixture
def test_user_and_token():
    email = f"rag_patient_{uuid.uuid4().hex}@example.com"
    password = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "RAG Patient",
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
    return token

@pytest.fixture
def uploaded_and_chunked_report(test_user_and_token):
    token = test_user_and_token
    pdf_bytes = create_sample_lab_pdf()

    upload_res = client.post(
        "/api/reports/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("metabolic_panel.pdf", pdf_bytes, "application/pdf")},
        data={"category": "Blood Glucose"}
    )
    assert upload_res.status_code == 201
    report_id = upload_res.json()["report_id"]

    # We manually simulate OCR chunk generation by invoking OCR or setting chunks
    ocr_res = client.post(
        f"/api/reports/{report_id}/ocr/process",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ocr_res.status_code == 200

    # Ensure chunk with clinical text exists in database
    from app.core.database import SessionLocal
    from app.models.entities import ReportChunk
    db = SessionLocal()
    chunk = ReportChunk(
        report_id=report_id,
        chunk_text=SAMPLE_CLINICAL_TEXT,
        page_number="1",
        embedding_reference="seed_dense_v1"
    )
    db.add(chunk)
    db.commit()
    db.close()

    return report_id, token

def test_rag_query_with_citations_success(uploaded_and_chunked_report):
    report_id, token = uploaded_and_chunked_report

    res = client.post(
        f"/api/reports/{report_id}/rag/query",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What is my fasting blood sugar level and is it high?",
            "top_k": 3
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["report_id"] == report_id
    assert data["is_grounded"] is True
    assert data["confidence_score"] > 0.1
    assert "Fasting Blood Sugar" in data["answer"] or "sugar" in data["answer"].lower()
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["page_number"] == "1"
    assert "disclaimer" in data
    assert "MediLens AI" in data["disclaimer"]

def test_rag_query_refusal_for_unrelated_topic(uploaded_and_chunked_report):
    report_id, token = uploaded_and_chunked_report

    res = client.post(
        f"/api/reports/{report_id}/rag/query",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What were the findings of my brain MRI lumbar spine scan?",
            "top_k": 3
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_grounded"] is False
    assert "no direct record or mention" in data["answer"].lower()

def test_rag_index_status_and_reindex(uploaded_and_chunked_report):
    report_id, token = uploaded_and_chunked_report

    # Check status
    status_res = client.get(
        f"/api/reports/{report_id}/rag/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["report_id"] == report_id
    assert status_data["total_chunks"] >= 1
    assert status_data["status"] == "Indexed"

    # Trigger reindex
    reindex_res = client.post(
        f"/api/reports/{report_id}/rag/reindex",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert reindex_res.status_code == 200
    reindex_data = reindex_res.json()
    assert reindex_data["report_id"] == report_id
    assert reindex_data["indexed_count"] >= 1

def test_rag_history_retrieval(uploaded_and_chunked_report):
    report_id, token = uploaded_and_chunked_report

    # Post a question
    client.post(
        f"/api/reports/{report_id}/rag/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What is my cholesterol level?"}
    )

    # Fetch history
    history_res = client.get(
        f"/api/reports/{report_id}/rag/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert history_res.status_code == 200
    history_items = history_res.json()
    assert len(history_items) >= 1
    assert any("cholesterol" in item["question"].lower() for item in history_items)

def test_rag_bola_isolation(uploaded_and_chunked_report):
    report_id, _ = uploaded_and_chunked_report

    # Register an attacker user
    attacker_email = f"attacker_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "Attacker",
        "email": attacker_email,
        "password": "Password123!"
    })
    login_res = client.post("/api/auth/login", json={
        "email": attacker_email,
        "password": "Password123!"
    })
    attacker_token = login_res.json()["access_token"]

    # Attacker tries to query report
    unauth_res = client.post(
        f"/api/reports/{report_id}/rag/query",
        headers={"Authorization": f"Bearer {attacker_token}"},
        json={"question": "Show me patient results"}
    )
    assert unauth_res.status_code == 404

    # Attacker tries to get status
    unauth_status = client.get(
        f"/api/reports/{report_id}/rag/status",
        headers={"Authorization": f"Bearer {attacker_token}"}
    )
    assert unauth_status.status_code == 404
