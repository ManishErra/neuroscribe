import re
from typing import Optional


HEMOGLOBIN_PATTERNS = [

    re.compile(
        r"(?:hemoglobin|haemoglobin|hgb)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    ),

]

GLUCOSE_PATTERNS = [

    re.compile(
        r"(glucose|sugar)[^\d]{0,15}(\d{2,3}(\.\d+)?)",
        re.IGNORECASE,
    ),
]


def extract_hemoglobin(
    text: str,
) -> Optional[str]:
    """
    Extract actual blood hemoglobin value only.
    Avoid HbA1c and Hb electrophoresis values.
    """

    text_lower = text.lower()

    # Reject known non-hemoglobin contexts
    blocked_terms = [
        "hba1c",
        "a1c",
        "electrophoresis",
        "hb a2",
        "hb a ",
        "foetal hb",
        "fetal hb",
    ]

    for blocked in blocked_terms:
        if blocked in text_lower:
            return None

    for pattern in HEMOGLOBIN_PATTERNS:

        match = pattern.search(text)

        if not match:
            continue

        value = match.group(1)

        if value is None:
            continue

        try:

            numeric = float(value)

            # realistic blood hemoglobin range
            if 5 <= numeric <= 20:
                return f"{numeric} g/dL"

        except ValueError:
            continue

    return None


import re


def extract_glucose(text: str) -> str | None:
    """
    Extract glucose / blood sugar values.
    """

    patterns = [

        # Standard glucose
        r"glucose[:\s]+([\d.]+\s*mg/dl)",

        # Blood sugar
        r"blood sugar[:\s]+([\d.]+\s*mg/dl)",

        # Mean blood glucose
        r"mean blood glucose.*?([\d.]+\s*mg/dl)",

        # HbA1c calculated glucose
        r"calculated.*?glucose.*?([\d.]+\s*mg/dl)",

    ]

    lower_text = text.lower()

    for pattern in patterns:

        match = re.search(
            pattern,
            lower_text,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1).upper()

    return None