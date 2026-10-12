import re

# Compiled regex patterns for medical document de-identification (HIPAA Safe Harbor aligned)
PATIENT_NAME_PATTERN = re.compile(
    r"(?i)\b(patient\s*(?:name)?|pt\.?\s*name)\s*:\s*[A-Za-z\s.'-]+(?=[|\n\r]|$)"
)
DOB_PATTERN = re.compile(
    r"(?i)\b(dob|date\s*of\s*birth|birth\s*date)\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
SSN_OR_GOV_ID_PATTERN = re.compile(
    r"\b(?:\d{3}-\d{2}-\d{4}|\d{9,12})\b"
)
ADDRESS_PATTERN = re.compile(
    r"\b\d+\s+[A-Za-z0-9\s,.'-]{3,}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Terrace|Ter|Way|Place|Pl)\b",
    re.IGNORECASE
)

def scrub_pii(text: str) -> str:
    """
    Sanitizes personally identifiable information (PII) from clinical text
    before transmitting data to external LLM providers (SEC-PRIV-005, SEC-AI-002).
    Preserves diagnostic terms, reference ranges, and lab biomarker names.
    """
    if not text:
        return text

    sanitized = text

    # Mask Patient Name
    sanitized = PATIENT_NAME_PATTERN.sub(r"\1: [REDACTED_PATIENT_NAME]", sanitized)

    # Mask Date of Birth
    sanitized = DOB_PATTERN.sub(r"\1: [REDACTED_DOB]", sanitized)

    # Mask Emails
    sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)

    # Mask Phone Numbers
    sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)

    # Mask SSN / Gov IDs
    sanitized = SSN_OR_GOV_ID_PATTERN.sub("[REDACTED_ID]", sanitized)

    # Mask Physical Addresses
    sanitized = ADDRESS_PATTERN.sub("[REDACTED_ADDRESS]", sanitized)

    return sanitized
