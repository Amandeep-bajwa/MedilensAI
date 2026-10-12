import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.errors import AppException
from app.models.entities import User, Report, AIInteraction
from app.schemas.ai import (
    ReportSummaryRequest,
    ReportExplanationResponse,
    AskReportQuestionRequest,
    AskReportQuestionResponse,
    AIInteractionSummary,
    AbnormalFindingItem
)
from app.api.deps import get_current_user
from app.services.ai_explanation import (
    generate_report_explanation,
    answer_report_question
)

router = APIRouter(prefix="/reports", tags=["AI Report Explanation & Clinical Insights"])

@router.post(
    "/{report_id}/explain",
    response_model=ReportExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate patient-friendly AI report explanation and doctor consultation prompts"
)
@limiter.limit(settings.RATE_LIMIT_AI)
def explain_report(
    request: Request,
    report_id: str,
    payload: Optional[ReportSummaryRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyzes extracted clinical findings and synthesizes:
    - Jargon-free summary
    - Highlighted abnormal / out-of-range biomarkers
    - Suggested questions for the patient's doctor
    - Mandatory clinical safety disclaimers
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    focus = payload.focus_areas if payload else None
    return generate_report_explanation(db, report, current_user.user_id, focus_areas=focus)

@router.get(
    "/{report_id}/explanation",
    response_model=ReportExplanationResponse,
    summary="Retrieve AI clinical explanation for a report"
)
def get_report_explanation(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the most recent explanation for a report.
    If no explanation exists, automatically generates one on demand.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    existing = (
        db.query(AIInteraction)
        .filter(AIInteraction.report_id == report_id, AIInteraction.question.like("Generate Clinical Summary%"))
        .order_by(AIInteraction.created_at.desc())
        .first()
    )

    if existing:
        try:
            data = json.loads(existing.response)
            return ReportExplanationResponse(
                interaction_id=existing.interaction_id,
                report_id=report_id,
                summary=data.get("summary", ""),
                key_findings=data.get("key_findings", []),
                abnormal_findings=[AbnormalFindingItem(**a) for a in data.get("abnormal_findings", [])],
                lifestyle_recommendations=data.get("lifestyle_recommendations", []),
                doctor_questions=data.get("doctor_questions", []),
                disclaimer=data.get("disclaimer", ""),
                provider_used=data.get("provider_used", "clinical_rules_engine"),
                created_at=existing.created_at
            )
        except Exception:
            pass

    # If parsing failed or none exists, generate fresh
    return generate_report_explanation(db, report, current_user.user_id)

@router.post(
    "/{report_id}/ask",
    response_model=AskReportQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a follow-up question grounded in this report's findings"
)
@limiter.limit(settings.RATE_LIMIT_AI)
def ask_question_about_report(
    request: Request,
    report_id: str,
    payload: AskReportQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Answers a patient question grounded in their lab findings with clinical safety boundaries.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    return answer_report_question(db, report, current_user.user_id, payload.question)

@router.get(
    "/{report_id}/interactions",
    response_model=List[AIInteractionSummary],
    summary="List all AI consultation interactions for this report"
)
def list_report_interactions(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the audit history of AI conversations and explanations associated with this report.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report or (report.user_id != current_user.user_id and current_user.role != "admin"):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message=f"Medical report '{report_id}' was not found."
        )

    interactions = (
        db.query(AIInteraction)
        .filter(AIInteraction.report_id == report_id)
        .order_by(AIInteraction.created_at.desc())
        .all()
    )

    return [
        AIInteractionSummary(
            interaction_id=i.interaction_id,
            report_id=i.report_id,
            question=i.question,
            response=i.response,
            created_at=i.created_at
        )
        for i in interactions
    ]
