import sys
import os
import io
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import SessionLocal
from app.models.entities import User, Report, AuditLog

client = TestClient(app)

# Dummy valid file byte sequences
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C"

import uuid

@pytest.fixture
def auth_user_a():
    email = f"usera_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "User Alpha",
        "email": email,
        "password": "Password123!",
        "role": "user"
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"token": token, "email": email, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def auth_user_b():
    email = f"userb_{uuid.uuid4().hex}@example.com"
    client.post("/api/auth/register", json={
        "name": "User Beta",
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
            db.query(Report).delete()
            db.query(AuditLog).delete()
            db.query(User).filter(User.email.like("%user%@example.com")).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    do_cleanup()
    yield
    do_cleanup()

def test_upload_pdf_success(auth_user_a):
    files = {
        "file": ("blood_test.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }
    data = {"category": "CBC"}
    res = client.post("/api/reports/upload", files=files, data=data, headers=auth_user_a["headers"])
    assert res.status_code == 201
    resp_data = res.json()
    assert resp_data["file_name"] == "blood_test.pdf"
    assert resp_data["file_type"] == "pdf"
    assert resp_data["category"] == "CBC"
    assert resp_data["processing_status"] == "Uploaded"
    assert resp_data["file_size_bytes"] == len(VALID_PDF_BYTES)

def test_upload_image_success(auth_user_a):
    files = {
        "file": ("skin_scan.png", io.BytesIO(VALID_PNG_BYTES), "image/png")
    }
    res = client.post("/api/reports/upload", files=files, data={"category": "Dermatology"}, headers=auth_user_a["headers"])
    assert res.status_code == 201
    resp_data = res.json()
    assert resp_data["file_name"] == "skin_scan.png"
    assert resp_data["file_type"] == "png"

def test_upload_unsupported_extension(auth_user_a):
    files = {
        "file": ("exploit.sh", io.BytesIO(b"echo 'malicious'"), "application/x-sh")
    }
    res = client.post("/api/reports/upload", files=files, headers=auth_user_a["headers"])
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

def test_upload_magic_spoofing_rejected(auth_user_a):
    # Extension says .pdf, but content is raw text
    files = {
        "file": ("fake_report.pdf", io.BytesIO(b"This is not a real PDF file!"), "application/pdf")
    }
    res = client.post("/api/reports/upload", files=files, headers=auth_user_a["headers"])
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "CORRUPTED_OR_SPOOFED_FILE"

def test_bola_tenant_isolation(auth_user_a, auth_user_b):
    # User A uploads a report
    files = {
        "file": ("confidential_report.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }
    upload_res = client.post("/api/reports/upload", files=files, headers=auth_user_a["headers"])
    assert upload_res.status_code == 201
    report_id = upload_res.json()["report_id"]

    # User B attempts to access User A's report directly
    get_res = client.get(f"/api/reports/{report_id}", headers=auth_user_b["headers"])
    assert get_res.status_code == 404

    # User B attempts to download User A's report
    download_res = client.get(f"/api/reports/{report_id}/download", headers=auth_user_b["headers"])
    assert download_res.status_code == 404

    # User B attempts to delete User A's report
    delete_res = client.get(f"/api/reports/{report_id}", headers=auth_user_b["headers"])
    assert delete_res.status_code == 404

    # User B listing reports does not contain User A's report
    list_b = client.get("/api/reports/", headers=auth_user_b["headers"])
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0

def test_download_and_delete_lifecycle(auth_user_a):
    files = {
        "file": ("lipid_panel.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")
    }
    upload_res = client.post("/api/reports/upload", files=files, data={"category": "Lipid Profile"}, headers=auth_user_a["headers"])
    report_id = upload_res.json()["report_id"]

    # Download document
    dl_res = client.get(f"/api/reports/{report_id}/download", headers=auth_user_a["headers"])
    assert dl_res.status_code == 200
    assert dl_res.content == VALID_PDF_BYTES
    assert dl_res.headers["content-type"] == "application/pdf"

    # Update category
    patch_res = client.patch(
        f"/api/reports/{report_id}",
        json={"category": "Lipid Profile (Fasting)"},
        headers=auth_user_a["headers"]
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["category"] == "Lipid Profile (Fasting)"

    # Delete document
    del_res = client.delete(f"/api/reports/{report_id}", headers=auth_user_a["headers"])
    assert del_res.status_code == 200

    # Ensure document is gone from API
    gone_res = client.get(f"/api/reports/{report_id}", headers=auth_user_a["headers"])
    assert gone_res.status_code == 404
