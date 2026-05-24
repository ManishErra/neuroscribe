import re
from typing import Dict, Optional


ENTITY_PATTERNS = {

    "hemoglobin": [
        r"hemoglobin[:\s]+([\d\.-]+)",
        r"hb[:\s]+([\d\.-]+)",
        r"([\d\.]+-[\d\.]+\s?%)",
    ],

    "glucose": [
        r"glucose[:\s]+([\d\.]+)",
        r"sugar[:\s]+([\d\.]+)",
        r"blood glucose[:\s]+([\d\.]+)",
    ],

    "platelets": [
        r"platelets?[:\s]+([\d,]+)",
        r"platelet count[:\s]+([\d,]+)",
    ],

    "wbc": [
        r"wbc[:\s]+([\d,\.]+)",
        r"white blood cells?[:\s]+([\d,\.]+)",
    ],

    "rbc": [
        r"rbc[:\s]+([\d,\.]+)",
        r"red blood cells?[:\s]+([\d,\.]+)",
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

    normalized_text = text.lower()

    for entity_name, patterns in ENTITY_PATTERNS.items():

        value = _search_patterns(
            normalized_text,
            patterns,
        )

        if value:
            extracted[entity_name] = value

    return extracted