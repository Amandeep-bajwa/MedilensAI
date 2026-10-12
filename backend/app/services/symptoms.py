import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.entities import SymptomInteraction, User
from app.schemas.symptom import (
    SymptomAnalyzeRequest,
    SymptomAnalysisResponse,
    RedFlagAlert,
    SymptomHistoryItem,
    CommonSymptomCategory
)
from app.services.audit import record_audit_log

logger = logging.getLogger(__name__)

MANDATORY_SYMPTOM_DISCLAIMER = (
    "MediLens AI provides educational triage assistance to help you communicate effectively with healthcare providers. "
    "It is NOT a medical diagnosis, clinical evaluation, or treatment plan. "
    "If you are experiencing life-threatening symptoms, call emergency medical services (such as 911 or 112) "
    "or proceed to the nearest emergency department immediately."
)

# Clinical Red-Flag Patterns: Symptoms that mandate EMERGENCY triage
RED_FLAG_PATTERNS = [
    {
        "keywords": ["chest pain", "pressure in chest", "crushing chest", "chest tightness", "pain radiating to arm", "pain radiating to jaw"],
        "reason": "Potential Acute Coronary Syndrome (Myocardial Infarction / Heart Attack)",
        "action": "Call emergency medical services (911/112) immediately. Do not drive yourself to the hospital."
    },
    {
        "keywords": ["slurred speech", "facial drooping", "face drooping", "arm weakness", "sudden weakness", "one side numb", "cannot speak"],
        "reason": "Signs of Acute Cerebrovascular Accident (Stroke / TIA - FAST criteria)",
        "action": "Immediate emergency care required. Time is critical for thrombolytic intervention."
    },
    {
        "keywords": ["cannot breathe", "severe shortness of breath", "choking", "stridor", "blue lips", "blue face", "gasping for air"],
        "reason": "Severe Respiratory Distress or Airway Compromise",
        "action": "Call emergency services immediately or seek emergency resuscitation."
    },
    {
        "keywords": ["throat swelling", "tongue swelling", "lips swelling", "anaphylaxis", "severe allergic reaction"],
        "reason": "Potential Anaphylactic Reaction (Airway Obstruction)",
        "action": "Administer intramuscular epinephrine (EpiPen) if available and call emergency services."
    },
    {
        "keywords": ["worst headache", "thunderclap headache", "sudden severe headache", "headache with stiff neck"],
        "reason": "Suspicion of Subarachnoid Hemorrhage or Meningitis",
        "action": "Seek immediate emergency department evaluation."
    },
    {
        "keywords": ["coughing blood", "vomiting blood", "throwing up blood", "black tarry stool", "uncontrolled bleeding"],
        "reason": "Active Severe Internal or Gastrointestinal Hemorrhage",
        "action": "Go to the nearest emergency department immediately."
    },
    {
        "keywords": ["unconscious", "passed out", "loss of consciousness", "unresponsive", "fainted"],
        "reason": "Acute Syncope or Neurological Impairment",
        "action": "Seek immediate urgent medical evaluation."
    }
]

# Urgent Clinical Patterns: Mandates URGENT physician evaluation within 24-48 hours
URGENT_PATTERNS = [
    {
        "keywords": ["high fever", "fever above 102", "fever above 103", "persistent fever", "shivering with fever"],
        "reason": "Potential systemic bacterial infection or febrile illness requiring clinical workup."
    },
    {
        "keywords": ["severe abdominal pain", "lower right abdominal", "sharp stomach pain", "severe belly pain"],
        "reason": "Potential acute abdomen (appendicitis, cholecystitis, or bowel obstruction)."
    },
    {
        "keywords": ["dehydration", "cannot keep fluids down", "vomiting for 2 days", "persistent diarrhea"],
        "reason": "Risk of significant electrolyte imbalance and acute kidney injury."
    },
    {
        "keywords": ["cannot bear weight", "suspected fracture", "bone fracture", "severe swelling joint"],
        "reason": "Potential structural bone fracture or acute inflammatory arthritis."
    },
    {
        "keywords": ["vision loss", "blurry vision sudden", "eye pain severe", "halos around lights"],
        "reason": "Acute ophthalmological emergency (glaucoma or retinal concern)."
    }
]

# Specialist Recommendation Mapping
SPECIALTY_RULES = [
    {
        "specialty": "Cardiologist",
        "keywords": ["chest", "palpitation", "heart", "racing heart", "irregular heartbeat", "shortness of breath on exertion"]
    },
    {
        "specialty": "Pulmonologist",
        "keywords": ["cough", "wheezing", "asthma", "phlegm", "breath", "lung", "sputum", "bronchitis"]
    },
    {
        "specialty": "Neurologist",
        "keywords": [
            "headache", "migraine", "dizziness", "vertigo", "tingling", "numbness",
            "tremor", "seizure", "memory", "speech", "slurred", "droop", "stroke", "weakness"
        ]
    },
    {
        "specialty": "Gastroenterologist",
        "keywords": ["stomach", "abdomen", "acid", "heartburn", "bloating", "nausea", "vomiting", "diarrhea", "constipation", "cramps"]
    },
    {
        "specialty": "Dermatologist",
        "keywords": ["rash", "skin", "itching", "hives", "eczema", "mole", "lesion", "acne", "hair loss"]
    },
    {
        "specialty": "Orthopedist / Rheumatologist",
        "keywords": ["joint", "knee", "back pain", "shoulder", "arthritis", "stiffness", "muscle pain", "spine", "hip"]
    },
    {
        "specialty": "Endocrinologist",
        "keywords": ["thyroid", "blood sugar", "excessive thirst", "unexplained weight loss", "heat intolerance", "cold intolerance"]
    },
    {
        "specialty": "ENT Specialist (Otolaryngologist)",
        "keywords": ["ear", "hearing", "throat", "sore throat", "tonsils", "sinus", "nasal", "congestion", "hoarseness"]
    }
]

# Common Categorized Symptoms for UI Selection
COMMON_SYMPTOM_CATEGORIES: List[CommonSymptomCategory] = [
    CommonSymptomCategory(
        category="General & Systemic",
        symptoms=["Fatigue & Weakness", "Mild Fever", "Chills & Sweating", "Unexplained Weight Loss", "Loss of Appetite"]
    ),
    CommonSymptomCategory(
        category="Respiratory",
        symptoms=["Persistent Dry Cough", "Productive Cough with Phlegm", "Shortness of Breath", "Wheezing", "Sore Throat", "Nasal Congestion"]
    ),
    CommonSymptomCategory(
        category="Cardiovascular",
        symptoms=["Chest Tightness", "Heart Palpitations", "Lightheadedness", "Swollen Ankles/Feet", "Dizziness"]
    ),
    CommonSymptomCategory(
        category="Gastrointestinal",
        symptoms=["Acid Reflux / Heartburn", "Abdominal Cramps", "Nausea & Vomiting", "Bloating", "Persistent Diarrhea", "Constipation"]
    ),
    CommonSymptomCategory(
        category="Neurological",
        symptoms=["Tension Headache", "Migraine", "Dizziness / Vertigo", "Numbness / Tingling", "Brain Fog"]
    ),
    CommonSymptomCategory(
        category="Musculoskeletal",
        symptoms=["Lower Back Pain", "Joint Stiffness", "Knee Pain", "Neck Stiffness", "Muscle Aches"]
    )
]

def detect_red_flags(text: str) -> List[RedFlagAlert]:
    """Scans text for clinical emergency keywords and constructs RedFlagAlert items."""
    alerts: List[RedFlagAlert] = []
    text_lower = text.lower()

    for rule in RED_FLAG_PATTERNS:
        for kw in rule["keywords"]:
            if kw in text_lower:
                alerts.append(
                    RedFlagAlert(
                        symptom=kw.title(),
                        urgency_reason=rule["reason"],
                        action_required=rule["action"]
                    )
                )
                break  # Don't duplicate for same pattern
    return alerts

def detect_urgent_signals(text: str, severity: Optional[int]) -> bool:
    """Evaluates whether symptoms trigger urgent priority (severity >= 8 or urgent keywords)."""
    if severity and severity >= 8:
        return True

    text_lower = text.lower()
    for rule in URGENT_PATTERNS:
        for kw in rule["keywords"]:
            if kw in text_lower:
                return True
    return False

def determine_specialist(text: str) -> str:
    """Identifies the most suitable clinical specialist based on symptom keywords."""
    text_lower = text.lower()
    for rule in SPECIALTY_RULES:
        for kw in rule["keywords"]:
            if kw in text_lower:
                return rule["specialty"]
    return "General Physician / Internal Medicine Specialist"

def generate_differential_and_tips(
    text: str,
    triage_level: str,
    specialist: str,
    duration: Optional[str] = None
) -> Tuple[str, List[str], List[str], List[str]]:
    """
    Constructs educational assessment narrative, possible non-definitive considerations,
    supportive care tips, and physician consultation prompts.
    """
    text_lower = text.lower()

    # Clinical Assessment Narrative
    if triage_level == "EMERGENCY":
        assessment = (
            "CRITICAL ALERT: Your described symptoms exhibit one or more clinical red-flag characteristics. "
            "These presentations can indicate acute cardiovascular, neurological, or severe respiratory events. "
            "Immediate emergency medical evaluation is paramount."
        )
        possible_causes = [
            "Acute clinical conditions requiring immediate diagnostic exclusion (e.g. cardiac ischemia, stroke, severe respiratory compromise)."
        ]
        tips = [
            "Do NOT attempt home remedies or wait for symptoms to resolve.",
            "Remain calm, seated or in a recovery position.",
            "Have someone stay with you and call emergency medical services immediately."
        ]
        questions = [
            "What immediate emergency interventions are indicated?",
            "What diagnostic imaging or cardiac/neurological markers need to be drawn?",
            "Are there vital sign instabilities requiring hospital admission?"
        ]
    elif triage_level == "URGENT":
        dur_str = f" persisting for {duration}" if duration else ""
        assessment = (
            f"Your reported symptoms{dur_str} suggest an acute or progressive clinical issue "
            "that warrants timely medical evaluation within the next 24 to 48 hours to avoid complications."
        )
        possible_causes = [
            "Acute infectious or inflammatory process requiring targeted medical evaluation.",
            "Exacerbation of an underlying physiological or musculoskeletal condition.",
            "Metabolic, gastrointestinal, or respiratory disturbance requiring lab confirmation."
        ]
        tips = [
            "Monitor body temperature and resting pulse twice daily.",
            "Maintain adequate hydration with water and electrolyte solutions.",
            "Avoid intense physical exertion until cleared by a physician."
        ]
        questions = [
            f"What primary diagnostic tests (blood panels, imaging) are recommended for these symptoms?",
            f"Is a referral to a {specialist} warranted at this stage?",
            "What warning signs should prompt me to seek emergency care instead?"
        ]
    else:
        dur_str = f" over the last {duration}" if duration else ""
        assessment = (
            f"Your reported symptoms{dur_str} appear consistent with a routine, non-emergency presentation. "
            "These findings frequently resolve with supportive comfort measures and primary care guidance."
        )
        possible_causes = [
            "Common mild viral or seasonal irritation.",
            "Muscular strain, postural fatigue, or environmental stress.",
            "Minor digestive or lifestyle-related sensitivity."
        ]
        tips = [
            "Ensure 7 to 8 hours of restorative sleep to facilitate immune recovery.",
            "Maintain continuous fluid hydration throughout the day.",
            "Keep a daily log noting when symptoms worsen or improve.",
            "Adopt gentle rest and avoid known environmental or dietary triggers."
        ]
        questions = [
            f"Given that these symptoms have lasted {duration or 'recently'}, what baseline checks do you advise?",
            "Are there specific dietary or lifestyle modifications you recommend?",
            "At what point would additional diagnostic tests become necessary?"
        ]

    return assessment, possible_causes, tips, questions

def analyze_symptoms_engine(
    request: SymptomAnalyzeRequest,
    current_user: User,
    db: Session
) -> SymptomAnalysisResponse:
    """
    Executes clinical symptom triage and educational assessment:
    1. Evaluates red-flag emergency symptoms.
    2. Determines triage classification (EMERGENCY, URGENT, ROUTINE).
    3. Maps to recommended medical specialty.
    4. Generates supportive tips and doctor consultation questions.
    5. Persists interaction into symptom_interactions table.
    6. Emits auditable event in audit_logs.
    """
    symptoms_text = request.symptoms.strip()

    # 1. Detect emergency red flags
    red_flags = detect_red_flags(symptoms_text)
    is_emergency = len(red_flags) > 0

    # 2. Determine Triage Level
    if is_emergency:
        triage_level = "EMERGENCY"
    elif detect_urgent_signals(symptoms_text, request.severity):
        triage_level = "URGENT"
    else:
        triage_level = "ROUTINE"

    # 3. Determine recommended specialist
    specialist = determine_specialist(symptoms_text)

    # 4. Generate assessment narrative, causes, tips, questions
    assessment, causes, tips, questions = generate_differential_and_tips(
        text=symptoms_text,
        triage_level=triage_level,
        specialist=specialist,
        duration=request.duration
    )

    # 5. Build rich JSON payload for persistence
    payload_to_store = {
        "triage_level": triage_level,
        "is_emergency": is_emergency,
        "red_flags": [rf.model_dump() for rf in red_flags],
        "recommended_specialist": specialist,
        "clinical_assessment": assessment,
        "possible_causes": causes,
        "supportive_care_tips": tips,
        "doctor_questions": questions,
        "duration": request.duration,
        "severity": request.severity
    }

    # 6. Persist to symptom_interactions table
    interaction = SymptomInteraction(
        user_id=current_user.user_id,
        symptom_input=symptoms_text,
        response=json.dumps(payload_to_store)
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    # 7. Record security audit log
    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="SYMPTOM_ANALYSIS_EXECUTED",
        result="Success",
        metadata_info={
            "triage_level": triage_level,
            "is_emergency": is_emergency,
            "red_flags_count": len(red_flags),
            "specialist": specialist,
            "severity": request.severity
        }
    )

    return SymptomAnalysisResponse(
        interaction_id=interaction.interaction_id,
        symptoms=symptoms_text,
        triage_level=triage_level,
        is_emergency=is_emergency,
        red_flags=red_flags,
        recommended_specialist=specialist,
        clinical_assessment=assessment,
        possible_causes=causes,
        supportive_care_tips=tips,
        doctor_questions=questions,
        disclaimer=MANDATORY_SYMPTOM_DISCLAIMER,
        created_at=interaction.created_at
    )

def get_user_symptom_history(
    current_user: User,
    db: Session
) -> List[SymptomHistoryItem]:
    """Retrieves previous symptom triage interactions for the authenticated user."""
    records = db.query(SymptomInteraction).filter(
        SymptomInteraction.user_id == current_user.user_id
    ).order_by(SymptomInteraction.created_at.desc()).limit(30).all()

    history: List[SymptomHistoryItem] = []
    for item in records:
        triage = "ROUTINE"
        spec = "General Physician"
        summary = item.symptom_input[:100]

        try:
            parsed = json.loads(item.response)
            triage = parsed.get("triage_level", "ROUTINE")
            spec = parsed.get("recommended_specialist", "General Physician")
            summary = parsed.get("clinical_assessment", item.symptom_input[:100])
        except Exception:
            pass

        history.append(
            SymptomHistoryItem(
                interaction_id=item.interaction_id,
                symptoms=item.symptom_input,
                triage_level=triage,
                recommended_specialist=spec,
                summary_text=summary[:140] + ("..." if len(summary) > 140 else ""),
                created_at=item.created_at
            )
        )
    return history
