from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ReportBase(BaseModel):
    category: str = Field(default="Other", description="Clinical report category (e.g., CBC, Lipid Profile)")

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    category: Optional[str] = Field(None, description="Updated clinical category")

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    user_id: str
    file_name: str
    file_type: str
    category: str
    processing_status: str
    file_size_bytes: Optional[int] = None
    uploaded_at: datetime
    updated_at: datetime

class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    limit: int
