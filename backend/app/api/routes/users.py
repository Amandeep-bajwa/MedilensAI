from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.errors import AppException
from app.models.entities import User, Report, Medication, Appointment
from app.schemas.auth import UserSummary
from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserStatusUpdateRequest
)
from app.api.deps import get_current_user, require_admin
from app.services.audit import record_audit_log

router = APIRouter(prefix="/users", tags=["Users & Management"])

@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Get user profile with health entity counts"
)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the authenticated user's profile together with aggregated counts
    of their uploaded reports, active medications, and upcoming appointments.
    """
    report_count = db.query(func.count(Report.report_id)).filter(Report.user_id == current_user.user_id).scalar() or 0
    medication_count = db.query(func.count(Medication.medication_id)).filter(Medication.user_id == current_user.user_id).scalar() or 0
    appointment_count = db.query(func.count(Appointment.appointment_id)).filter(Appointment.user_id == current_user.user_id).scalar() or 0

    return UserProfileResponse(
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        total_reports=report_count,
        total_medications=medication_count,
        total_appointments=appointment_count
    )

@router.put(
    "/profile",
    response_model=UserSummary,
    summary="Update authenticated user profile"
)
def update_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates mutable user profile attributes (such as full name).
    """
    if payload.name:
        current_user.name = payload.name.strip()
        db.commit()
        db.refresh(current_user)

        record_audit_log(
            db=db,
            event_type="PROFILE_UPDATE",
            result="Success",
            user_id=current_user.user_id,
            metadata_info={"updated_name": current_user.name}
        )

    return UserSummary.model_validate(current_user)

@router.get(
    "/",
    response_model=List[UserSummary],
    summary="List users (Admin only)"
)
def list_users(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(20, ge=1, le=100, description="Page limit"),
    search: Optional[str] = Query(None, description="Filter by name or email"),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Lists system accounts with pagination and search. Restricted to system administrators.
    """
    query = db.query(User)
    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.filter(
            (func.lower(User.name).like(search_filter)) |
            (func.lower(User.email).like(search_filter))
        )
    
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [UserSummary.model_validate(u) for u in users]

@router.patch(
    "/{user_id}/status",
    response_model=UserSummary,
    summary="Update user status or role (Admin only)"
)
def update_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Allows administrators to activate, deactivate, or elevate roles of a target account.
    """
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message=f"User with id '{user_id}' does not exist."
        )

    # Prevent admin from deactivating their own account accidentally
    if target_user.user_id == admin.user_id and payload.is_active is False:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="SELF_DEACTIVATION_PROHIBITED",
            message="Administrators cannot deactivate their own account."
        )

    updates = {}
    if payload.is_active is not None:
        target_user.is_active = payload.is_active
        updates["is_active"] = payload.is_active
    
    if payload.role is not None:
        if payload.role not in ["user", "admin"]:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_ROLE",
                message="Role must be either 'user' or 'admin'."
            )
        target_user.role = payload.role
        updates["role"] = payload.role

    db.commit()
    db.refresh(target_user)

    record_audit_log(
        db=db,
        event_type="ADMIN_UPDATE_USER_STATUS",
        result="Success",
        user_id=admin.user_id,
        metadata_info={"target_user_id": user_id, "changes": updates}
    )

    return UserSummary.model_validate(target_user)
