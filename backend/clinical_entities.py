import re
from typing import Dict, Optional


ENTITY_PATTERNS = {

    "hemoglobin": [
        r"\b(?:hemoglobin|haemoglobin|hgb|hb)\b(?!\s*[-_]?\s*(?:a1c|a2))(?:(?!a1c|a2|electrophoresis)[^\n]){0,50}?\b(\d+(?:\.\d+)?(?:\s*g/dl)?)\b(?!\s*%)",
    ],

    "glucose": [
        r"glucose[:\s]+([\d\.]+)",
        r"sugar[:\s]+([\d\.]+)",
        r"blood glucose[:\s]+([\d\.]+)",
    ],

    "platelets": [
        r"\b(?:platelets?|plt)\b.{0,100}?\b(\d+(?:[\d,]*\d)?)\b",
    ],

    "wbc": [
        r"\b(?:wbc|white blood cells?|white blood count)\b.{0,100}?\b(\d+(?:[\d,]*\d)?)\b",
    ],

    "rbc": [
        r"\b(?:rbc|red blood cells?|red blood count)\b.{0,100}?\b(\d+(?:\.\d+)?)\b",
    ],

    "creatinine": [
        r"creatinine[:\s]+([\d\.]+)",
    ],

    "bilirubin": [
        r"bilirubin[:\s]+([\d\.]+)",
    ],

}


def _search_patterns(
    text: str,
    patterns: list[str],
) -> Optional[str]:
    """
    Search multiple regex patterns and return first match.
    """

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


def extract_clinical_entities(
    text: str,
) -> Dict[str, str]:
    """
    Extract structured clinical entities from report text.
    """

    extracted: Dict[str, str] = {}

    if not text or not text.strip():
        return extracted

    normalized_text = text

    for entity_name, patterns in ENTITY_PATTERNS.items():

        value = _search_patterns(
            normalized_text,
            patterns,
        )

        if value:
            if entity_name == "hemoglobin":
                # Validate range to prevent matching arbitrary numbers like 120
                numeric_str = re.sub(r"[^\d.]", "", value)
                try:
                    numeric = float(numeric_str)
                    if not (5 <= numeric <= 20):
                        continue
                except ValueError:
                    continue
            extracted[entity_name] = value

    return extracted