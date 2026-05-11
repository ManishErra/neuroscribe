import re

SYSTEM_PROMPT = """
You are a medical documentation assistant for psychiatrists.

STRICT RULES:
- NEVER diagnose. NEVER write disorder names as conclusions.
- NEVER assess suicide risk or write risk levels.
- NEVER recommend medication changes.
- ONLY summarize what was actually said in the transcript.
- If content is unclear or sensitive, put it in flags_for_review.
- Output ONLY valid JSON. No preamble. No markdown code blocks.
"""

def build_user_prompt(
    transcript: str,
    patient_name: str,
    patient_age: int
) -> str:

    return f"""
Patient: {patient_name}, Age: {patient_age}

TRANSCRIPT:
{transcript}

Generate this exact JSON structure:
{{
  "presenting_complaint": "main issue patient described today",
  "symptoms_mentioned": ["symptom 1", "symptom 2"],
  "medications_mentioned": ["name and dose if stated, else empty"],
  "sleep": "what patient said about sleep",
  "mood_in_patient_words": "patient's own words about mood",
  "social_context": "family or life situation mentioned",
  "plan_discussed": "what doctor mentioned for next steps",
  "flags_for_review": "unclear, sensitive, or important items doctor must verify",
  "confidence": "high or medium or low"
}}
"""


# Safety filter — run on ALL LLM outputs before display
BLOCKED_PHRASES = [
    "diagnosis of",
    "patient has",
    "confirms diagnosis",
    "schizophrenia",
    "bipolar disorder",
    "depressive disorder",
    "PTSD",
    "suicidal",
    "risk level",
    "high risk",
    "low risk",
    "borderline personality"
]


def safety_filter(text: str) -> tuple[str, list]:

    flagged = []

    for phrase in BLOCKED_PHRASES:

        if phrase.lower() in text.lower():

            flagged.append(phrase)

            # Case-insensitive replacement
            text = re.sub(
                phrase,
                "[FLAGGED FOR REVIEW]",
                text,
                flags=re.IGNORECASE
            )

    return text, flagged