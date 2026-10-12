from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

# ----------------- MEDICATION SCHEMAS -----------------

class MedicationBase(BaseModel):
    medicine_name: str = Field(..., min_length=2, max_length=150, description="Name of the prescribed medicine")
    dosage: str = Field(..., min_length=1, max_length=100, description="Dosage (e.g. 500mg, 10ml, 1 tablet)")
    frequency: str = Field(..., min_length=2, max_length=100, description="Administration frequency (e.g. Once daily morning, Twice daily with meals)")
    start_date: date = Field(..., description="Start date of medication course")
    end_date: Optional[date] = Field(None, description="Optional end or completion date")
    notes: Optional[str] = Field(None, max_length=500, description="Special instructions (e.g. Take after meals, with water)")

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    medicine_name: Optional[str] = Field(None, min_length=2, max_length=150)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(None, min_length=2, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)

class MedicationResponse(MedicationBase):
    model_config = ConfigDict(from_attributes=True)

    medication_id: str
    user_id: str
    is_active: bool = Field(True, description="Whether medication course is currently active")
    created_at: datetime

class MedicationListResponse(BaseModel):
    total: int
    items: List[MedicationResponse]


# ----------------- APPOINTMENT SCHEMAS -----------------

class AppointmentBase(BaseModel):
    doctor_name: str = Field(..., min_length=2, max_length=150, description="Name of the physician or specialist")
    specialization: str = Field(..., min_length=2, max_length=100, description="Medical specialization (e.g. Cardiologist, Neurologist, General Physician)")
    appointment_date: date = Field(..., description="Date of the scheduled appointment")
    appointment_time: str = Field(..., min_length=2, max_length=20, description="Time of appointment (e.g. 10:30 AM, 14:00)")
    location: Optional[str] = Field(None, max_length=255, description="Clinic name, hospital room, or telehealth link")
    notes: Optional[str] = Field(None, max_length=500, description="Clinical reason for consultation or preparation notes")
    status: str = Field("Upcoming", description="Status: Upcoming, Completed, or Cancelled")

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    doctor_name: Optional[str] = Field(None, min_length=2, max_length=150)
    specialization: Optional[str] = Field(None, min_length=2, max_length=100)
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = Field(None, min_length=2, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, description="Upcoming, Completed, or Cancelled")

class AppointmentResponse(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: str
    user_id: str
    created_at: datetime

class AppointmentListResponse(BaseModel):
    total: int
    items: List[AppointmentResponse]
