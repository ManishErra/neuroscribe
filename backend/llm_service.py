from ollama import chat

from clinical_extractors import (
    extract_glucose,
    extract_hemoglobin,
)


def _try_structured_extraction(
    context: str,
    question: str,
) -> str | None:
    """
    Attempt deterministic medical extraction before LLM generation.
    """

    q = question.lower()

    if "hemoglobin" in q or "hb" in q:

        value = extract_hemoglobin(context)

        if value:
            return f"Hemoglobin level: {value}"

    if "glucose" in q or "sugar" in q:

        value = extract_glucose(context)

        if value:
            return f"Glucose level: {value}"

    return None


def generate_answer(
    context: str,
    question: str,
) -> str:
    """
    Generate medical answer with:
    1. Deterministic extraction
    2. Safe hallucination prevention
    3. LLM fallback only for non-structured questions
    """

    # STEP 1 — structured extraction
    structured_answer = _try_structured_extraction(
        context,
        question,
    )

    if structured_answer:
        return structured_answer

    # STEP 2 — prevent hallucinations
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

    # STEP 3 — LLM fallback only for general questions
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