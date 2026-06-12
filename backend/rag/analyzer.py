"""
rag/analyzer.py — Chain-of-Thought violation detection via LLM.
"""
import json
import logging
import time
from typing import Dict, Any, List, Optional
from django.conf import settings

logger = logging.getLogger('medguard')


SYSTEM_PROMPT = """You are MedGuard, an expert healthcare compliance AI auditor with deep knowledge of:
- WHO Infection Prevention & Control (IPC) Guidelines
- CDC National Healthcare Safety Network (NHSN) Protocols
- HHS Hospital-Acquired Condition Prevention guidelines
- OSHA Bloodborne Pathogens Standard (29 CFR 1910.1030)
- The Joint Commission (TJC) Infection Control standards
- CDC MDRO Management Guidelines

Your task is to analyze a hospital policy document and identify compliance violations against the retrieved regulatory policy chunks provided.

You MUST follow this Chain-of-Thought reasoning process:
Step 1: Summarize the hospital document's key procedures and policies.
Step 2: For each retrieved policy chunk, check if the hospital document addresses the requirement.
Step 3: Identify specific mismatches, gaps, or non-compliant sections.
Step 4: Assess risk level for each finding (critical/high/medium/low).
Step 5: Generate corrective actions grounded ONLY in the retrieved evidence.
Step 6: Calculate an overall compliance score (0–100).

CRITICAL RULES:
- Base ALL findings only on retrieved policy chunks. Do NOT cite policies not in the context.
- Quote exact evidence from the hospital document for each violation.
- Be specific and actionable in corrective actions.
- Do NOT hallucinate regulation IDs or policy requirements.

Respond ONLY with valid JSON in the following schema (no markdown, no preamble):
{
  "cot_reasoning": "string — your full step-by-step reasoning",
  "summary": "string — 2-3 sentence executive summary",
  "compliance_score": number (0-100),
  "violations": [
    {
      "regulation_id": "string — e.g. WHO-IPC-2.3",
      "title": "string — short descriptive title",
      "description": "string — detailed explanation of the gap",
      "risk": "critical|high|medium|low",
      "evidence": "string — exact quote or paraphrase from hospital doc",
      "citation": "string — exact policy source from context chunks",
      "corrective_action": "string — specific, actionable steps",
      "category": "string — e.g. Infection Control, HAI Prevention"
    }
  ],
  "citations": ["string — list of all policy sources referenced"],
  "recommendations_summary": "string — top 3 priority recommendations"
}"""


def build_audit_prompt(document_text: str, policy_context: str, doc_name: str) -> str:
    return f"""HOSPITAL DOCUMENT: {doc_name}
=====================================
{document_text[:6000]}
=====================================

RETRIEVED REGULATORY POLICY CONTEXT:
=====================================
{policy_context}
=====================================

Now perform the full compliance audit following the Chain-of-Thought steps in your system instructions.
Output ONLY valid JSON."""


def call_gemini(prompt: str, system: str) -> Dict[str, Any]:
    """Call Google Gemini API."""
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.LLM_MODEL,
        system_instruction=system,
        generation_config={
            "temperature": settings.LLM_TEMPERATURE,
            "max_output_tokens": settings.LLM_MAX_TOKENS,
            "response_mime_type": "application/json",
        }
    )
    response = model.generate_content(prompt)
    text = response.text.strip()
    return json.loads(text)


def call_openai(prompt: str, system: str) -> Dict[str, Any]:
    """Call OpenAI API."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def call_llm(prompt: str, system: str = SYSTEM_PROMPT) -> Dict[str, Any]:
    """Route to configured LLM provider with fallback."""
    provider = settings.LLM_PROVIDER

    try:
        if provider == 'gemini' and settings.GEMINI_API_KEY:
            return call_gemini(prompt, system)
        elif provider == 'openai' and settings.OPENAI_API_KEY:
            return call_openai(prompt, system)
        else:
            raise ValueError(f"No valid LLM provider configured (provider={provider})")
    except Exception as e:
        logger.error(f"LLM call failed with provider={provider}: {e}")
        # Fallback: try openai if gemini failed
        if provider == 'gemini' and settings.OPENAI_API_KEY:
            logger.info("Falling back to OpenAI")
            return call_openai(prompt, system)
        raise


def run_compliance_analysis(
    document: Any,
    policy_chunks: List[Dict],
    document_chunks: List[Dict],
) -> Dict[str, Any]:
    """
    Main analysis pipeline:
    1. Build context from policy + doc chunks
    2. Call LLM with CoT prompt
    3. Return structured result
    """
    from rag.retriever import build_context_string

    start_time = time.time()

    # Build document text from its chunks
    doc_text = "\n\n".join([c["text"] for c in document_chunks[:10]])
    policy_context = build_context_string(policy_chunks)

    prompt = build_audit_prompt(doc_text, policy_context, document.name)

    logger.info(f"Calling LLM ({settings.LLM_MODEL}) for document: {document.name}")
    result = call_llm(prompt)

    elapsed_ms = int((time.time() - start_time) * 1000)
    result["processing_time_ms"] = elapsed_ms
    result["llm_model"] = settings.LLM_MODEL
    result["embedding_model"] = settings.EMBEDDING_MODEL
    result["chunks_retrieved"] = len(policy_chunks)
    result["chunks_reranked"] = len(policy_chunks)  # already filtered

    logger.info(f"LLM analysis complete: score={result.get('compliance_score')}, violations={len(result.get('violations', []))}, time={elapsed_ms}ms")
    return result


def mock_analysis_result(document_name: str) -> Dict[str, Any]:
    """
    Mock result for development/testing when no LLM key is configured.
    Returns a realistic-looking audit result.
    """
    return {
        "cot_reasoning": "Step 1: Document describes ICU infection control procedures including hand hygiene, CLABSI prevention, and VAP bundles. Step 2: Comparing against WHO IPC 2022, CDC NHSN, HHS HAP guidelines. Step 3: Found 6 gaps including incomplete WHO 5 Moments coverage and missing chlorhexidine oral care. Step 4: Assessed risks as critical (x1), high (x2), medium (x2), low (x1). Step 5: Generated specific corrective actions per gap. Step 6: Score = 61/100.",
        "summary": f"The document '{document_name}' demonstrates partial compliance. Critical gaps in hand hygiene (WHO 5 Moments) and CLABSI prevention require immediate attention. 2 critical and 2 high-risk findings identified.",
        "compliance_score": 61,
        "violations": [
            {"regulation_id": "WHO-IPC-2.3", "title": "Hand Hygiene Protocol Gap", "description": "Document only requires hand hygiene before invasive procedures, missing 4 of the 5 WHO moments.", "risk": "critical", "evidence": "Section 4.2: 'Staff must wash hands before any invasive procedure…'", "citation": "WHO IPC Guidelines 2022, Section 2.3: The Five Moments for Hand Hygiene", "corrective_action": "Update Section 4.2 to include all 5 WHO moments. Schedule refresher training within 30 days.", "category": "Infection Control"},
            {"regulation_id": "CDC-NHSN-4.1", "title": "CLABSI Prevention Incomplete", "description": "Central-line insertion checklist missing maximal barrier precautions and chlorhexidine skin antisepsis.", "risk": "high", "evidence": "Appendix B Checklist: sterile gloves ✓, sterile gown ✓ — chlorhexidine prep: missing.", "citation": "CDC NHSN CLABSI Protocol 2023, Section 4.1.2", "corrective_action": "Revise Appendix B to include full CDC NHSN insertion bundle.", "category": "HAI Prevention"},
            {"regulation_id": "HHS-HAP-7.2", "title": "Ventilator Bundle Non-Compliance", "description": "VAP prevention bundle missing oral care with chlorhexidine every 6 hours.", "risk": "high", "evidence": "Section 7.1 VAP Bundle: Head-of-bed elevation ✓, Daily sedation ✓ — Oral care: NOT LISTED.", "citation": "HHS HAP Prevention Guideline, Section 7.2", "corrective_action": "Add oral care protocol. Source chlorhexidine 0.12% oral rinse. Train ICU nursing.", "category": "Critical Care"},
            {"regulation_id": "OSHA-BBP-1910.1030", "title": "PEP Timeline Non-Compliant", "description": "Post-exposure prophylaxis window listed as 4 hours; OSHA mandates 2 hours.", "risk": "medium", "evidence": "Section 9.3: '…report to occupational health within 4 hours for PEP evaluation.'", "citation": "OSHA 29 CFR 1910.1030 Bloodborne Pathogens Standard, Appendix B", "corrective_action": "Amend Section 9.3 to reflect 2-hour window. Update signage.", "category": "Occupational Safety"},
            {"regulation_id": "TJC-IC.02.02.01", "title": "Isolation Precaution Signage", "description": "Policy lacks specification of signage types per transmission-based precaution category.", "risk": "medium", "evidence": "Section 6.1: 'Isolation rooms will be clearly marked.' No further specification.", "citation": "The Joint Commission IC.02.02.01, EP 4", "corrective_action": "Develop distinct signage templates for contact, droplet, and airborne precautions.", "category": "Isolation Precautions"},
            {"regulation_id": "CDC-MDRO-3.5", "title": "MRSA Screening Frequency", "description": "MRSA screening listed as optional for low-risk patients; CDC mandates universal ICU screening.", "risk": "low", "evidence": "Section 3.2: 'MRSA screening is recommended for high-risk patients as defined by clinician assessment.'", "citation": "CDC MDRO Management Guideline 2023, Section 3.5", "corrective_action": "Update ICU admission protocol to mandatory universal MRSA screening.", "category": "MDRO Control"},
        ],
        "citations": ["WHO IPC Guidelines 2022", "CDC NHSN Protocol 2023", "HHS HAP Prevention Guideline", "OSHA 29 CFR 1910.1030", "The Joint Commission IC.02.02.01", "CDC MDRO Management Guideline 2023"],
        "recommendations_summary": "1. Immediately update hand hygiene protocol to WHO 5 Moments. 2. Revise CLABSI insertion checklist to full CDC bundle. 3. Add chlorhexidine oral care to VAP prevention bundle.",
        "processing_time_ms": 3800,
        "llm_model": "mock-dev-mode",
        "embedding_model": settings.EMBEDDING_MODEL,
        "chunks_retrieved": 20,
        "chunks_reranked": 8,
    }
