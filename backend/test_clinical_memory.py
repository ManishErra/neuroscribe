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

    # Patient B fixture
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

    db = MockDB(
        patients=[patient_a, patient_b],
        sessions=[session_a, session_b],
        transcripts=[transcript_a, transcript_b],
        notes=[note_a],
        reports=[report_a],
    )
    return db, patient_a_id, patient_b_id, owner_id


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
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Summarize the last consultation", owner_id=owner_id)
    assert any(r["source_type"] == "transcript" for r in results)
    assert any("morning headaches" in r["chunk_text"] for r in results)


def test_test_b_patient_statements_last_consultation():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What did the patient say in the last consultation?", owner_id=owner_id)
    # Transcript is the primary source
    assert results[0]["source_type"] == "transcript"
    assert "morning headaches" in results[0]["chunk_text"]


def test_test_c_patient_mention_during_session():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What did the patient mention during the last session?", owner_id=owner_id)
    assert results[0]["source_type"] == "transcript"
    assert "dizziness" in results[0]["chunk_text"]


def test_test_d_active_medications():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What are the active medications?", owner_id=owner_id)
    assert any("Metformin" in r["chunk_text"] for r in results)


def test_test_e_medications_currently_taking():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What medications is the patient currently taking?", owner_id=owner_id)
    assert any("Lisinopril" in r["chunk_text"] or "Metformin" in r["chunk_text"] for r in results)


def test_test_f_tell_me_about_the_patient():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Tell me about the patient", owner_id=owner_id)
    # Combines patient profile, note, transcript, report
    source_types = {r["source_type"] for r in results}
    assert "patient" in source_types
    assert any("Eleanor Vance" in r["chunk_text"] for r in results)


def test_test_g_give_me_details_of_patient():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Give me the details of the patient", owner_id=owner_id)
    assert any(r["source_type"] == "patient" for r in results)


def test_test_h_what_do_we_know_about_patient():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "What do we know about this patient?", owner_id=owner_id)
    assert any(r["source_type"] == "patient" for r in results)


def test_test_i_recent_history():
    db, patient_a_id, _, owner_id = create_test_fixtures()
    results = retrieve_patient_context(db, patient_a_id, "Give me the patient's recent history", owner_id=owner_id)
    source_types = {r["source_type"] for r in results}
    assert "transcript" in source_types or "note" in source_types


def test_test_j_medication_recommendation_safety_refusal():
    # Never recommends treatment or prescribes medications
    answer = generate_answer("Context with Lisinopril", "What medication should the patient take?")
    assert "NeuroScribe only reports documented clinical information" in answer
    assert "does not recommend treatment" in answer


def test_test_k_unrelated_question_not_found():
    # Asking for MRI brain when only CBC exists
    context = "LABORATORY REPORT: Hemoglobin: 14.2 g/dL. Platelets: 250000 /uL."
    answer = generate_answer(context, "What were the results of the brain MRI scan?")
    assert answer == "Not found in available records."


def test_test_l_cross_patient_isolation():
    db, patient_a_id, patient_b_id, owner_id = create_test_fixtures()
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


if __name__ == "__main__":
    print("Running Ask NeuroScribe Query Intent & Retrieval Test Suite...")
    test_intent_detection()
    print("Test Intent Detection: PASSED")
    test_test_a_summarize_last_consultation()
    print("Test A (Summarize last consultation): PASSED")
    test_test_b_patient_statements_last_consultation()
    print("Test B (Patient statements): PASSED")
    test_test_c_patient_mention_during_session()
    print("Test C (Patient mention during session): PASSED")
    test_test_d_active_medications()
    print("Test D (Active medications): PASSED")
    test_test_e_medications_currently_taking()
    print("Test E (Medications currently taking): PASSED")
    test_test_f_tell_me_about_the_patient()
    print("Test F (Tell me about the patient): PASSED")
    test_test_g_give_me_details_of_patient()
    print("Test G (Give me details of patient): PASSED")
    test_test_h_what_do_we_know_about_patient()
    print("Test H (What do we know about patient): PASSED")
    test_test_i_recent_history()
    print("Test I (Recent history): PASSED")
    test_test_j_medication_recommendation_safety_refusal()
    print("Test J (Medication recommendation safety refusal): PASSED")
    test_test_k_unrelated_question_not_found()
    print("Test K (Unrelated question not found): PASSED")
    test_test_l_cross_patient_isolation()
    print("Test L (Cross-patient isolation): PASSED")
    print("\nALL CLINICAL MEMORY INTENT TESTS PASSED SUCCESSFULLY (12/12)!")
