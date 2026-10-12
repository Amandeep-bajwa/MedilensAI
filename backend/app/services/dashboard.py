from typing import List, Dict
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.entities import (
    User,
    Report,
    Medication,
    Appointment,
    AIInteraction,
    SymptomInteraction,
    Notification
)
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardReportItem,
    DashboardMedicationItem,
    DashboardAppointmentItem,
    DashboardAIActivityItem
)
from app.services.health import is_medication_active

def get_dashboard_summary(current_user: User, db: Session) -> DashboardSummaryResponse:
    """Aggregates executive clinical and adherence metrics strictly for the authenticated patient."""
    user_id = current_user.user_id

    # 1. Reports Metrics
    reports_query = db.query(Report).filter(Report.user_id == user_id)
    total_reports = reports_query.count()

    status_counts_raw = (
        db.query(Report.processing_status, func.count(Report.report_id))
        .filter(Report.user_id == user_id)
        .group_by(Report.processing_status)
        .all()
    )
    reports_by_status: Dict[str, int] = {
        "Uploaded": 0,
        "Processing": 0,
        "Completed": 0,
        "Failed": 0
    }
    for st, count in status_counts_raw:
        reports_by_status[st] = count

    recent_reports_records = (
        reports_query.order_by(Report.uploaded_at.desc())
        .limit(5)
        .all()
    )
    recent_reports = [
        DashboardReportItem.model_validate(r) for r in recent_reports_records
    ]

    # 2. Medications Metrics
    all_meds = (
        db.query(Medication)
        .filter(Medication.user_id == user_id)
        .order_by(Medication.start_date.desc())
        .all()
    )
    active_med_items: List[DashboardMedicationItem] = []
    for med in all_meds:
        active = is_medication_active(med.start_date, med.end_date)
        if active:
            active_med_items.append(
                DashboardMedicationItem(
                    medication_id=med.medication_id,
                    medicine_name=med.medicine_name,
                    dosage=med.dosage,
                    frequency=med.frequency,
                    start_date=med.start_date,
                    end_date=med.end_date,
                    is_active=True
                )
            )

    active_medications_count = len(active_med_items)
    displayed_meds = active_med_items[:5]

    # 3. Appointments Metrics
    appts_query = (
        db.query(Appointment)
        .filter(Appointment.user_id == user_id, Appointment.status == "Upcoming")
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
    )
    upcoming_appointments_count = appts_query.count()
    upcoming_appointments = [
        DashboardAppointmentItem.model_validate(a) for a in appts_query.limit(5).all()
    ]

    # 4. Notifications Metric
    unread_notifications_count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )

    # 5. Recent AI Activity Aggregation
    recent_ai: List[DashboardAIActivityItem] = []

    # RAG & AI Queries
    rag_interactions = (
        db.query(AIInteraction)
        .filter(AIInteraction.user_id == user_id)
        .order_by(AIInteraction.created_at.desc())
        .limit(5)
        .all()
    )
    for inter in rag_interactions:
        recent_ai.append(
            DashboardAIActivityItem(
                id=inter.interaction_id,
                activity_type="RAG_QUESTION",
                summary=f"Asked: \"{inter.question[:50]}...\"",
                timestamp=inter.created_at,
                reference_id=inter.report_id
            )
        )

    # Symptom Triage Interactions
    symptom_ints = (
        db.query(SymptomInteraction)
        .filter(SymptomInteraction.user_id == user_id)
        .order_by(SymptomInteraction.created_at.desc())
        .limit(3)
        .all()
    )
    for sym in symptom_ints:
        recent_ai.append(
            DashboardAIActivityItem(
                id=sym.interaction_id,
                activity_type="SYMPTOM_TRIAGE",
                summary=f"Symptom assessment: \"{sym.symptom_input[:50]}...\"",
                timestamp=sym.created_at,
                reference_id=None
            )
        )

    # Sort combined AI activities chronologically
    recent_ai.sort(key=lambda x: x.timestamp, reverse=True)
    displayed_ai = recent_ai[:5]

    return DashboardSummaryResponse(
        total_reports=total_reports,
        reports_by_status=reports_by_status,
        active_medications_count=active_medications_count,
        upcoming_appointments_count=upcoming_appointments_count,
        unread_notifications_count=unread_notifications_count,
        recent_reports=recent_reports,
        active_medications=displayed_meds,
        upcoming_appointments=upcoming_appointments,
        recent_ai_activity=displayed_ai
    )
