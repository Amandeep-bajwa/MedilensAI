from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.symptom import (
    SymptomAnalyzeRequest,
    SymptomAnalysisResponse,
    SymptomHistoryItem,
    CommonSymptomCategory
)
from app.services.symptoms import (
    analyze_symptoms_engine,
    get_user_symptom_history,
    COMMON_SYMPTOM_CATEGORIES
)

router = APIRouter(prefix="/symptoms", tags=["Symptom Assistant & Clinical Triage"])

@router.post(
    "/analyze",
    response_model=SymptomAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze patient symptoms for triage, red-flags, and specialist referral"
)
def analyze_symptoms(
    request: SymptomAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates patient-described symptoms against clinical red-flag protocols and triage rules.
    Identifies emergency indicators, determines triage urgency (EMERGENCY, URGENT, ROUTINE),
    recommends clinical specialty, constructs supportive tips and consultation questions,
    and attaches non-diagnostic regulatory disclaimers.
    """
    return analyze_symptoms_engine(
        request=request,
        current_user=current_user,
        db=db
    )

@router.get(
    "/history",
    response_model=List[SymptomHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Retrieve user's symptom analysis and triage history"
)
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves previous symptom evaluations for the authenticated user."""
    return get_user_symptom_history(
        current_user=current_user,
        db=db
    )

@router.get(
    "/common",
    response_model=List[CommonSymptomCategory],
    status_code=status.HTTP_200_OK,
    summary="Retrieve categorized common symptoms for UI tag selection"
)
def get_common_symptoms():
    """Returns categorized clinical symptoms for quick patient selection."""
    return COMMON_SYMPTOM_CATEGORIES
