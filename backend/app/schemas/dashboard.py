from typing import List, Optional, Dict
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field

class DashboardReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    file_name: str
    file_type: str
    category: str
    processing_status: str
    uploaded_at: datetime

class DashboardMedicationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    medication_id: str
    medicine_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    is_active: bool

class DashboardAppointmentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: str
    doctor_name: str
    specialization: str
    appointment_date: date
    appointment_time: str
    location: Optional[str] = None
    status: str

class DashboardAIActivityItem(BaseModel):
    id: str
    activity_type: str  # "REPORT_EXPLANATION", "RAG_QUESTION", "SYMPTOM_TRIAGE"
    summary: str
    timestamp: datetime
    reference_id: Optional[str] = None

class DashboardSummaryResponse(BaseModel):
    total_reports: int
    reports_by_status: Dict[str, int]
    active_medications_count: int
    upcoming_appointments_count: int
    unread_notifications_count: int
    
    recent_reports: List[DashboardReportItem]
    active_medications: List[DashboardMedicationItem]
    upcoming_appointments: List[DashboardAppointmentItem]
    recent_ai_activity: List[DashboardAIActivityItem]
