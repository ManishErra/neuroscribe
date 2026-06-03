import re
from typing import Optional


HEMOGLOBIN_PATTERNS = [

    re.compile(
        r"\b(?:hemoglobin|haemoglobin|hgb|hb)\b(?!\s*[-_]?\s*(?:a1c|a2))(?:(?!a1c|a2|electrophoresis)[^\n]){0,50}?\b(\d+(?:\.\d+)?(?:\s*g/dl)?)\b(?!\s*%)",
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

    # Reject known non-hemoglobin contexts line-by-line
    text_lines = text.splitlines()
    blocked_terms = [
        "hba1c",
        "a1c",
        "electrophoresis",
        "hb a2",
        "hb a ",
        "foetal hb",
        "fetal hb",
    ]

    for line in text_lines:
        line_lower = line.lower()
        if any(blocked in line_lower for blocked in blocked_terms):
            continue

        for pattern in HEMOGLOBIN_PATTERNS:

            match = pattern.search(line)

            if not match:
                continue

            value = match.group(1)

            if value is None:
                continue

            # Strip any units or spacing to parse float
            numeric_str = re.sub(r"[^\d.]", "", value)
            try:

                numeric = float(numeric_str)

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