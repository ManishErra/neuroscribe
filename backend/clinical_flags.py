import re


REFERENCE_RANGES = {
    "glucose": {
        "low": 70,
        "high": 110,
        "unit": "mg/dL",
    },
    "hemoglobin": {
        "low": 12,
        "high": 17,
        "unit": "g/dL",
    },
    "platelets": {
        "low": 150000,
        "high": 450000,
        "unit": "/cmm",
    },
    "wbc": {
        "low": 4000,
        "high": 11000,
        "unit": "/cmm",
    },
    "rbc": {
        "low": 4.5,
        "high": 5.9,
        "unit": "million/cmm",
    },
}


def _extract_numeric_value(value: str) -> float | None:
    """
    Extract numeric value from text.
    """

    match = re.search(r"[\d.]+", value)

    if not match:
        return None

    try:
        return float(match.group())

    except ValueError:
        return None


def classify_lab_result(
    test_name: str,
    value: str,
) -> dict:
    """
    Classify lab result using reference ranges.
    """

    test_key = test_name.lower()

    if test_key not in REFERENCE_RANGES:

        return {
            "test": test_name,
            "value": value,
            "status": "UNKNOWN",
        }

    config = REFERENCE_RANGES[test_key]

    numeric_value = _extract_numeric_value(value)

    if numeric_value is None:

        return {
            "test": test_name,
            "value": value,
            "status": "INVALID",
        }

    low = config["low"]
    high = config["high"]

    if numeric_value < low:
        status = "LOW"

    elif numeric_value > high:
        status = "HIGH"

    else:
        status = "NORMAL"

    return {
        "test": test_name,
        "value": value,
        "unit": config["unit"],
        "reference_range": f"{low}-{high}",
        "status": status,
    }