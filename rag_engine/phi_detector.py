"""
Healthcare RAG — PHI Detector & Redactor
Detects and redacts Protected Health Information from text.
"""
import re
from typing import Tuple

# PHI regex patterns
PATTERNS = {
    'SSN':          r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    'PHONE':        r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'EMAIL':        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'DATE':         r'\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](\d{2}|\d{4})\b',
    'MRN':          r'\b(MRN|Medical Record|Record No|Patient ID)[:\s#]*\d{4,12}\b',
    'DOB':          r'\b(DOB|Date of Birth|Born)[:\s]+\S+',
    'NAME_TRIGGER': r'\b(patient name|provider name|physician name)[:\s]+[A-Z][a-z]+(\s[A-Z][a-z]+)+',
    'ZIP':          r'\b\d{5}(-\d{4})?\b',
    'NPI':          r'\bNPI[:\s#]*\d{10}\b',
    'DEA':          r'\bDEA[:\s#]*[A-Z]{2}\d{7}\b',
}

CLINICAL_ESCALATION_KEYWORDS = [
    'diagnose', 'diagnosis', 'treatment plan', 'prescribe', 'prescription',
    'chest pain', 'difficulty breathing', 'stroke', 'heart attack', 'emergency',
    'overdose', 'suicide', 'seizure', 'allergic reaction', 'dosage for me',
    'my symptoms', 'what disease', 'do i have', 'should i take',
]


def detect_phi(text: str) -> Tuple[bool, list]:
    """Returns (has_phi, list of detected types)."""
    found = []
    txt_lower = text.lower()
    for name, pattern in PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(name)
    return bool(found), found


def redact_phi(text: str) -> str:
    """Replaces PHI tokens with [REDACTED-TYPE]."""
    for name, pattern in PATTERNS.items():
        text = re.sub(pattern, f'[REDACTED-{name}]', text, flags=re.IGNORECASE)
    return text


def is_clinical_query(text: str) -> bool:
    """Returns True if query appears to be asking for clinical/medical advice."""
    txt_lower = text.lower()
    return any(kw in txt_lower for kw in CLINICAL_ESCALATION_KEYWORDS)


def classify_query_risk(text: str) -> str:
    """Returns 'safe', 'clinical', or 'phi' risk level."""
    has_phi, _ = detect_phi(text)
    if has_phi:
        return 'phi'
    if is_clinical_query(text):
        return 'clinical'
    return 'safe'
