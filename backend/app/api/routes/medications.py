from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.health import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationListResponse
)
from app.services.health import (
    create_medication,
    list_medications,
    get_medication_by_id,
    update_medication,
    delete_medication
)

router = APIRouter(prefix="/medications", tags=["Medications Management"])

@router.post(
    "",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new prescribed medication"
)
def add_medication(
    data: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registers a new medication regimen for the patient."""
    return create_medication(data=data, current_user=current_user, db=db)

@router.get(
    "",
    response_model=MedicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List patient medications"
)
def get_medications(
    active_only: bool = Query(False, description="Filter only currently active medications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists patient medications, optionally filtering to only active courses."""
    return list_medications(current_user=current_user, active_only=active_only, db=db)

@router.get(
    "/{medication_id}",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get medication details by ID"
)
def get_single_medication(
    medication_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves single medication with BOLA protection."""
    return get_medication_by_id(medication_id=medication_id, current_user=current_user, db=db)

@router.put(
    "/{medication_id}",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update medication dosage or schedule"
)
def edit_medication(
    medication_id: str,
    data: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates a medication regimen with BOLA validation."""
    return update_medication(medication_id=medication_id, data=data, current_user=current_user, db=db)

@router.delete(
    "/{medication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a medication record"
)
def remove_medication(
    medication_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a medication entry with BOLA validation."""
    delete_medication(medication_id=medication_id, current_user=current_user, db=db)
    return None
