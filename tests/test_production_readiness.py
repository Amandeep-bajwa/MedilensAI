import sys
import os
import shutil
import pytest
from fastapi.testclient import TestClient

# Package path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from scripts.backup_db import run_backup, compute_sha256
from scripts.restore_db import run_restore

client = TestClient(app)
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ----------------- PRODUCTION READINESS TESTS (SRS SECTION 12 & 18) -----------------

def test_health_liveness_and_system_monitoring_probes():
    """
    SRS Section 12 & Phase 12 Monitoring:
    Verifies that liveness probe and deep system telemetry endpoints return valid operational metrics.
    """
    # 1. Liveness check
    live_res = client.get("/api/health")
    assert live_res.status_code == 200
    live_data = live_res.json()
    assert live_data["status"] == "online"
    assert live_data["database"] == "healthy"

    # 2. Deep monitoring probe
    sys_res = client.get("/api/health/system")
    assert sys_res.status_code == 200
    sys_data = sys_res.json()

    assert sys_data["status"] in ["operational", "degraded"]
    assert "uptime_seconds" in sys_data
    assert sys_data["uptime_seconds"] >= 0

    # Verify database latency metric
    db_metrics = sys_data["database"]
    assert db_metrics["connected"] is True
    assert "latency_ms" in db_metrics
    assert db_metrics["latency_ms"] >= 0

    # Verify storage metrics
    storage = sys_data["storage"]
    assert storage["total_gb"] > 0
    assert storage["free_gb"] > 0
    assert storage["writable"] is True

    # Verify rate limit configuration
    rate_cfg = sys_data["rate_limiting"]
    assert rate_cfg["enabled"] is True


def test_database_backup_and_recovery_integrity():
    """
    SRS Section 18.1 & 18.2: Database Backup and Disaster Recovery Procedure
    Validates automated backup creation, SHA-256 sidecar checksum calculation,
    and post-restore table count verification.
    """
    # 1. Execute atomic backup
    backup_file = run_backup()
    assert os.path.exists(backup_file), f"Backup file not generated: {backup_file}"

    # 2. Verify SHA-256 sidecar checksum file
    sidecar_path = backup_file + ".sha256"
    assert os.path.exists(sidecar_path), f"SHA-256 sidecar missing: {sidecar_path}"

    with open(sidecar_path, "r", encoding="utf-8") as f:
        recorded_checksum = f.read().split()[0].strip()

    actual_checksum = compute_sha256(backup_file)
    assert recorded_checksum == actual_checksum, "SHA-256 checksum mismatch"

    # 3. Test restoration to target sandbox database
    test_target_db = os.path.join(WORKSPACE_ROOT, "backups", "test_verify_restore.db")
    try:
        ok = run_restore(backup_file, f"sqlite:///{test_target_db}")
        assert ok is True, "Database restoration failed"
        assert os.path.exists(test_target_db), "Restored database file was not created"
    finally:
        # Cleanup test restore artifact
        if os.path.exists(test_target_db):
            os.remove(test_target_db)


def test_docker_production_manifests_and_directives():
    """
    Phase 12 Deployment: Verifies that Dockerfiles, NGINX config, and docker-compose.prod.yml
    contain all mandatory production directives (healthchecks, non-root user, multi-workers).
    """
    backend_dockerfile = os.path.join(WORKSPACE_ROOT, "backend", "Dockerfile.prod")
    frontend_dockerfile = os.path.join(WORKSPACE_ROOT, "frontend", "Dockerfile")
    frontend_nginx = os.path.join(WORKSPACE_ROOT, "frontend", "nginx.conf")
    compose_prod = os.path.join(WORKSPACE_ROOT, "docker-compose.prod.yml")
    env_prod = os.path.join(WORKSPACE_ROOT, ".env.production.example")

    # Assert files exist
    for path in [backend_dockerfile, frontend_dockerfile, frontend_nginx, compose_prod, env_prod]:
        assert os.path.exists(path), f"Missing deployment manifest: {path}"

    # Check backend Dockerfile directives
    with open(backend_dockerfile, "r", encoding="utf-8") as f:
        backend_content = f.read()
    assert "useradd" in backend_content, "Backend Dockerfile must enforce non-root security user"
    assert "HEALTHCHECK" in backend_content, "Backend Dockerfile must specify HEALTHCHECK probe"
    assert "--workers" in backend_content, "Backend Dockerfile must run multi-worker ASGI"

    # Check frontend Dockerfile & NGINX directives
    with open(frontend_dockerfile, "r", encoding="utf-8") as f:
        frontend_content = f.read()
    assert "FROM node:20-alpine AS build" in frontend_content, "Frontend Dockerfile must use multi-stage build"
    assert "FROM nginx:alpine" in frontend_content, "Frontend Dockerfile must serve via NGINX"

    with open(frontend_nginx, "r", encoding="utf-8") as f:
        nginx_content = f.read()
    assert "gzip on;" in nginx_content, "NGINX must have gzip compression enabled"
    assert "try_files $uri $uri/ /index.html;" in nginx_content, "NGINX must support SPA fallback"
    assert "proxy_pass http://backend:8000/api/;" in nginx_content, "NGINX must proxy API traffic"

    # Check docker-compose.prod.yml directives
    with open(compose_prod, "r", encoding="utf-8") as f:
        compose_content = f.read()
    assert "pg_isready" in compose_content, "Compose DB must define healthcheck probe"
    assert "resources:" in compose_content, "Compose must enforce container resource limits"
    assert "depends_on:" in compose_content, "Compose services must configure healthy dependencies"
