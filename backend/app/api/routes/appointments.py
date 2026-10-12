from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.health import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse
)
from app.services.health import (
    create_appointment,
    list_appointments,
    get_appointment_by_id,
    update_appointment,
    delete_appointment
)

router = APIRouter(prefix="/appointments", tags=["Appointments Management"])

@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a doctor consultation appointment"
)
def schedule_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedules a new doctor appointment for the patient."""
    return create_appointment(data=data, current_user=current_user, db=db)

@router.get(
    "",
    response_model=AppointmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List patient appointments"
)
def get_appointments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: Upcoming, Completed, Cancelled"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists patient consultations chronologically, optionally filtered by status."""
    return list_appointments(current_user=current_user, status_filter=status_filter, db=db)

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get appointment details by ID"
)
def get_single_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves single appointment details with BOLA validation."""
    return get_appointment_by_id(appointment_id=appointment_id, current_user=current_user, db=db)

@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update or reschedule appointment"
)
def edit_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reschedules or updates consultation details with BOLA protection."""
    return update_appointment(appointment_id=appointment_id, data=data, current_user=current_user, db=db)

@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel or delete an appointment"
)
def remove_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancels/deletes appointment entry with BOLA validation."""
    delete_appointment(appointment_id=appointment_id, current_user=current_user, db=db)
    return None
