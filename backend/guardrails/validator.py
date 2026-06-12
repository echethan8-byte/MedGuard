"""
guardrails/validator.py — Input and output validation for healthcare RAG.
"""
import re
import logging
from typing import Tuple, List

logger = logging.getLogger('medguard')

# ─── Input Guardrails ──────────────────────────────────────────────────────────

PROMPT_INJECTION_PATTERNS = [
    r'ignore (previous|all|above) instructions',
    r'forget (your|all) (instructions|rules)',
    r'you are now',
    r'act as (a|an)',
    r'system prompt',
    r'jailbreak',
    r'DAN mode',
    r'<script',
    r'DROP TABLE',
    r'SELECT .* FROM',
]

PII_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',           # SSN
    r'\b\d{10,16}\b',                    # Generic long numbers (MRN etc)
    r'\b[A-Z]{2}\d{6,8}\b',              # Passport-style
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b.*?(born|dob|birth)',  # DOB patterns
]

MAX_QUERY_LENGTH = 5000
MIN_QUERY_LENGTH = 10


def validate_input(text: str) -> Tuple[bool, List[str]]:
    """
    Validate user input for prompt injection and PII.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    if len(text) < MIN_QUERY_LENGTH:
        issues.append(f"Input too short (min {MIN_QUERY_LENGTH} chars).")

    if len(text) > MAX_QUERY_LENGTH:
        issues.append(f"Input too long (max {MAX_QUERY_LENGTH} chars). Got {len(text)}.")
        text = text[:MAX_QUERY_LENGTH]

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"Potential prompt injection detected: '{pattern}'")
            logger.warning(f"Prompt injection pattern matched: {pattern}")

    for pattern in PII_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append("Possible PII detected in input. Please anonymize before uploading.")
            logger.warning("PII pattern detected in input")
            break

    return len(issues) == 0, issues


def redact_pii(text: str) -> str:
    """Redact common PII patterns from text."""
    # SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN-REDACTED]', text)
    # Phone numbers
    text = re.sub(r'\b(\+1[\s-])?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b', '[PHONE-REDACTED]', text)
    # Email
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL-REDACTED]', text)
    return text


# ─── Output Guardrails ─────────────────────────────────────────────────────────

REQUIRED_REPORT_FIELDS = ['compliance_score', 'violations', 'summary', 'citations']
VALID_RISK_LEVELS = {'critical', 'high', 'medium', 'low'}


def validate_output(report: dict) -> Tuple[bool, List[str]]:
    """
    Validate LLM output structure and content quality.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    # Check required fields
    for field in REQUIRED_REPORT_FIELDS:
        if field not in report:
            issues.append(f"Missing required field: {field}")

    # Validate score
    score = report.get('compliance_score')
    if score is not None:
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            issues.append(f"Invalid compliance_score: {score} (must be 0–100)")

    # Validate violations
    violations = report.get('violations', [])
    if not isinstance(violations, list):
        issues.append("violations must be a list")
    else:
        for i, v in enumerate(violations):
            if not isinstance(v, dict):
                issues.append(f"Violation {i} is not a dict")
                continue
            if v.get('risk') not in VALID_RISK_LEVELS:
                issues.append(f"Violation {i} has invalid risk level: {v.get('risk')}")
            if not v.get('evidence'):
                issues.append(f"Violation {i} missing evidence (hallucination risk)")
            if not v.get('citation'):
                issues.append(f"Violation {i} missing citation")

    # Check for empty summary
    if not report.get('summary', '').strip():
        issues.append("Empty summary in output")

    if issues:
        logger.warning(f"Output validation issues: {issues}")

    return len(issues) == 0, issues


def sanitize_output(report: dict) -> dict:
    """
    Auto-fix minor issues in LLM output.
    - Clamp score to 0–100
    - Filter out violations with invalid risk levels
    - Strip whitespace
    """
    if 'compliance_score' in report:
        try:
            report['compliance_score'] = max(0, min(100, float(report['compliance_score'])))
        except (TypeError, ValueError):
            report['compliance_score'] = 0

    if 'violations' in report and isinstance(report['violations'], list):
        valid_violations = []
        for v in report['violations']:
            if isinstance(v, dict) and v.get('risk') in VALID_RISK_LEVELS:
                # Sanitize strings
                for key in ['title', 'description', 'evidence', 'citation', 'corrective_action']:
                    if key in v:
                        v[key] = str(v[key]).strip()
                valid_violations.append(v)
        report['violations'] = valid_violations

    if 'summary' in report:
        report['summary'] = str(report['summary']).strip()

    return report
