import uuid
import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.errors import AppException
from app.models.entities import User, Report
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportUpdate
)
from app.api.deps import get_current_user
from app.services.storage import (
    validate_file_security,
    save_upload_file,
    delete_upload_file,
    get_file_size
)
from app.services.audit import record_audit_log

router = APIRouter(prefix="/reports", tags=["Reports Management"])

def serialize_report(report: Report) -> ReportResponse:
    size = get_file_size(report.file_path)
    return ReportResponse(
        report_id=report.report_id,
        user_id=report.user_id,
        file_name=report.file_name,
        file_type=report.file_type,
        category=report.category,
        processing_status=report.processing_status,
        file_size_bytes=size,
        uploaded_at=report.uploaded_at,
        updated_at=report.updated_at
    )

@router.post(
    "/upload",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a medical report"
)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_report(
    request: Request,
    file: UploadFile = File(..., description="Medical lab report document (PDF, PNG, JPG, JPEG)"),
    category: str = Form("Other", description="Clinical test category (e.g., CBC, Lipid Profile)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingests a clinical report document:
    1. Validates MIME type, maximum size, and magic byte signatures.
    2. Stores the immutable source file in a partitioned directory per user tenant.
    3. Creates the Report metadata record in status 'Uploaded'.
    4. Records an auditable security entry in the audit trail.
    """
    file_bytes = await file.read()
    file_type = validate_file_security(file_bytes, file.filename or "report")

    report_id = str(uuid.uuid4())
    safe_name, file_path = save_upload_file(
        user_id=current_user.user_id,
        report_id=report_id,
        original_filename=file.filename or f"report.{file_type}",
        file_bytes=file_bytes
    )

    new_report = Report(
        report_id=report_id,
        user_id=current_user.user_id,
        file_name=safe_name,
        file_type=file_type,
        file_path=file_path,
        category=category.strip() or "Other",
        processing_status="Uploaded"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    record_audit_log(
        db=db,
        event_type="REPORT_UPLOAD",
        result="Success",
        user_id=current_user.user_id,
        metadata_info={
            "report_id": report_id,
            "file_name": safe_name,
            "category": new_report.category,
            "file_size": len(file_bytes)
        }
    )

    return serialize_report(new_report)

@router.get(
    "/",
    response_model=ReportListResponse,
    summary="List medical reports with tenant isolation"
)
def list_reports(
    skip: int = Query(0, ge=0, description="Offset pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    category: Optional[str] = Query(None, description="Filter by clinical category"),
    processing_status: Optional[str] = Query(None, description="Filter by status (Uploaded, Processing, Completed, Failed)"),
    search: Optional[str] = Query(None, description="Search by file name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists medical reports for the current tenant.
    Enforces strict user data boundary: users can only view their own uploaded documents.
    """
    query = db.query(Report)

    if current_user.role != "admin":
        query = query.filter(Report.user_id == current_user.user_id)

    if category:
        query = query.filter(Report.category == category)

    if processing_status:
        query = query.filter(Report.processing_status == processing_status)

    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.filter(func.lower(Report.file_name).like(search_filter))

    total = query.count()
    reports = query.order_by(Report.uploaded_at.desc()).offset(skip).limit(limit).all()

    return ReportListResponse(
        items=[serialize_report(r) for r in reports],
        total=total,
        page=(skip // limit) + 1,
        limit=limit
    )

@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get single report details"
)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a report by its UUID with strict BOLA isolation checks.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    return serialize_report(report)

@router.get(
    "/{report_id}/download",
    summary="Stream and download original document"
)
def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Securely serves the unmodified original medical document.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    if not os.path.isfile(report.file_path):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_NOT_FOUND_ON_DISK",
            message="Document binary is missing from secure storage."
        )

    media_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg"
    }
    media_type = media_map.get(report.file_type.lower(), "application/octet-stream")

    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type=media_type
    )

@router.patch(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Update report category"
)
def update_report(
    report_id: str,
    payload: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the clinical category classification of an uploaded report.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    if payload.category:
        report.category = payload.category.strip()
        db.commit()
        db.refresh(report)

        record_audit_log(
            db=db,
            event_type="REPORT_UPDATE",
            result="Success",
            user_id=current_user.user_id,
            metadata_info={"report_id": report_id, "updated_category": report.category}
        )

    return serialize_report(report)

@router.delete(
    "/{report_id}",
    summary="Delete medical report and purge from storage"
)
def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes the medical report, safely removing the disk file and cascading
    the removal of any related OCR and AI interaction records.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    file_path = report.file_path
    file_name = report.file_name

    db.delete(report)
    db.commit()

    # Safely purge physical file from storage
    delete_upload_file(file_path)

    record_audit_log(
        db=db,
        event_type="REPORT_DELETE",
        result="Success",
        user_id=current_user.user_id,
        metadata_info={"report_id": report_id, "file_name": file_name}
    )

    return {
        "message": "Medical report deleted successfully.",
        "report_id": report_id
    }
