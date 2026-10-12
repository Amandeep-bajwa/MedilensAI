from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RedFlagAlert(BaseModel):
    symptom: str = Field(..., description="The red-flag symptom detected")
    urgency_reason: str = Field(..., description="Clinical reason for urgent/emergency concern")
    action_required: str = Field(..., description="Action required by the patient (e.g., call 911 / go to ER)")

class SymptomAnalyzeRequest(BaseModel):
    symptoms: str = Field(..., min_length=3, max_length=1000, description="Description of symptoms experienced")
    duration: Optional[str] = Field(None, max_length=100, description="Duration (e.g. 2 hours, 3 days, 2 weeks)")
    severity: Optional[int] = Field(None, ge=1, le=10, description="Self-reported severity scale (1 to 10)")
    additional_notes: Optional[str] = Field(None, max_length=500, description="Underlying conditions or context")

class SymptomAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    symptoms: str
    triage_level: str = Field(..., description="Triage classification: EMERGENCY, URGENT, or ROUTINE")
    is_emergency: bool = Field(..., description="Flag indicating immediate emergency service requirement")
    red_flags: List[RedFlagAlert] = Field(default_factory=list, description="Identified red-flag clinical alerts")
    recommended_specialist: str = Field(..., description="Recommended medical specialty for consultation")
    clinical_assessment: str = Field(..., description="Patient-friendly educational overview of the symptoms")
    possible_causes: List[str] = Field(default_factory=list, description="Educational potential considerations")
    supportive_care_tips: List[str] = Field(default_factory=list, description="General non-pharmacological comfort steps")
    doctor_questions: List[str] = Field(default_factory=list, description="Actionable questions for physician appointment")
    disclaimer: str = Field(..., description="Mandatory clinical safety and non-diagnostic disclaimer")
    created_at: datetime

class SymptomHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    symptoms: str
    triage_level: str
    recommended_specialist: str
    summary_text: str
    created_at: datetime

class CommonSymptomCategory(BaseModel):
    category: str
    symptoms: List[str]
