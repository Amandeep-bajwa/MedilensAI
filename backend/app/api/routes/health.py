import os
import shutil
import time
import platform
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

START_TIME = time.time()

@router.get("/health", summary="Basic System Health & Liveness Probe")
def health_check(db: Session = Depends(get_db)):
    """
    Lightweight health check for container liveness and load balancer health monitors.
    Returns HTTP 200 when database connectivity is verified.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "service": "MediLens AI Backend API",
        "database": db_status,
        "version": "1.0.0"
    }

@router.get("/health/system", summary="Deep System Monitoring & Readiness Probe")
def system_monitoring_probe(db: Session = Depends(get_db)):
    """
    Deep readiness and system telemetry probe (SRS Section 12 & 18).
    Evaluates:
    - Database round-trip ping latency
    - Upload disk storage capacity and free space
    - Process uptime and platform specifications
    - Security and environment flags
    """
    # 1. Database latency
    db_ok = True
    db_error = None
    db_start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - db_start) * 1000, 2)
    except Exception as e:
        db_ok = False
        db_error = str(e)
        db_latency_ms = -1.0

    # 2. Disk storage metrics
    upload_path = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_path, exist_ok=True)
    total_bytes, used_bytes, free_bytes = shutil.disk_usage(upload_path)
    total_gb = round(total_bytes / (1024 ** 3), 2)
    free_gb = round(free_bytes / (1024 ** 3), 2)
    used_percent = round((used_bytes / total_bytes) * 100, 1)

    # 3. Uptime
    uptime_seconds = int(time.time() - START_TIME)

    return {
        "status": "operational" if db_ok else "degraded",
        "timestamp": time.time(),
        "uptime_seconds": uptime_seconds,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "database": {
            "connected": db_ok,
            "latency_ms": db_latency_ms,
            "error": db_error
        },
        "storage": {
            "upload_dir": upload_path,
            "total_gb": total_gb,
            "free_gb": free_gb,
            "used_percent": used_percent,
            "writable": os.access(upload_path, os.W_OK)
        },
        "runtime": {
            "python_version": platform.python_version(),
            "os": platform.system(),
            "architecture": platform.machine()
        },
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "login_limit": settings.RATE_LIMIT_LOGIN,
            "ai_limit": settings.RATE_LIMIT_AI,
            "upload_limit": settings.RATE_LIMIT_UPLOAD
        }
    }
