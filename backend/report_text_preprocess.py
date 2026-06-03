"""
Text normalization for report chunking and embedding.

Prepares OCR report text and query strings so embeddings focus on clinical
content rather than layout noise.
"""

from __future__ import annotations

import re
from typing import Final

MIN_EMBED_CHUNK_CHARS: Final[int] = 60

_WHITESPACE = re.compile(r"\s+")
_REPEATED_CHAR = re.compile(r"(.)\1{4,}")
_OCR_PIPE_NOISE = re.compile(r"\|{2,}")
_OCR_DASH_NOISE = re.compile(r"[-_=]{5,}")
_OCR_GARBAGE_LINE = re.compile(r"^[^\w\s]{4,}$", re.MULTILINE)

_MEDICAL_ABBREVIATIONS = {
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "wbc": "white blood cell",
    "rbc": "red blood cell",
    "plt": "platelet",
    "bp": "blood pressure",
    "hr": "heart rate",
}


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace and strip line edges."""
    lines = [line.strip() for line in text.splitlines()]
    joined = "\n".join(line for line in lines if line)
    return _WHITESPACE.sub(" ", joined).strip()


def remove_ocr_artifacts(text: str) -> str:
    """Remove common OCR repetition and separator noise."""
    cleaned = text.replace("\x0c", " ")
    cleaned = _REPEATED_CHAR.sub(r"\1\1", cleaned)
    cleaned = _OCR_PIPE_NOISE.sub(" ", cleaned)
    cleaned = _OCR_DASH_NOISE.sub(" ", cleaned)
    cleaned = _OCR_GARBAGE_LINE.sub("", cleaned)
    return normalize_whitespace(cleaned)


def normalize_medical_terms(text: str) -> str:
    """
    Normalize common medical abbreviations for better semantic retrieval.
    Preserves lab values and units while improving embedding consistency.
    """

    normalized = text

    for abbreviation, full_term in _MEDICAL_ABBREVIATIONS.items():
        pattern = rf"\b{re.escape(abbreviation)}\b"

        normalized = re.sub(
            pattern,
            full_term,
            normalized,
            flags=re.IGNORECASE,
        )

    normalized = re.sub(r"\s*:\s*", ": ", normalized)

    return normalized


def prepare_text_for_embedding(text: str) -> str:
    """
    Full preprocessing pipeline used before embedding chunks or queries.

    Returns lowercased, normalized text.
    Empty string if nothing usable remains.
    """

    if not text or not text.strip():
        return ""

    cleaned = remove_ocr_artifacts(text)

    if not cleaned:
        return ""

    normalized = normalize_medical_terms(cleaned)

    return normalized.lower()


def is_embeddable_chunk(
    text: str,
    min_chars: int = MIN_EMBED_CHUNK_CHARS,
) -> bool:
    """Return True when a chunk has enough content to embed meaningfully."""

    prepared = prepare_text_for_embedding(text)

    return len(prepared) >= min_chars