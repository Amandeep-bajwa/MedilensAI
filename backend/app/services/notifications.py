from typing import Optional, List
from datetime import date, timedelta
from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.models.entities import User, Notification, Appointment, Medication
from app.schemas.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    RemindersGenerationResponse
)
from app.services.health import is_medication_active
from app.services.audit import record_audit_log

def create_notification(
    data: NotificationCreate,
    user_id: str,
    db: Session
) -> NotificationResponse:
    """Creates a notification record for a specific user."""
    notif = Notification(
        user_id=user_id,
        title=data.title.strip(),
        message=data.message.strip(),
        type=data.type,
        link=data.link.strip() if data.link else None,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    return NotificationResponse.model_validate(notif)

def list_notifications(
    current_user: User,
    unread_only: bool,
    db: Session
) -> NotificationListResponse:
    """Lists notifications for the authenticated user, ordered with newest first."""
    query = db.query(Notification).filter(Notification.user_id == current_user.user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    records = query.order_by(Notification.created_at.desc()).all()
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.user_id, Notification.is_read.is_(False))
        .count()
    )

    items = [NotificationResponse.model_validate(n) for n in records]
    return NotificationListResponse(
        total=len(items),
        unread_count=unread_count,
        items=items
    )

def mark_notification_read(
    notification_id: str,
    current_user: User,
    db: Session
) -> NotificationResponse:
    """Marks a single notification as read with strict BOLA isolation."""
    notif = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id
    ).first()

    if not notif:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOTIFICATION_NOT_FOUND",
            message="Notification not found."
        )

    notif.is_read = True
    db.commit()
    db.refresh(notif)

    return NotificationResponse.model_validate(notif)

def mark_all_notifications_read(
    current_user: User,
    db: Session
) -> int:
    """Marks all unread notifications for the user as read."""
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.user_id, Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return updated

def delete_notification(
    notification_id: str,
    current_user: User,
    db: Session
) -> None:
    """Permanently deletes a notification with BOLA ownership validation."""
    notif = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id
    ).first()

    if not notif:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOTIFICATION_NOT_FOUND",
            message="Notification not found."
        )

    db.delete(notif)
    db.commit()

def generate_health_reminders(
    current_user: User,
    db: Session
) -> RemindersGenerationResponse:
    """Automatically generates notifications for upcoming appointments and active medication courses."""
    user_id = current_user.user_id
    today = date.today()
    three_days_hence = today + timedelta(days=3)
    generated: List[str] = []

    # 1. Appointment Reminders (within next 3 days)
    upcoming_appts = (
        db.query(Appointment)
        .filter(
            Appointment.user_id == user_id,
            Appointment.status == "Upcoming",
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= three_days_hence
        )
        .all()
    )

    for appt in upcoming_appts:
        link_target = f"/appointments/{appt.appointment_id}"
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.type == "APPOINTMENT_REMINDER",
                Notification.link == link_target
            )
            .first()
        )
        if not existing:
            notif = Notification(
                user_id=user_id,
                title=f"Upcoming Appointment: {appt.doctor_name}",
                message=f"Reminder: You have a consultation with {appt.doctor_name} ({appt.specialization}) on {appt.appointment_date} at {appt.appointment_time}.",
                type="APPOINTMENT_REMINDER",
                link=link_target,
                is_read=False
            )
            db.add(notif)
            generated.append(f"Appointment reminder for {appt.doctor_name}")

    # 2. Medication Reminders (active medicines)
    active_meds = db.query(Medication).filter(Medication.user_id == user_id).all()
    for med in active_meds:
        if is_medication_active(med.start_date, med.end_date):
            link_target = f"/medications/{med.medication_id}"
            existing = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.type == "MEDICATION_REMINDER",
                    Notification.link == link_target
                )
                .first()
            )
            if not existing:
                notif = Notification(
                    user_id=user_id,
                    title=f"Active Prescription: {med.medicine_name}",
                    message=f"Take {med.dosage} of {med.medicine_name} — {med.frequency}.",
                    type="MEDICATION_REMINDER",
                    link=link_target,
                    is_read=False
                )
                db.add(notif)
                generated.append(f"Medication reminder for {med.medicine_name}")

    if generated:
        db.commit()

    return RemindersGenerationResponse(
        generated_count=len(generated),
        details=generated
    )
