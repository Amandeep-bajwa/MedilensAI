from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Text, Float, DateTime, ForeignKey, Date, Time, JSON, Boolean
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # user / admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="user", cascade="all, delete-orphan")
    symptom_interactions = relationship("SymptomInteraction", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, png, jpg, jpeg
    file_path = Column(String(500), nullable=False)
    category = Column(String(50), default="Other", nullable=False)  # CBC, Blood Test, Lipid Profile, etc.
    processing_status = Column(String(30), default="Uploaded", nullable=False)  # Uploaded, Processing, Completed, Failed
    uploaded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reports")
    ocr_record = relationship("OCR", back_populates="report", uselist=False, cascade="all, delete-orphan")
    chunks = relationship("ReportChunk", back_populates="report", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="report", cascade="all, delete-orphan")

class OCR(Base):
    __tablename__ = "ocr_records"

    ocr_id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.report_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    extracted_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(30), default="Pending", nullable=False)  # Pending, Completed, Failed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    report = relationship("Report", back_populates="ocr_record")

class ReportChunk(Base):
    __tablename__ = "report_chunks"

    chunk_id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    page_number = Column(String(20), nullable=True)
    embedding_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    report = relationship("Report", back_populates="chunks")

class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    interaction_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_interactions")
    report = relationship("Report", back_populates="ai_interactions")

class SymptomInteraction(Base):
    __tablename__ = "symptom_interactions"

    interaction_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    symptom_input = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    user = relationship("User", back_populates="symptom_interactions")

class Medication(Base):
    __tablename__ = "medications"

    medication_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name = Column(String(150), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    user = relationship("User", back_populates="medications")

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(150), nullable=False)
    specialization = Column(String(100), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(20), nullable=False)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="Upcoming", nullable=False)  # Upcoming, Completed, Cancelled
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    user = relationship("User", back_populates="appointments")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False)
    result = Column(String(20), nullable=False)  # Success / Failure
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    metadata_info = Column(JSON, nullable=True)

    # Relationship
    user = relationship("User", back_populates="audit_logs")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="INFO", nullable=False)  # REPORT_PROCESSED, MEDICATION_REMINDER, APPOINTMENT_REMINDER, SYSTEM
    is_read = Column(Boolean, default=False, nullable=False)
    link = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    user = relationship("User", back_populates="notifications")
