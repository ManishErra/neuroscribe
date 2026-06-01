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