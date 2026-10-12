from typing import Optional, List
from datetime import date
from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.models.entities import Medication, Appointment, User
from app.schemas.health import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationListResponse,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse
)
from app.services.audit import record_audit_log

def is_medication_active(start_dt: date, end_dt: Optional[date]) -> bool:
    """Computes whether a medication regimen is currently active based on today's date."""
    today = date.today()
    if end_dt is None:
        return True
    return end_dt >= today

def serialize_medication(med: Medication) -> MedicationResponse:
    """Serializes a Medication ORM entity into a Pydantic response with dynamic active flag."""
    active = is_medication_active(med.start_date, med.end_date)
    return MedicationResponse(
        medication_id=med.medication_id,
        user_id=med.user_id,
        medicine_name=med.medicine_name,
        dosage=med.dosage,
        frequency=med.frequency,
        start_date=med.start_date,
        end_date=med.end_date,
        notes=med.notes,
        is_active=active,
        created_at=med.created_at
    )

# ----------------- MEDICATION SERVICES -----------------

def create_medication(
    data: MedicationCreate,
    current_user: User,
    db: Session
) -> MedicationResponse:
    """Registers a new prescribed medication for the authenticated user."""
    med = Medication(
        user_id=current_user.user_id,
        medicine_name=data.medicine_name.strip(),
        dosage=data.dosage.strip(),
        frequency=data.frequency.strip(),
        start_date=data.start_date,
        end_date=data.end_date,
        notes=data.notes.strip() if data.notes else None
    )
    db.add(med)
    db.commit()
    db.refresh(med)

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="MEDICATION_CREATED",
        result="Success",
        metadata_info={"medication_id": med.medication_id, "medicine_name": med.medicine_name}
    )

    return serialize_medication(med)

def list_medications(
    current_user: User,
    active_only: bool,
    db: Session
) -> MedicationListResponse:
    """Lists patient medications, optionally filtering to only active prescriptions."""
    query = db.query(Medication).filter(Medication.user_id == current_user.user_id)
    records = query.order_by(Medication.start_date.desc(), Medication.created_at.desc()).all()

    items = [serialize_medication(m) for m in records]
    if active_only:
        items = [item for item in items if item.is_active]

    return MedicationListResponse(
        total=len(items),
        items=items
    )

def get_medication_by_id(
    medication_id: str,
    current_user: User,
    db: Session
) -> MedicationResponse:
    """Retrieves a single medication record with strict BOLA isolation."""
    med = db.query(Medication).filter(
        Medication.medication_id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()

    if not med:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEDICATION_NOT_FOUND",
            message="Medication record not found."
        )

    return serialize_medication(med)

def update_medication(
    medication_id: str,
    data: MedicationUpdate,
    current_user: User,
    db: Session
) -> MedicationResponse:
    """Updates a medication regimen with BOLA validation."""
    med = db.query(Medication).filter(
        Medication.medication_id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()

    if not med:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEDICATION_NOT_FOUND",
            message="Medication record not found."
        )

    if data.medicine_name is not None:
        med.medicine_name = data.medicine_name.strip()
    if data.dosage is not None:
        med.dosage = data.dosage.strip()
    if data.frequency is not None:
        med.frequency = data.frequency.strip()
    if data.start_date is not None:
        med.start_date = data.start_date
    if data.end_date is not None:
        med.end_date = data.end_date
    if data.notes is not None:
        med.notes = data.notes.strip() if data.notes else None

    db.commit()
    db.refresh(med)

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="MEDICATION_UPDATED",
        result="Success",
        metadata_info={"medication_id": med.medication_id}
    )

    return serialize_medication(med)

def delete_medication(
    medication_id: str,
    current_user: User,
    db: Session
) -> None:
    """Permanently deletes a medication record with BOLA ownership validation."""
    med = db.query(Medication).filter(
        Medication.medication_id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()

    if not med:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEDICATION_NOT_FOUND",
            message="Medication record not found."
        )

    db.delete(med)
    db.commit()

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="MEDICATION_DELETED",
        result="Success",
        metadata_info={"medication_id": medication_id}
    )


# ----------------- APPOINTMENT SERVICES -----------------

def create_appointment(
    data: AppointmentCreate,
    current_user: User,
    db: Session
) -> AppointmentResponse:
    """Schedules a new physician appointment for the patient."""
    app = Appointment(
        user_id=current_user.user_id,
        doctor_name=data.doctor_name.strip(),
        specialization=data.specialization.strip(),
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time.strip(),
        location=data.location.strip() if data.location else None,
        notes=data.notes.strip() if data.notes else None,
        status=data.status
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="APPOINTMENT_SCHEDULED",
        result="Success",
        metadata_info={
            "appointment_id": app.appointment_id,
            "doctor": app.doctor_name,
            "specialty": app.specialization
        }
    )

    return AppointmentResponse.model_validate(app)

def list_appointments(
    current_user: User,
    status_filter: Optional[str],
    db: Session
) -> AppointmentListResponse:
    """Lists scheduled consultations, sorted chronologically."""
    query = db.query(Appointment).filter(Appointment.user_id == current_user.user_id)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    records = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()
    items = [AppointmentResponse.model_validate(a) for a in records]

    return AppointmentListResponse(
        total=len(items),
        items=items
    )

def get_appointment_by_id(
    appointment_id: str,
    current_user: User,
    db: Session
) -> AppointmentResponse:
    """Retrieves single consultation details with BOLA protection."""
    app = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id,
        Appointment.user_id == current_user.user_id
    ).first()

    if not app:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="APPOINTMENT_NOT_FOUND",
            message="Appointment record not found."
        )

    return AppointmentResponse.model_validate(app)

def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    current_user: User,
    db: Session
) -> AppointmentResponse:
    """Updates appointment date, time, notes, or status with BOLA validation."""
    app = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id,
        Appointment.user_id == current_user.user_id
    ).first()

    if not app:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="APPOINTMENT_NOT_FOUND",
            message="Appointment record not found."
        )

    if data.doctor_name is not None:
        app.doctor_name = data.doctor_name.strip()
    if data.specialization is not None:
        app.specialization = data.specialization.strip()
    if data.appointment_date is not None:
        app.appointment_date = data.appointment_date
    if data.appointment_time is not None:
        app.appointment_time = data.appointment_time.strip()
    if data.location is not None:
        app.location = data.location.strip() if data.location else None
    if data.notes is not None:
        app.notes = data.notes.strip() if data.notes else None
    if data.status is not None:
        app.status = data.status

    db.commit()
    db.refresh(app)

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="APPOINTMENT_UPDATED",
        result="Success",
        metadata_info={"appointment_id": app.appointment_id, "status": app.status}
    )

    return AppointmentResponse.model_validate(app)

def delete_appointment(
    appointment_id: str,
    current_user: User,
    db: Session
) -> None:
    """Cancels/deletes appointment record with BOLA ownership validation."""
    app = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id,
        Appointment.user_id == current_user.user_id
    ).first()

    if not app:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="APPOINTMENT_NOT_FOUND",
            message="Appointment record not found."
        )

    db.delete(app)
    db.commit()

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="APPOINTMENT_DELETED",
        result="Success",
        metadata_info={"appointment_id": appointment_id}
    )
