import json
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import clinical_memory
# Mock vector search in tests so tests are completely offline and fast
clinical_memory.search_similar_chunks = lambda **kwargs: []

from clinical_memory import _chunk_text, _score_text, retrieve_patient_context
from llm_service import generate_answer, _validate_evidence
from models import Note, Patient, Report, Session as SessionModel, Transcript
from query_intents import QueryIntent, detect_query_intent


class MockQuery:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, *conditions):
        filtered = self.items
        for cond in conditions:
            left_col = getattr(cond.left, "key", str(cond.left))
            op = getattr(cond.operator, "__name__", str(cond.operator))
            right_val = getattr(cond.right, "value", cond.right)

            if op == "eq":
                filtered = [x for x in filtered if getattr(x, left_col, None) == right_val]
            elif op == "in_op":
                val_list = [v.value if hasattr(v, "value") else v for v in right_val]
                filtered = [x for x in filtered if getattr(x, left_col, None) in val_list]
            elif op == "is_not":
                filtered = [x for x in filtered if getattr(x, left_col, None) is not None]
        return MockQuery(filtered)

    def order_by(self, *args):
        return self

    def limit(self, n):
        return MockQuery(self.items[:n])

    def all(self):
        return list(self.items)

    def first(self):
        return self.items[0] if self.items else None


class MockDB:
    def __init__(self, patients=None, sessions=None, transcripts=None, notes=None, reports=None):
        self.patients = patients or []
        self.sessions = sessions or []
        self.transcripts = transcripts or []
        self.notes = notes or []
        self.reports = reports or []

    def query(self, model):
        if model == Patient:
            return MockQuery(self.patients)
        elif model == SessionModel:
            return MockQuery(self.sessions)
        elif model == Transcript:
            return MockQuery(self.transcripts)
        elif model == Note:
            return MockQuery(self.notes)
        elif model == Report:
            return MockQuery(self.reports)
        return MockQuery([])


def create_test_fixtures():
    patient_a_id = "patient-aaa-111"
    patient_b_id = "patient-bbb-222"
    patient_c_id = "patient-ccc-333"  # Explicitly no medications
    patient_d_id = "patient-ddd-444"  # No medication info at all (only lab report)
    owner_id = "doctor-owner-999"

    patient_a = Patient(
        id=patient_a_id,
        name="Eleanor Vance",
        age=42,
        gender="Female",
        owner_id=owner_id,
    )
    patient_b = Patient(
        id=patient_b_id,
        name="Arthur Dent",
        age=30,
        gender="Male",
        owner_id=owner_id,
    )
    patient_c = Patient(
        id=patient_c_id,
        name="Clara Oswald",
        age=28,
        gender="Female",
        owner_id=owner_id,
    )
    patient_d = Patient(
        id=patient_d_id,
        name="David Noble",
        age=55,
        gender="Male",
        owner_id=owner_id,
    )

    # Patient A (Documented active medications)
    session_a = SessionModel(
        id="session-aaa-1",
        patient_id=patient_a_id,
        session_date=date(2026, 9, 30),
        created_at=datetime(2026, 9, 30, 10, 0),
    )
    transcript_a = Transcript(
        id="transcript-aaa-1",
        session_id="session-aaa-1",
        raw_text="Doctor: How have you been feeling? Patient: I have had severe morning headaches for the past three weeks and intermittent dizziness after standing up.",
        created_at=datetime(2026, 9, 30, 10, 5),
    )
    note_a = Note(
        id="note-aaa-1",
        session_id="session-aaa-1",
        doctor_edited=json.dumps({
            "subjective": "Patient reports severe morning headaches and dizziness.",
            "objective": "BP 120/80 mmHg, alert and oriented.",
            "assessment": "Tension headaches vs migraine.",
            "plan": "Continue current regimen. Start Metformin 500mg daily and Lisinopril 10mg once daily. Follow up in two weeks.",
            "medications_mentioned": ["Metformin 500mg daily", "Lisinopril 10mg once daily"],
        }),
        is_finalized=True,
        created_at=datetime(2026, 9, 30, 10, 10),
    )
    report_a = Report(
        id="report-aaa-1",
        patient_id=patient_a_id,
        file_path="uploads/cbc_a.pdf",
        title="Complete Blood Count",
        original_filename="cbc_a.pdf",
        ocr_status="ready",
        ocr_text="LABORATORY REPORT: Hemoglobin: 14.2 g/dL. Platelets: 250000 /uL. WBC: 6.5 x10^3/uL.",
        report_date=date(2026, 9, 29),
        created_at=datetime(2026, 9, 29, 9, 0),
    )

    # Patient B (Knee pain session)
    session_b = SessionModel(
        id="session-bbb-1",
        patient_id=patient_b_id,
        session_date=date(2026, 9, 28),
        created_at=datetime(2026, 9, 28, 14, 0),
    )
    transcript_b = Transcript(
        id="transcript-bbb-1",
        session_id="session-bbb-1",
        raw_text="Patient B mentions chronic knee pain after marathon running.",
        created_at=datetime(2026, 9, 28, 14, 5),
    )

    # Patient C (Explicit "No current medications")
    session_c = SessionModel(
        id="session-ccc-1",
        patient_id=patient_c_id,
        session_date=date(2026, 9, 25),
        created_at=datetime(2026, 9, 25, 11, 0),
    )
    transcript_c = Transcript(
        id="transcript-ccc-1",
        session_id="session-ccc-1",
        raw_text="Doctor: Are you taking any prescription or over-the-counter medications? Patient: No current medications. I do not take any pills.",
        created_at=datetime(2026, 9, 25, 11, 5),
    )
    note_c = Note(
        id="note-ccc-1",
        session_id="session-ccc-1",
        doctor_edited=json.dumps({
            "subjective": "Annual wellness visit. Patient is active.",
            "medications_mentioned": ["None documented. No active medications."],
            "plan": "Maintain routine diet and exercise.",
        }),
        is_finalized=True,
        created_at=datetime(2026, 9, 25, 11, 10),
    )

    # Patient D (Only lab report, zero medication mentions)
    report_d = Report(
        id="report-ddd-1",
        patient_id=patient_d_id,
        file_path="uploads/glucose_d.pdf",
        title="Fasting Glucose",
        original_filename="glucose_d.pdf",
        ocr_status="ready",
        ocr_text="LABORATORY REPORT: Fasting Plasma Glucose: 98 mg/dL. HbA1c: 5.4%.",
        report_date=date(2026, 9, 20),
        created_at=datetime(2026, 9, 20, 8, 0),
    )

    db = MockDB(
        patients=[patient_a, patient_b, patient_c, patient_d],
        sessions=[session_a, session_b, session_c],
        transcripts=[transcript_a, transcript_b, transcript_c],
        notes=[note_a, note_c],
        reports=[report_a, report_d],
    )
    return db, patient_a_id, patient_b_id, patient_c_id, patient_d_id, owner_id


# =============================================================================
# TEST SUITE
# =============================================================================

def test_intent_detection():
    # Test intent classification on core user queries
    assert detect_query_intent("Summarize the last consultation") == QueryIntent.LAST_CONSULTATION
    assert detect_query_intent("what happened in the last consultation") == QueryIntent.LAST_CONSULTATION
    assert detect_query_intent("tell me about the last session") == QueryIntent.LAST_CONSULTATION
    assert detect_query_intent("summarize the recent consultation") == QueryIntent.LAST_CONSULTATION

    assert detect_query_intent("What did the patient say in the last consultation?") == QueryIntent.PATIENT_STATEMENTS
    assert detect_query_intent("What did the patient mention during the last session?") == QueryIntent.PATIENT_STATEMENTS
    assert detect_query_intent("What did the patient report during the consultation?") == QueryIntent.PATIENT_STATEMENTS
    assert detect_query_intent("what did the patient complain about") == QueryIntent.PATIENT_STATEMENTS
    assert detect_query_intent("what did the patient say during the session") == QueryIntent.PATIENT_STATEMENTS

    assert detect_query_intent("What are the active medications?") == QueryIntent.ACTIVE_MEDICATIONS
    assert detect_query_intent("What medications is the patient taking?") == QueryIntent.ACTIVE_MEDICATIONS
    assert detect_query_intent("Does the patient take any medication?") == QueryIntent.ACTIVE_MEDICATIONS
    assert detect_query_intent("what medicines is the patient currently on") == QueryIntent.ACTIVE_MEDICATIONS

    assert detect_query_intent("Tell me about the patient") == QueryIntent.PATIENT_OVERVIEW
    assert detect_query_intent("Give me the details of the patient") == QueryIntent.PATIENT_OVERVIEW
    assert detect_query_intent("What do we know about this patient?") == QueryIntent.PATIENT_OVERVIEW
    assert detect_query_intent("describe this patient") == QueryIntent.PATIENT_OVERVIEW

    assert detect_query_intent("Give me the patient's recent history") == QueryIntent.RECENT_HISTORY
    assert detect_query_intent("what has happened recently") == QueryIntent.RECENT_HISTORY
    assert detect_query_intent("give me a recent clinical summary") == QueryIntent.RECENT_HISTORY

    assert detect_query_intent("What medication should the patient take?") == QueryIntent.MEDICATION_RECOMMENDATION
    assert detect_query_intent("What should I prescribe for this condition?") == QueryIntent.MEDICATION_RECOMMENDATION


def test_test_a_summarize_last_consultation():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Summarize the last consultation", owner_id=owner_id)
    assert any(r["source_type"] == "transcript" for r in results)
    assert any("morning headaches" in r["chunk_text"] for r in results)


def test_test_b_patient_statements_last_consultation():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What did the patient say in the last consultation?", owner_id=owner_id)
    assert results[0]["source_type"] == "transcript"
    assert "morning headaches" in results[0]["chunk_text"]


def test_test_c_patient_mention_during_session():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What did the patient mention during the last session?", owner_id=owner_id)
    assert results[0]["source_type"] == "transcript"
    assert "dizziness" in results[0]["chunk_text"]


def test_test_d_active_medications_documented():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What are the active medications?", owner_id=owner_id)
    assert any("Metformin" in r["chunk_text"] for r in results)
    # Evidence validation passes because medication indicators exist in context
    context = "\n".join(r["chunk_text"] for r in results)
    assert _validate_evidence(context, "What are the active medications?")


def test_test_e_active_medications_explicit_no_medication():
    # Patient C has explicit "No current medications"
    db, _, _, patient_c_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_c_id, "Does the patient take any medication?", owner_id=owner_id)
    assert any("No current medications" in r["chunk_text"] or "No active medications" in r["chunk_text"] for r in results)
    context = "\n".join(r["chunk_text"] for r in results)
    # Evidence validation passes because explicit negative statement is present
    assert _validate_evidence(context, "Does the patient take any medication?")


def test_test_f_active_medications_absent_returns_not_found():
    # Patient D has only a fasting glucose report, zero medication mentions
    db, _, _, _, patient_d_id, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_d_id, "What are the active medications?", owner_id=owner_id)
    context = "\n".join(r["chunk_text"] for r in results) if results else ""
    # Evidence validation must fail because no medication or no-medication statement exists
    assert not _validate_evidence(context, "What are the active medications?")
    # generate_answer must return "Not found in available records." without guessing
    answer = generate_answer(context, "What are the active medications?")
    assert answer == "Not found in available records."


def test_test_g_patient_overview_balanced_sources():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Tell me about the patient", owner_id=owner_id)
    source_types = [r["source_type"] for r in results]
    assert "patient" in source_types
    assert "note" in source_types
    assert "transcript" in source_types
    assert "report" in source_types
    assert any("Eleanor Vance" in r["chunk_text"] for r in results)


def test_test_h_give_me_details_of_patient():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Give me the details of the patient", owner_id=owner_id)
    assert any(r["source_type"] == "patient" for r in results)


def test_test_i_what_do_we_know_about_patient():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What do we know about this patient?", owner_id=owner_id)
    assert any(r["source_type"] == "patient" for r in results)


def test_test_j_recent_history():
    db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Give me the patient's recent history", owner_id=owner_id)
    source_types = {r["source_type"] for r in results}
    assert "transcript" in source_types or "note" in source_types


def test_test_k_medication_recommendation_safety_refusal():
    # Never recommends treatment or prescribes medications
    answer = generate_answer("Context with Lisinopril", "What medication should the patient take?")
    assert "NeuroScribe only reports documented clinical information" in answer
    assert "does not recommend treatment" in answer


def test_test_l_unrelated_question_not_found():
    # Asking for MRI brain when only CBC exists
    context = "LABORATORY REPORT: Hemoglobin: 14.2 g/dL. Platelets: 250000 /uL."
    answer = generate_answer(context, "What were the results of the brain MRI scan?")
    assert answer == "Not found in available records."


def test_test_m_cross_patient_isolation():
    db, patient_a_id, patient_b_id, _, _, owner_id = create_test_fixtures()
    # Query for Patient A must NEVER return Patient B's records
    results_a = retrieve_patient_context(db, patient_a_id, "What did the patient say in the last consultation?", owner_id=owner_id)
    for r in results_a:
        assert r["patient_id"] == patient_a_id
        assert "knee pain" not in r["chunk_text"]
        assert "Arthur Dent" not in r["chunk_text"]

    # Query for Patient B must NEVER return Patient A's records
    results_b = retrieve_patient_context(db, patient_b_id, "Tell me about the patient", owner_id=owner_id)
    for r in results_b:
        assert r["patient_id"] == patient_b_id
        assert "Eleanor Vance" not in r["chunk_text"]
        assert "morning headaches" not in r["chunk_text"]


def _create_mock_groq_response(content: str | None, finish_reason: str = "stop", completion_tokens: int = 50, reasoning_tokens: int | None = None):
    mock_choice = MagicMock()
    mock_choice.finish_reason = finish_reason
    mock_choice.message.content = content

    mock_details = MagicMock()
    mock_details.reasoning_tokens = reasoning_tokens

    mock_usage = MagicMock()
    mock_usage.completion_tokens = completion_tokens
    mock_usage.completion_tokens_details = mock_details

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    return mock_response


def test_test_n_llm_response_normal_content():
    """Test A: Mock Groq client returns normal response content with 1024 token budget."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _create_mock_groq_response(
        content="Patient Eleanor Vance is a 32-year-old female presenting with morning headaches.",
        finish_reason="stop",
        completion_tokens=42,
    )

    context = "[Source: Patient profile]\nPatient name: Eleanor Vance; age: 32; gender: female."
    question = "Tell me about the patient and give me details of the patient"

    with patch("llm_service._get_groq_client", return_value=mock_client), \
         patch.dict("os.environ", {}, clear=False):
        # Remove any override to test default
        import os
        os.environ.pop("GROQ_MAX_COMPLETION_TOKENS", None)
        answer = generate_answer(context, question)
        assert answer == "Patient Eleanor Vance is a 32-year-old female presenting with morning headaches."
        assert mock_client.chat.completions.create.called
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 1024


def test_test_o_llm_response_empty_content_length_truncation():
    """Test B: Mock Groq client returns empty content + finish_reason='length'."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _create_mock_groq_response(
        content="",
        finish_reason="length",
        completion_tokens=1024,
        reasoning_tokens=1024,
    )

    context = "[Source: Patient profile]\nPatient name: Eleanor Vance; age: 32; gender: female."
    question = "Tell me about the patient and give me details of the patient"

    with patch("llm_service._get_groq_client", return_value=mock_client):
        try:
            generate_answer(context, question)
            assert False, "Expected RuntimeError due to length truncation"
        except RuntimeError as exc:
            assert "truncated due to context/token length limit" in str(exc)
            assert "finish_reason='length'" in str(exc)
            assert "Not found in available records." not in str(exc)


def test_test_p_llm_response_empty_content_other_finish_reason():
    """Test C: Mock Groq client returns empty content + finish_reason='stop'."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _create_mock_groq_response(
        content="",
        finish_reason="stop",
        completion_tokens=10,
    )

    context = "[Source: Patient profile]\nPatient name: Eleanor Vance; age: 32; gender: female."
    question = "Tell me about the patient and give me details of the patient"

    with patch("llm_service._get_groq_client", return_value=mock_client):
        try:
            generate_answer(context, question)
            assert False, "Expected RuntimeError due to empty response"
        except RuntimeError as exc:
            assert "empty response received from model" in str(exc)
            assert "finish_reason='stop'" in str(exc)
            assert "Not found in available records." not in str(exc)


def test_test_q_llm_response_not_found_missing_evidence():
    """Test D: Evidence validation fails and returns 'Not found in available records.' without LLM call."""
    mock_client = MagicMock()

    context = "[Source: Lab Report]\nHemoglobin: 14.2 g/dL. Platelets: 250000 /uL."
    question = "What were the results of the brain MRI scan?"

    with patch("llm_service._get_groq_client", return_value=mock_client):
        answer = generate_answer(context, question)
        assert answer == "Not found in available records."
        # Verify LLM was NOT called when evidence is missing
        assert not mock_client.chat.completions.create.called


def test_test_r_search_api_does_not_leak_runtime_error_details():
    """Test that search router catches LLM generation errors and raises HTTP 503 without leaking internal details."""
    from fastapi import HTTPException
    from routers.search import ask_question, AskRequest

    mock_db, patient_a_id, _, _, _, owner_id = create_test_fixtures()
    mock_user = MagicMock()
    mock_user.id = owner_id

    mock_request = MagicMock()
    mock_request.headers = {}

    ask_req = AskRequest(
        patient_id=patient_a_id,
        question="Tell me about the patient and give me details of the patient",
        top_k=5,
    )

    with patch("database.get_db", return_value=iter([mock_db])), \
         patch("rate_limiter.rag_limiter.check"), \
         patch("routers.search.generate_answer", side_effect=RuntimeError("LLM generation failed: response truncated due to context/token length limit (finish_reason='length', completion_tokens=1024).")):
        try:
            ask_question(ask_req, mock_request, current_user=mock_user)
            assert False, "Expected HTTPException with status 503"
        except HTTPException as exc:
            assert exc.status_code == 503
            assert exc.detail == "The clinical answer service is temporarily unavailable. Please retry."
            # Confirm no internal tokens or stack info is in detail
            assert "finish_reason" not in exc.detail
            assert "completion_tokens" not in exc.detail
            assert "RuntimeError" not in exc.detail
            assert "truncated" not in exc.detail


def test_test_s_groq_token_budget_env_configuration():
    """Test E: Groq token budget respects GROQ_MAX_COMPLETION_TOKENS environment variable."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _create_mock_groq_response(
        content="Overview response under custom token budget.",
        finish_reason="stop",
        completion_tokens=60,
    )

    context = "[Source: Patient profile]\nPatient name: Eleanor Vance; age: 32; gender: female."
    question = "Tell me about the patient and give me details of the patient"

    with patch("llm_service._get_groq_client", return_value=mock_client), \
         patch.dict("os.environ", {"GROQ_MAX_COMPLETION_TOKENS": "2048"}):
        answer = generate_answer(context, question)
        assert answer == "Overview response under custom token budget."
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 2048


if __name__ == "__main__":
    print("Running Ask NeuroScribe Query Intent & Retrieval Test Suite...")
    test_intent_detection()
    print("Test 1 (Intent Detection): PASSED")
    test_test_a_summarize_last_consultation()
    print("Test 2 (Summarize last consultation): PASSED")
    test_test_b_patient_statements_last_consultation()
    print("Test 3 (Patient statements): PASSED")
    test_test_c_patient_mention_during_session()
    print("Test 4 (Patient mention during session): PASSED")
    test_test_d_active_medications_documented()
    print("Test 5 (Active medications documented): PASSED")
    test_test_e_active_medications_explicit_no_medication()
    print("Test 6 (Active medications explicit no-medication statement): PASSED")
    test_test_f_active_medications_absent_returns_not_found()
    print("Test 7 (Active medications absent returns not found): PASSED")
    test_test_g_patient_overview_balanced_sources()
    print("Test 8 (Patient overview balanced sources): PASSED")
    test_test_h_give_me_details_of_patient()
    print("Test 9 (Give me details of patient): PASSED")
    test_test_i_what_do_we_know_about_patient()
    print("Test 10 (What do we know about patient): PASSED")
    test_test_j_recent_history()
    print("Test 11 (Recent history): PASSED")
    test_test_k_medication_recommendation_safety_refusal()
    print("Test 12 (Medication recommendation safety refusal): PASSED")
    test_test_l_unrelated_question_not_found()
    print("Test 13 (Unrelated question not found): PASSED")
    test_test_m_cross_patient_isolation()
    print("Test 14 (Cross-patient isolation): PASSED")
    test_test_n_llm_response_normal_content()
    print("Test 15 (LLM normal response content): PASSED")
    test_test_o_llm_response_empty_content_length_truncation()
    print("Test 16 (LLM empty content length truncation): PASSED")
    test_test_p_llm_response_empty_content_other_finish_reason()
    print("Test 17 (LLM empty content other finish reason): PASSED")
    test_test_q_llm_response_not_found_missing_evidence()
    print("Test 18 (Evidence missing returns Not found): PASSED")
    test_test_r_search_api_does_not_leak_runtime_error_details()
    print("Test 19 (Search API 503 error without leaking internal details): PASSED")
    test_test_s_groq_token_budget_env_configuration()
    print("Test 20 (Groq token budget configurable via env): PASSED")
    print("\nALL CLINICAL MEMORY INTENT & LLM ERROR-HANDLING TESTS PASSED SUCCESSFULLY (20/20)!")



