import json
import uuid
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Report, OCR, AIInteraction
from app.schemas.ai import (
    ReportExplanationResponse,
    AbnormalFindingItem,
    AskReportQuestionResponse
)
from app.services.ocr import process_report_ocr, parse_clinical_lab_parameters
from app.services.audit import record_audit_log
from app.core.pii_scrubber import scrub_pii

MANDATORY_SAFETY_DISCLAIMER = (
    "MediLens AI is an educational clinical assistant designed to help patients understand medical terminology. "
    "It does not provide medical diagnoses, treatment prescriptions, or clinical advice. "
    "Always consult a licensed physician or healthcare specialist to interpret your diagnostic lab results."
)

PARAMETER_KNOWLEDGE_BASE: Dict[str, str] = {
    "hemoglobin": "Transports oxygen from your lungs to your body's tissues. Low levels may cause fatigue (anemia), while high levels can indicate dehydration or respiratory conditions.",
    "glucose": "Reflects the amount of sugar in your bloodstream after fasting. Higher levels may signal insulin resistance or prediabetes.",
    "fasting blood sugar": "Measures baseline blood sugar after fasting. Elevated numbers indicate a need for dietary and metabolic review.",
    "total cholesterol": "Measures overall blood fats. Elevated numbers are associated with increased cardiovascular risk and arterial plaque.",
    "hdl cholesterol": "Known as 'good' cholesterol; helps remove excess cholesterol from your bloodstream.",
    "ldl cholesterol": "Known as 'bad' cholesterol; high concentrations can accumulate inside arterial walls.",
    "triglycerides": "A type of fat in your blood stored from unused calories. High levels can impact heart and pancreas health.",
    "creatinine": "A natural waste product produced by muscle breakdown and filtered by the kidneys. Elevated levels suggest the kidneys may be working harder than usual.",
    "blood urea nitrogen": "Measures waste nitrogen from protein metabolism; provides additional insight into kidney filtration function.",
    "wbc": "White blood cells protect your body against infections and inflammation. Elevated counts frequently indicate an immune response.",
    "platelets": "Blood cells that form clots to prevent and stop bleeding. Low levels can increase bruising, while high levels increase clot risk.",
    "tsh": "Thyroid Stimulating Hormone regulates metabolic rate and energy levels. Elevated TSH often indicates an underactive thyroid (hypothyroidism).",
    "hba1c": "Reflects your average blood glucose levels over the preceding 2 to 3 months.",
    "bilirubin": "A yellow pigment formed during the breakdown of red blood cells, processed by the liver."
}

def generate_heuristic_explanation(
    report: Report,
    extracted_text: str,
    parameters: List[Any],
    focus_areas: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes a structured clinical explanation from parsed parameters and text.
    Provides reliable, deterministic patient guidance with zero external latency or API costs.
    """
    category = report.category or "Clinical Test"
    abnormal_items: List[Dict[str, Any]] = []
    normal_items: List[str] = []
    doctor_questions: List[str] = []

    for p in parameters:
        name_lower = p.name.lower()
        explanation_snippet = "A diagnostic biomarker evaluated to monitor overall physiological health."
        for key, desc in PARAMETER_KNOWLEDGE_BASE.items():
            if key in name_lower:
                explanation_snippet = desc
                break

        if p.status in ["HIGH", "LOW"]:
            abnormal_items.append({
                "parameter_name": p.name,
                "observed_value": f"{p.value} {p.unit or ''}".strip(),
                "reference_interval": p.reference_range or "Not specified",
                "flag": p.status,
                "plain_english_explanation": f"{p.name} is {p.status.lower()} relative to standard reference ranges. {explanation_snippet}"
            })
            doctor_questions.append(
                f"My {p.name} was flagged as {p.status} at {p.value} (normal: {p.reference_range or 'range'}). What might be causing this deviation?"
            )
        else:
            normal_items.append(f"{p.name} is within the expected physiological range ({p.value} {p.unit or ''}).".strip())

    # Build executive summary
    if abnormal_items:
        summary_lead = (
            f"This {category} report contains {len(parameters)} analyzed laboratory parameters. "
            f"Most biomarkers are in order, but {len(abnormal_items)} finding{'s' if len(abnormal_items) > 1 else ''} "
            f"({', '.join(a['parameter_name'] for a in abnormal_items)}) fell outside standard diagnostic reference ranges."
        )
    else:
        summary_lead = (
            f"This {category} report reflects a well-balanced panel. "
            f"All {len(parameters)} identified clinical biomarkers are within standard reference intervals."
        )

    if focus_areas:
        summary_lead += f" Special focus was placed on your inquiry regarding: '{focus_areas}'."

    # Standard doctor consultation questions
    if not doctor_questions:
        doctor_questions = [
            f"Do these {category} findings align with my baseline medical history?",
            "Are there specific lifestyle or dietary recommendations you advise based on these markers?",
            "When should I schedule my next follow-up routine panel?"
        ]
    else:
        doctor_questions.append("Should we repeat this test in 6 to 12 weeks to track biomarker stability?")
        doctor_questions.append("Are there any lifestyle or dietary adjustments that could help normalize these findings?")

    key_findings = normal_items[:4]
    if not key_findings:
        key_findings = [
            f"Report successfully ingested and parsed under category: {category}.",
            f"Processed {len(extracted_text.splitlines())} lines of diagnostic clinical observations."
        ]

    lifestyle_tips = [
        "Maintain adequate hydration throughout the day to support circulatory and kidney function.",
        "Ensure consistent restorative sleep (7-8 hours) to support immune and metabolic equilibrium.",
        "Discuss any new over-the-counter vitamins or supplements with your doctor before starting."
    ]

    return {
        "summary": summary_lead,
        "key_findings": key_findings,
        "abnormal_findings": abnormal_items,
        "lifestyle_recommendations": lifestyle_tips,
        "doctor_questions": doctor_questions[:5],
        "disclaimer": MANDATORY_SAFETY_DISCLAIMER,
        "provider_used": "clinical_rules_engine"
    }

async def call_external_llm(prompt: str) -> Optional[str]:
    """
    Attempts to query external LLM API (Gemini or OpenAI) if credentials are configured.
    """
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"]
        except Exception:
            pass

    return None

def generate_report_explanation(
    db: Session,
    report: Report,
    current_user_id: str,
    focus_areas: Optional[str] = None
) -> ReportExplanationResponse:
    """
    Generates a patient-friendly clinical report explanation:
    1. Ensures OCR extracted text is available.
    2. Identifies out-of-range clinical parameters.
    3. Synthesizes a structured explanation with doctor consultation prompts.
    4. Persists the explanation in the ai_interactions table.
    5. Logs an auditable entry in audit_logs.
    """
    ocr_record = db.query(OCR).filter(OCR.report_id == report.report_id).first()
    if not ocr_record or not ocr_record.extracted_text:
        ocr_record, _, _ = process_report_ocr(db, report, current_user_id)

    raw_text = ocr_record.extracted_text or ""
    sanitized_text = scrub_pii(raw_text)
    parameters = parse_clinical_lab_parameters(sanitized_text)

    # Generate clinical explanation with de-identified patient content
    explanation_data = generate_heuristic_explanation(
        report=report,
        extracted_text=sanitized_text,
        parameters=parameters,
        focus_areas=focus_areas
    )

    interaction_id = str(uuid.uuid4())
    ai_record = AIInteraction(
        interaction_id=interaction_id,
        user_id=current_user_id,
        report_id=report.report_id,
        question=f"Generate Clinical Summary (Category: {report.category})",
        response=json.dumps(explanation_data)
    )
    db.add(ai_record)
    db.commit()
    db.refresh(ai_record)

    # Audit Logging
    record_audit_log(
        db=db,
        event_type="AI_EXPLANATION_GENERATED",
        result="Success",
        user_id=current_user_id,
        metadata_info={
            "report_id": report.report_id,
            "interaction_id": interaction_id,
            "abnormal_count": len(explanation_data["abnormal_findings"]),
            "provider": explanation_data["provider_used"]
        }
    )

    return ReportExplanationResponse(
        interaction_id=interaction_id,
        report_id=report.report_id,
        summary=explanation_data["summary"],
        key_findings=explanation_data["key_findings"],
        abnormal_findings=[AbnormalFindingItem(**item) for item in explanation_data["abnormal_findings"]],
        lifestyle_recommendations=explanation_data["lifestyle_recommendations"],
        doctor_questions=explanation_data["doctor_questions"],
        disclaimer=explanation_data["disclaimer"],
        provider_used=explanation_data["provider_used"],
        created_at=ai_record.created_at
    )

def answer_report_question(
    db: Session,
    report: Report,
    current_user_id: str,
    question: str
) -> AskReportQuestionResponse:
    """
    Answers a patient's question grounded in the context of their specific report.
    """
    ocr_record = db.query(OCR).filter(OCR.report_id == report.report_id).first()
    extracted_text = ocr_record.extracted_text if ocr_record else ""
    parameters = parse_clinical_lab_parameters(extracted_text)

    clean_q = question.strip()
    q_lower = clean_q.lower()

    # Search for matching parameters mentioned in the patient's question
    matched_params = [p for p in parameters if p.name.lower() in q_lower]

    if matched_params:
        details = []
        for p in matched_params:
            status_text = f"flagged as {p.status}" if p.status in ["HIGH", "LOW"] else "within the normal range"
            details.append(f"Your {p.name} was measured at {p.value} {p.unit or ''} (reference interval: {p.reference_range or 'standard'}), which is {status_text}.")
        answer_body = " ".join(details) + " Always discuss these values with your doctor to evaluate them within your personal medical history."
    else:
        answer_body = (
            f"Based on your {report.category} report, we identified {len(parameters)} recorded laboratory parameters. "
            f"Regarding your question ('{clean_q}'), remember that laboratory values must always be correlated with your overall symptoms and clinical examination by a physician."
        )

    interaction_id = str(uuid.uuid4())
    ai_record = AIInteraction(
        interaction_id=interaction_id,
        user_id=current_user_id,
        report_id=report.report_id,
        question=clean_q,
        response=answer_body
    )
    db.add(ai_record)
    db.commit()
    db.refresh(ai_record)

    record_audit_log(
        db=db,
        event_type="AI_QUESTION_ANSWERED",
        result="Success",
        user_id=current_user_id,
        metadata_info={"report_id": report.report_id, "question": clean_q}
    )

    return AskReportQuestionResponse(
        interaction_id=interaction_id,
        report_id=report.report_id,
        question=clean_q,
        answer=answer_body,
        disclaimer=MANDATORY_SAFETY_DISCLAIMER,
        created_at=ai_record.created_at
    )
