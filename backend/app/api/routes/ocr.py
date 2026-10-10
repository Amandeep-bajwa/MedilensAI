from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppException
from app.models.entities import User, Report, OCR, ReportChunk
from app.schemas.ocr import (
    OCRResponse,
    ReportChunkResponse,
    ChunksListResponse
)
from app.api.deps import get_current_user
from app.services.ocr import (
    process_report_ocr,
    parse_clinical_lab_parameters
)

router = APIRouter(prefix="/reports", tags=["OCR & Document Processing"])

def build_ocr_response(ocr_record: OCR, db: Session) -> OCRResponse:
    chunks_count = db.query(ReportChunk).filter(ReportChunk.report_id == ocr_record.report_id).count()
    params = parse_clinical_lab_parameters(ocr_record.extracted_text or "")
    return OCRResponse(
        ocr_id=ocr_record.ocr_id,
        report_id=ocr_record.report_id,
        extracted_text=ocr_record.extracted_text or "",
        confidence=ocr_record.confidence or 0.0,
        status=ocr_record.status,
        parameters=params,
        total_chunks=chunks_count,
        created_at=ocr_record.created_at
    )

@router.post(
    "/{report_id}/ocr/process",
    response_model=OCRResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger OCR text extraction and clinical parameter parsing"
)
def trigger_ocr(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes the OCR processing pipeline on an uploaded clinical report.
    Extracts text, parses structured lab values, and chunks content for RAG.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    ocr_record, _, _ = process_report_ocr(db, report, current_user.user_id)
    return build_ocr_response(ocr_record, db)

@router.get(
    "/{report_id}/ocr",
    response_model=OCRResponse,
    summary="Retrieve OCR results and extracted laboratory parameters"
)
def get_ocr_data(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the extracted OCR text and structured clinical parameters.
    If OCR has not yet been triggered, automatically processes the document on demand.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    ocr_record = db.query(OCR).filter(OCR.report_id == report_id).first()
    if not ocr_record:
        # Run on-demand processing
        ocr_record, _, _ = process_report_ocr(db, report, current_user.user_id)

    return build_ocr_response(ocr_record, db)

@router.get(
    "/{report_id}/chunks",
    response_model=ChunksListResponse,
    summary="Retrieve semantic document chunks (RAG Ready)"
)
def get_report_chunks(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all semantic chunks with page number references for a report.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    chunks = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).order_by(ReportChunk.page_number).all()

    return ChunksListResponse(
        report_id=report_id,
        total_chunks=len(chunks),
        chunks=[ReportChunkResponse.model_validate(c) for c in chunks]
    )
