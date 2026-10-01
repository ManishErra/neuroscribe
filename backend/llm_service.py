import json
import os
import logging

from groq import Groq

from clinical_entities import extract_clinical_entities
from clinical_extractors import (
    extract_glucose,
    extract_hemoglobin,
)
from clinical_flags import classify_lab_result
from query_intents import QueryIntent, detect_query_intent, has_medication_evidence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq client — reads GROQ_API_KEY from environment.
# Falls back gracefully if the key is absent (RAG still returns deterministic
# answers; only free-text fallback is affected).
# ---------------------------------------------------------------------------

_groq_client: Groq | None = None


def _get_groq_client() -> Groq | None:
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        logger.warning(
            "GROQ_API_KEY is not set — free-text LLM fallback is disabled. "
            "Deterministic clinical extraction will still work."
        )
        return None
    try:
        _groq_client = Groq(api_key=api_key)
        return _groq_client
    except Exception as exc:
        logger.error("Failed to initialise Groq client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Model selection — can be overridden via env var for flexibility.
# Default to a currently configured production model; Railway can override
# this with GROQ_MODEL. Older deprecated IDs are remapped for compatibility.
# See: https://console.groq.com/docs/models

GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-20b").strip()
if GROQ_LLM_MODEL in {"llama-3.3-70b-versatile", "llama-3.1-8b-instant"}:
    GROQ_LLM_MODEL = "openai/gpt-oss-20b"


def _get_max_completion_tokens() -> int:
    val = os.getenv("GROQ_MAX_COMPLETION_TOKENS", "1024").strip()
    try:
        parsed = int(val)
        return parsed if parsed > 0 else 1024
    except (ValueError, TypeError):
        return 1024


GROQ_MAX_COMPLETION_TOKENS = _get_max_completion_tokens()


def _try_structured_extraction(
    context: str,
    question: str,
) -> str | None:
    """
    Deterministic extractor pipeline
    using regex-based extractors.
    """

    q = question.lower()

    # Hemoglobin
    if "hemoglobin" in q or "hb" in q:

        value = extract_hemoglobin(context)

        if value:

            print(f"[DEBUG] _try_structured_extraction: Extracted Hemoglobin = '{value}'")
            result = classify_lab_result(
                "hemoglobin",
                value,
            )

            return json.dumps(
                result,
                indent=2,
            )

    # Glucose
    if "glucose" in q or "sugar" in q:

        value = extract_glucose(context)

        if value:

            print(f"[DEBUG] _try_structured_extraction: Extracted Glucose = '{value}'")
            result = classify_lab_result(
                "glucose",
                value,
            )

            return json.dumps(
                result,
                indent=2,
            )

    return None


def try_structured_entity_answer(
    context: str,
    question: str,
) -> str | None:
    """
    Structured entity extraction
    using deterministic NLP parsing.
    """

    entities = extract_clinical_entities(context)

    question_lower = question.lower()

    entity_keywords = {
        "glucose": ["glucose", "sugar"],
        "platelets": ["platelet", "platelets"],
        "wbc": ["wbc", "white blood"],
        "rbc": ["rbc", "red blood"],
        "creatinine": ["creatinine"],
        "bilirubin": ["bilirubin"],
        "sodium": ["sodium"],
        "potassium": ["potassium"],
        "hemoglobin": ["hemoglobin", "hb"],
    }

    requested_entities = []

    for entity_name, keywords in entity_keywords.items():

        if any(
            keyword in question_lower
            for keyword in keywords
        ):

            if entity_name in entities:

                value = entities[entity_name]

                print(f"[DEBUG] try_structured_entity_answer: Extracted {entity_name} = '{value}'")
                result = classify_lab_result(
                    entity_name,
                    value,
                )

                requested_entities.append(
                    json.dumps(
                        result,
                        indent=2,
                    )
                )

    if requested_entities:
        return "\n\n".join(requested_entities)

    return None


def _validate_evidence(context: str, question: str, intent: QueryIntent | None = None) -> bool:
    """
    Intent-aware evidence validation layer.
    Verifies that the retrieved context contains valid indicators for clinical
    concepts without requiring natural-language question phrasing to appear
    literally in the source text.
    """
    if not context or not context.strip():
        return False

    if intent is None:
        intent = detect_query_intent(question)

    # Treatment/recommendation questions are safely rejected directly
    if intent == QueryIntent.MEDICATION_RECOMMENDATION:
        return True

    # For medication queries, evidence MUST contain either documented medication
    # information or an explicit statement that there are no active medications.
    if intent in (QueryIntent.ACTIVE_MEDICATIONS, QueryIntent.MEDICATION_HISTORY):
        return has_medication_evidence(context)

    # High-level overview, consultation, and statement queries are satisfied
    # by the presence of authentic patient-scoped records in the context.
    if intent in (
        QueryIntent.PATIENT_OVERVIEW,
        QueryIntent.LAST_CONSULTATION,
        QueryIntent.PATIENT_STATEMENTS,
        QueryIntent.RECENT_HISTORY,
    ):
        if "[Source:" in context or len(context.strip()) > 30:
            return True

    q_lower = question.lower()
    ctx_lower = context.lower()

    # Define common clinical concept triggers and their valid evidence terms
    clinical_triggers = {
        ("blood pressure", "bp"): ["pressure", "bp", "mmHg"],
        ("pulse", "heart rate", "hr", "pulse rate"): ["pulse", "hr", "heart rate", "beats", "bpm"],
        ("temperature", "temp"): ["temp", "fever", "celsius", "fahrenheit", "body temperature", "temp."],
        ("oxygen saturation", "spo2", "sat", "oxygen"): ["spo2", "saturation", "oxygen sat"],
        ("medication", "medications", "meds", "drug", "drugs"): ["medication", "medications", "meds", "prescribed", "therapy", "mg", "tablet", "cap", "capsule", "treatment", "dose", "none", "no medication"],
        ("diagnosis", "diagnoses", "condition", "illness", "disorder"): ["diagnosis", "diagnoses", "diagnosed", "history", "condition", "illness", "disorder", "syndrome", "ref."],
        ("hemoglobin", "haemoglobin", "hgb", "hb"): ["hemoglobin", "haemoglobin", "hgb", "hb", "g/dl"],
        ("glucose", "sugar", "blood sugar", "hba1c"): ["glucose", "sugar", "mg/dl", "mmol/l", "hba1c"],
        ("platelet", "platelets", "plt"): ["platelet", "platelets", "plt", "10^3", "/ul"],
        ("wbc", "white blood", "white blood cells"): ["wbc", "white blood", "leukocyte", "10^3"],
        ("rbc", "red blood", "red blood cells"): ["rbc", "red blood", "erythrocyte", "10^6"],
        ("creatinine", "creat"): ["creatinine", "creat", "mg/dl", "umol/l"],
        ("sodium", "na"): ["sodium", "na", "mmol/l", "meq/l"],
        ("potassium", "k"): ["potassium", "k", "mmol/l", "meq/l"],
        ("bilirubin",): ["bilirubin", "mg/dl", "umol/l"],
    }

    # First check: If a critical clinical concept is requested, verify we have corresponding evidence terms
    for trigger_keys, evidence_terms in clinical_triggers.items():
        if any(key in q_lower for key in trigger_keys):
            if not any(term in ctx_lower for term in evidence_terms):
                return False

    # Second check: General non-stopword keyword check
    import re
    cleaned_q = re.sub(r"[^\w\s]", "", q_lower)
    words = cleaned_q.split()

    stop_words = {
        "what", "is", "the", "patients", "patient", "level", "value", "count", "show", "me",
        "are", "there", "any", "for", "to", "in", "of", "about", "describe", "detail",
        "details", "info", "information", "a", "an", "does", "do", "has", "have", "had", "give",
        "tell", "retrieve", "search", "find", "check", "verify", "confirm", "rate", "level",
        "levels", "measurement", "measurements", "test", "tests", "result", "results",
        "current", "history", "was", "were", "who", "when", "where", "how", "why", "say", "said",
        "mention", "mentioned", "report", "reported", "during", "session", "sessions", "consultation",
        "consultations", "last", "latest", "recent", "complaint", "complaints", "know", "overview",
        "summary", "summarize", "take", "taking", "prescribe", "prescribed"
    }

    key_terms = [w for w in words if w not in stop_words and len(w) > 2]
    high_freq_filter = {"blood", "cell", "cells", "report", "reports", "patient", "patients"}
    filtered_key_terms = [t for t in key_terms if t not in high_freq_filter]

    if filtered_key_terms:
        if not any(term in ctx_lower for term in filtered_key_terms):
            return False

    return True


def _call_groq_llm(
    context: str,
    question: str,
    intent: QueryIntent | None = None,
) -> str:
    """
    Call Groq API with the clinical QA prompt.
    Preserves strict clinical boundaries and hallucination prevention.
    Returns a string answer or raises an exception.
    """
    client = _get_groq_client()
    if client is None:
        return "LLM service unavailable — GROQ_API_KEY not configured."

    prompt = f"""
You are a clinical AI assistant.

Answer ONLY using the provided clinical record context.

RULES:
- Do NOT invent information.
- Do NOT use outside medical knowledge.
- If the answer is not supported by the provided context, say exactly:
  "Not found in available records."
- Do not assume the context is a laboratory report; it may be a report, consultation transcript, doctor note, AI note, or patient record.
- If asked for treatment recommendations, prescriptions, or what medications a patient should take, state that NeuroScribe only reports documented clinical information and does not recommend treatment or prescribe medications.
- For medication queries:
  * If records document active/current medications, list only the documented medications.
  * If records explicitly state that the patient takes no medication (e.g. 'none' or 'no current medications'), state that no active medications are documented in the records.
  * If no medication information is present in the records, say "Not found in available records." Never guess, infer, or recommend any medication.
- Keep answers short and clinically precise.

CLINICAL RECORD CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    if intent is None:
        intent = detect_query_intent(question)

    intent_str = intent.value if hasattr(intent, "value") else str(intent)

    try:
        response = client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.1,
            max_completion_tokens=_get_max_completion_tokens(),
        )

        choice = response.choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        raw_content = choice.message.content
        content = raw_content.strip() if raw_content else ""

        usage = getattr(response, "usage", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = getattr(details, "reasoning_tokens", None)

        is_empty = not content

        logger.info(
            "Groq LLM response received | model=%s intent=%s finish_reason=%s "
            "prompt_chars=%d context_chars=%d completion_tokens=%s reasoning_tokens=%s is_content_empty=%s",
            GROQ_LLM_MODEL,
            intent_str,
            finish_reason,
            len(prompt),
            len(context),
            completion_tokens,
            reasoning_tokens,
            is_empty,
        )

        if is_empty:
            if finish_reason == "length":
                raise RuntimeError(
                    f"LLM generation failed: response truncated due to context/token length limit "
                    f"(finish_reason='length', completion_tokens={completion_tokens})."
                )
            raise RuntimeError(
                f"LLM generation failed: empty response received from model (finish_reason='{finish_reason}')."
            )

        return content

    except RuntimeError:
        raise
    except Exception as exc:
        logger.error(
            "Groq LLM call failed | model=%s intent=%s error_type=%s: %s",
            GROQ_LLM_MODEL,
            intent_str,
            type(exc).__name__,
            exc,
        )
        raise RuntimeError(f"LLM generation failed: {exc}") from exc


def generate_answer(
    context: str,
    question: str,
) -> str:
    """
    NeuroScribe Clinical QA Pipeline

    Steps:
    0. Intent safety guard (e.g. medication/treatment recommendation refusal)
    1. Regex deterministic extraction (hemoglobin, glucose)
    2. Entity extraction (deterministic NLP parsing)
    3. Hallucination prevention & evidence validation
    4. Groq LLM fallback
    """
    intent = detect_query_intent(question)

    # STEP 0 — Treatment/prescribing recommendation safety guard
    if intent == QueryIntent.MEDICATION_RECOMMENDATION:
        return "NeuroScribe only reports documented clinical information and does not recommend treatment or prescribe medications."

    # STEP 1 — regex extraction
    structured_answer = _try_structured_extraction(
        context,
        question,
    )

    if structured_answer:
        return structured_answer

    # STEP 2 — entity extraction
    entity_answer = try_structured_entity_answer(
        context,
        question,
    )

    if entity_answer:
        return entity_answer

    # STEP 3 — evidence validation
    if not _validate_evidence(context, question, intent):
        return "Not found in available records."

    # STEP 4 — Groq LLM fallback
    return _call_groq_llm(context, question, intent=intent)

