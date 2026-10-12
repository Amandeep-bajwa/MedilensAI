import sys
import os
import io
import time
import uuid
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import SessionLocal
from app.models.entities import User, Report

client = TestClient(app)

BENCHMARK_PDF = b"""%PDF-1.4
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
(METROPOLITAN CLINICAL LABORATORIES) Tj
0 -20 Td
(Patient Name: Benchmark Patient | Age: 42) Tj
0 -20 Td
(Hemoglobin: 13.8 g/dL [12.0 - 16.0]) Tj
0 -20 Td
(Fasting Blood Sugar: 95 mg/dL [70 - 100]) Tj
0 -20 Td
(Total Cholesterol: 180 mg/dL [125 - 200]) Tj
0 -20 Td
(Serum Creatinine: 0.8 mg/dL [0.6 - 1.2]) Tj
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

@pytest.fixture
def benchmark_patient():
    email = f"bench_{uuid.uuid4().hex}@example.com"
    pwd = "BenchmarkPassword123!"
    reg_res = client.post("/api/auth/register", json={
        "name": "Benchmark Patient",
        "email": email,
        "password": pwd
    })
    token = reg_res.json()["access_token"]
    return {
        "email": email,
        "password": pwd,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }

# ----------------- PERFORMANCE BENCHMARKS (SRS SECTION 17) -----------------

def test_benchmark_standard_api_latency():
    """
    SRS Section 17: Standard API request latency benchmark (Target: ≤ 2.0s)
    Evaluates health probe and lightweight API responses.
    """
    start_time = time.perf_counter()
    res = client.get("/api/health")
    duration = time.perf_counter() - start_time

    assert res.status_code == 200
    assert duration <= 2.0, f"Standard API latency {duration:.4f}s exceeded target of 2.0s"
    print(f"\n[BENCHMARK] Standard API request latency: {duration * 1000:.2f} ms (Target: <= 2000 ms)")


def test_benchmark_auth_login_latency():
    """
    SRS Section 17: Authentication request latency benchmark (Target: ≤ 2.0s)
    Evaluates bcrypt password verification and JWT cryptographic signing.
    """
    email = f"auth_bench_{uuid.uuid4().hex}@example.com"
    pwd = "SecureBenchPassword123!"

    client.post("/api/auth/register", json={"name": "Auth Bench", "email": email, "password": pwd})

    start_time = time.perf_counter()
    login_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
    duration = time.perf_counter() - start_time

    assert login_res.status_code == 200
    assert duration <= 2.0, f"Auth request latency {duration:.4f}s exceeded target of 2.0s"
    print(f"\n[BENCHMARK] Authentication login latency: {duration * 1000:.2f} ms (Target: <= 2000 ms)")


def test_benchmark_database_query_latency():
    """
    SRS Section 17: Database query latency benchmark (Target: ≤ 1.0s)
    Direct ORM query execution latency on SessionLocal.
    """
    db = SessionLocal()
    try:
        start_time = time.perf_counter()
        users = db.query(User).limit(50).all()
        duration = time.perf_counter() - start_time

        assert duration <= 1.0, f"Database query latency {duration:.4f}s exceeded target of 1.0s"
        print(f"\n[BENCHMARK] Database ORM query latency: {duration * 1000:.2f} ms (Target: <= 1000 ms)")
    finally:
        db.close()


def test_benchmark_ocr_processing_latency(benchmark_patient):
    """
    SRS Section 17: Normal OCR processing latency benchmark (Target: ≤ 30.0s)
    Evaluates file upload, PDF byte extraction, parameter parsing, and chunking.
    """
    headers = benchmark_patient["headers"]

    # Upload report
    up_res = client.post(
        "/api/reports/upload",
        headers=headers,
        files={"file": ("bench_report.pdf", io.BytesIO(BENCHMARK_PDF), "application/pdf")}
    )
    assert up_res.status_code == 201
    report_id = up_res.json()["report_id"]

    # Trigger OCR and measure latency
    start_time = time.perf_counter()
    ocr_res = client.post(f"/api/reports/{report_id}/ocr/process", headers=headers)
    duration = time.perf_counter() - start_time

    assert ocr_res.status_code == 200
    assert duration <= 30.0, f"OCR processing latency {duration:.4f}s exceeded target of 30.0s"
    print(f"\n[BENCHMARK] OCR processing pipeline latency: {duration:.3f} s (Target: <= 30.0 s)")

    # Cleanup report
    client.delete(f"/api/reports/{report_id}", headers=headers)


def test_benchmark_dashboard_loading_latency(benchmark_patient):
    """
    SRS Section 17: Dashboard loading latency benchmark (Target: ≤ 3.0s)
    Evaluates multi-table aggregated summary query across reports, medications, appointments, and AI logs.
    """
    headers = benchmark_patient["headers"]

    start_time = time.perf_counter()
    dash_res = client.get("/api/dashboard/summary", headers=headers)
    duration = time.perf_counter() - start_time

    assert dash_res.status_code == 200
    assert duration <= 3.0, f"Dashboard loading latency {duration:.4f}s exceeded target of 3.0s"
    print(f"\n[BENCHMARK] Dashboard summary aggregation latency: {duration * 1000:.2f} ms (Target: <= 3000 ms)")


def test_benchmark_concurrent_api_requests():
    """
    SRS Section 20.6: Concurrent request handling and connection pool stability.
    Dispatches 10 concurrent requests to verify server throughput without connection exhaustion.
    """
    def make_request():
        start = time.perf_counter()
        res = client.get("/api/health")
        return res.status_code, time.perf_counter() - start

    concurrency = 10
    start_all = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(lambda _: make_request(), range(concurrency)))
    total_time = time.perf_counter() - start_all

    for code, dur in results:
        assert code == 200
        assert dur <= 2.0

    avg_latency = (sum(dur for _, dur in results) / concurrency) * 1000
    print(f"\n[BENCHMARK] Concurrent requests ({concurrency} workers): Total {total_time:.3f}s | Avg per request: {avg_latency:.2f} ms")
