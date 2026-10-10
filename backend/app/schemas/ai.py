from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AbnormalFindingItem(BaseModel):
    parameter_name: str = Field(..., description="Name of the abnormal lab parameter")
    observed_value: str = Field(..., description="Observed patient measurement")
    reference_interval: str = Field(..., description="Normal physiological reference interval")
    flag: str = Field(..., description="Clinical flag: HIGH or LOW")
    plain_english_explanation: str = Field(..., description="Jargon-free explanation of what this marker indicates")

class ReportSummaryRequest(BaseModel):
    focus_areas: Optional[str] = Field(None, description="Optional patient focus areas (e.g. cardiovascular risk, metabolic health)")
    language: Optional[str] = Field("en", description="Target language code (default 'en')")

class ReportExplanationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    report_id: str
    summary: str = Field(..., description="High-level, patient-friendly summary of the medical report")
    key_findings: List[str] = Field(default_factory=list, description="Bullet-point breakdown of key findings")
    abnormal_findings: List[AbnormalFindingItem] = Field(default_factory=list, description="Out-of-range clinical parameters requiring physician review")
    lifestyle_recommendations: List[str] = Field(default_factory=list, description="General health and wellness tips")
    doctor_questions: List[str] = Field(default_factory=list, description="Actionable questions for the patient to ask their physician")
    disclaimer: str = Field(..., description="Mandatory medical and clinical safety disclaimer")
    provider_used: str = Field(..., description="AI service provider (gemini, openai, or clinical_rules_engine)")
    created_at: datetime

class AskReportQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Patient question regarding their lab findings")

class AskReportQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    report_id: str
    question: str
    answer: str
    disclaimer: str
    created_at: datetime

class AIInteractionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    report_id: Optional[str] = None
    question: str
    response: str
    created_at: datetime
