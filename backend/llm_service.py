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
# Default: llama-3.3-70b-versatile (confirmed active on Groq, Aug 2026)
# Alternatives: qwen/qwen3.6-27b, qwen/qwen3.8-27b, llama-3.1-8b-instant
# See: https://console.groq.com/docs/models

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


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


def _validate_evidence(context: str, question: str) -> bool:
    """
    Generalized evidence validation layer.
    Verifies that the retrieved context contains matching indicators 
    for critical clinical concepts present in the user question.
    """
    q_lower = question.lower()
    ctx_lower = context.lower()

    # Define common clinical concept triggers and their valid evidence terms
    clinical_triggers = {
        ("blood pressure", "bp"): ["pressure", "bp", "mmHg"],
        ("pulse", "heart rate", "hr", "pulse rate"): ["pulse", "hr", "heart rate", "beats", "bpm"],
        ("temperature", "temp"): ["temp", "fever", "celsius", "fahrenheit", "body temperature", "temp."],
        ("oxygen saturation", "spo2", "sat", "oxygen"): ["spo2", "saturation", "oxygen sat"],
        ("medication", "medications", "meds", "drug", "drugs"): ["medication", "medications", "meds", "prescribed", "therapy", "mg", "tablet", "cap", "capsule", "treatment", "dose"],
        ("diagnosis", "diagnoses", "condition", "illness", "disorder"): ["diagnosis", "diagnoses", "diagnosed", "history", "condition", "illness", "disorder", "syndrome", "ref."]
    }

    # First check: If a critical concept is requested, verify we have corresponding evidence terms
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
        "details", "info", "information", "a", "an", "does", "do", "has", "have", "give", 
        "tell", "retrieve", "search", "find", "check", "verify", "confirm", "rate", "level",
        "levels", "measurement", "measurements", "test", "tests", "result", "results",
        "current", "history", "was", "were", "who", "when", "where", "how", "why"
    }

    key_terms = [w for w in words if w not in stop_words and len(w) > 2]
    high_freq_filter = {"blood", "cell", "cells", "report", "reports"}
    filtered_key_terms = [t for t in key_terms if t not in high_freq_filter]

    if filtered_key_terms:
        if not any(term in ctx_lower for term in filtered_key_terms):
            return False

    return True


def _call_groq_llm(context: str, question: str) -> str:
    """
    Call Groq API with the clinical QA prompt.
    Preserves the original prompt structure verbatim.
    Returns a string answer or raises an exception.
    """
    client = _get_groq_client()
    if client is None:
        return "LLM service unavailable — GROQ_API_KEY not configured."

    prompt = f"""
You are a clinical AI assistant.

Answer ONLY using the provided report context.

RULES:
- Do NOT invent information.
- Do NOT use outside medical knowledge.
- If answer is missing, say:
  "The report does not contain this information."
- Keep answers short and clinically precise.

REPORT CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.1,
            max_tokens=200,
        )
        return response.choices[0].message.content or "No response from LLM."
    except Exception as exc:
        logger.error("Groq LLM call failed: %s", exc)
        raise RuntimeError(f"LLM generation failed: {exc}") from exc


def generate_answer(
    context: str,
    question: str,
) -> str:
    """
    NeuroScribe Clinical QA Pipeline

    Steps:
    1. Regex deterministic extraction
    2. Entity extraction
    3. Hallucination prevention
    3.5 Generalized evidence validation guard
    4. Groq LLM fallback
    """

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

    # STEP 3 — hallucination prevention
    structured_keywords = [
        "hemoglobin",
        "glucose",
        "platelet",
        "platelets",
        "wbc",
        "rbc",
        "creatinine",
        "bilirubin",
        "sodium",
        "potassium",
    ]

    question_lower = question.lower()

    for keyword in structured_keywords:

        if keyword in question_lower:

            return (
                "The report does not contain "
                "this information."
            )

    # STEP 3.5 — generalized evidence validation guard
    if not _validate_evidence(context, question):
        return "The report does not contain sufficient information to answer this question."

    # STEP 4 — Groq LLM fallback
    return _call_groq_llm(context, question)