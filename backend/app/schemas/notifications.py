from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class NotificationBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150, description="Brief notification headline")
    message: str = Field(..., min_length=2, max_length=1000, description="Notification message body")
    type: str = Field("INFO", max_length=50, description="Type: REPORT_PROCESSED, MEDICATION_REMINDER, APPOINTMENT_REMINDER, SYSTEM")
    link: Optional[str] = Field(None, max_length=255, description="Optional target route or resource identifier")

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    notification_id: str
    user_id: str
    is_read: bool
    created_at: datetime

class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationResponse]

class RemindersGenerationResponse(BaseModel):
    generated_count: int
    details: List[str]
