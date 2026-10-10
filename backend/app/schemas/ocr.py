from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class LabParameter(BaseModel):
    name: str = Field(..., description="Name of laboratory test (e.g. Hemoglobin, Glucose)")
    value: str = Field(..., description="Observed measurement value")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g. g/dL, mg/dL)")
    reference_range: Optional[str] = Field(None, description="Standard clinical reference interval")
    status: str = Field("NORMAL", description="Clinical flag: NORMAL, HIGH, LOW, or UNKNOWN")

class ReportChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    report_id: str
    chunk_text: str
    page_number: Optional[str] = None
    embedding_reference: Optional[str] = None
    created_at: datetime

class OCRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ocr_id: str
    report_id: str
    extracted_text: str
    confidence: float
    status: str
    parameters: List[LabParameter] = []
    total_chunks: int = 0
    created_at: datetime

class ChunksListResponse(BaseModel):
    report_id: str
    total_chunks: int
    chunks: List[ReportChunkResponse]
