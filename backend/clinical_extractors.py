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


def extract_glucose(
    text: str,
) -> Optional[str]:
    """
    Extract glucose value.
    """

    for pattern in GLUCOSE_PATTERNS:

        match = pattern.search(text)

        if not match:
            continue

        value = (
            match.group(2)
            if len(match.groups()) >= 2
            else match.group(1)
        )

        try:

            numeric = float(value)

            # realistic glucose range
            if 20 <= numeric <= 600:
                return value

        except ValueError:
            continue

    return None