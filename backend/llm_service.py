import json

from ollama import chat

from clinical_entities import extract_clinical_entities

from clinical_extractors import (
    extract_glucose,
    extract_hemoglobin,
)

from clinical_flags import classify_lab_result


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
    4. LLM fallback
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

    # STEP 4 — LLM fallback

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

    response = chat(
        model="tinyllama",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": 0.1,
            "num_predict": 120,
        },
    )

    return response.message.content