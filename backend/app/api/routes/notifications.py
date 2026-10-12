from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    RemindersGenerationResponse
)
from app.services.notifications import (
    create_notification,
    list_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
    generate_health_reminders
)

router = APIRouter(prefix="/notifications", tags=["Notifications & Clinical Reminders"])

@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List patient notifications and alerts"
)
def get_user_notifications(
    unread_only: bool = Query(False, description="Filter only unread alerts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists notifications for authenticated user, sorted with newest first."""
    return list_notifications(current_user=current_user, unread_only=unread_only, db=db)

@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a notification"
)
def add_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a notification record for the authenticated user."""
    return create_notification(data=data, user_id=current_user.user_id, db=db)

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark single notification as read"
)
def read_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks a notification as read with BOLA validation."""
    return mark_notification_read(notification_id=notification_id, current_user=current_user, db=db)

@router.post(
    "/mark-all-read",
    status_code=status.HTTP_200_OK,
    summary="Mark all unread notifications as read"
)
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks all user notifications as read."""
    updated_count = mark_all_notifications_read(current_user=current_user, db=db)
    return {"message": f"Marked {updated_count} notifications as read", "updated_count": updated_count}

@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification"
)
def remove_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently deletes a notification with BOLA ownership validation."""
    delete_notification(notification_id=notification_id, current_user=current_user, db=db)
    return None

@router.post(
    "/generate-reminders",
    response_model=RemindersGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate and generate automated reminders"
)
def trigger_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Scans user's active prescriptions and upcoming appointments to trigger reminders."""
    return generate_health_reminders(current_user=current_user, db=db)
