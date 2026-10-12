from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_reports: int = 0
    total_medications: int = 0
    total_appointments: int = 0

class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Updated full name")

class UserStatusUpdateRequest(BaseModel):
    is_active: Optional[bool] = Field(None, description="Toggle user active status")
    role: Optional[str] = Field(None, description="Update role (user or admin)")

class AuditLogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    user_id: Optional[str] = None
    event_type: str
    result: str
    timestamp: datetime
    metadata_info: Optional[dict] = None

class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogItemResponse]

