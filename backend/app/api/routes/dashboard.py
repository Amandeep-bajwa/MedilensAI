from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Clinical Analytics"])

@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated patient dashboard metrics"
)
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves aggregated dashboard statistics strictly for the authenticated patient:
    - Total reports and report processing statuses
    - Active medication regimens
    - Upcoming clinical consultations
    - Recent AI interactions (summaries, RAG questions, triage logs)
    - Unread alert notification count
    """
    return get_dashboard_summary(current_user=current_user, db=db)
