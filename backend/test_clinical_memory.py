import json

from clinical_memory import _chunk_text, _score_text
from llm_service import generate_answer


def test_clinical_memory_chunking_and_query_scoring():
    text = (
        "Patient reports difficulty sleeping and feeling anxious after work. "
        "Sleep is reduced to four hours nightly."
    )
    chunks = _chunk_text(text, size=20, overlap=4)
    assert chunks
    assert _score_text(chunks[0], "What did the patient say about sleep?") > 0


def test_llm_uses_context_when_lab_extractor_misses(monkeypatch):
    # Hb is deliberately formatted in a way that can bypass the deterministic
    # extractor. The evidence still contains the requested clinical concept.
    context = "Hemoglobin result was documented as Hb 13.7 g/dL on the report."
    captured = {}

    def fake_call(context_arg, question_arg):
        captured["context"] = context_arg
        captured["question"] = question_arg
        return "The hemoglobin reading was 13.7 g/dL."

    monkeypatch.setattr("llm_service._call_groq_llm", fake_call)
    monkeypatch.setattr("llm_service._try_structured_extraction", lambda *_args: None)
    monkeypatch.setattr("llm_service.try_structured_entity_answer", lambda *_args: None)

    answer = generate_answer(context, "What was the latest hemoglobin reading?")
    assert answer == "The hemoglobin reading was 13.7 g/dL."
    assert "13.7" in captured["context"]


def test_llm_returns_not_found_without_evidence():
    # This path must not call the LLM when there is no supporting evidence.
    answer = generate_answer(
        "The report contains sodium 140 mmol/L.",
        "What was the hemoglobin reading?",
    )
    assert answer == "Not found in available records."
