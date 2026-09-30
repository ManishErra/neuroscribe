import json
import os
import logging

from groq import Groq

from clinical_entities import extract_clinical_entities

from clinical_extractors import (
    extract_glucose,
    extract_hemoglobin,
)

from clinical_flags import classify_lab_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq client — reads GROQ_API_KEY from environment.
# Falls back gracefully if the key is absent (RAG still returns deterministic
# answers; only free-text fallback is affected).
# ---------------------------------------------------------------------------

_groq_client: Groq | None = None


def _get_groq_client() -> Groq | None:
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        logger.warning(
            "GROQ_API_KEY is not set — free-text LLM fallback is disabled. "
            "Deterministic clinical extraction will still work."
        )
        return None
    try:
        _groq_client = Groq(api_key=api_key)
        return _groq_client
    except Exception as exc:
        logger.error("Failed to initialise Groq client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Model selection — can be overridden via env var for flexibility.
# Use a currently configured production-safe default, while preserving
# compatibility with older/deprecated environment values.
# See: https://console.groq.com/docs/models
#
# Railway can override this with GROQ_MODEL without requiring a code change.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
if GROQ_MODEL in {"llama-3.3-70b-versatile", "llama-3.1-8b-instant"}:
    GROQ_MODEL = "openai/gpt-oss-20b"


def _try_structured_extraction(
    context: str,
    question: str,
) -> str | None:
    """
    Deterministic extractor pipeline
    using regex-based extractors.
    """

    q = question.lower()

    # Hemoglobin
    if "hemoglobin" in q or "hb" in q:

        value = extract_hemoglobin(context)

        if value:

            print(f"[DEBUG] _try_structured_extraction: Extracted Hemoglobin = '{value}'")
            result = classify_lab_result(
                "hemoglobin",
                value,
            )
