import re


def normalize_newlines(text: str) -> str:
    """
    Reduce excessive newlines.
    """
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def normalize_spaces(text: str) -> str:
    """
    Remove excessive spaces and tabs.
    """
    text = re.sub(r"[ \t]+", " ", text)
    return text


def remove_ocr_artifacts(text: str) -> str:
    """
    Remove common OCR garbage artifacts.
    """
    text = text.replace("\x0c", "")
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬂ", "fl")
    return text


def clean_ocr_text(text: str) -> str:
    """
    Full OCR cleaning pipeline.
    """

    if not text:
        return ""

    text = remove_ocr_artifacts(text)

    text = normalize_spaces(text)

    text = normalize_newlines(text)

    text = text.strip()

    return text