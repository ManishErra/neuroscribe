"""
Unified patient-scoped clinical memory retrieval for Ask NeuroScribe.

This module intentionally keeps retrieval patient-scoped at the database boundary
and combines the existing report FAISS cache with durable database records:
reports/OCR, consultation transcripts, notes, and patient/session context.
Retrieval priority is intent-aware to accurately answer clinical queries without
relying solely on literal keyword overlap.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List

from models import Note, Patient, Report, Session as SessionModel, Transcript
from report_vector_store import search_similar_chunks
from query_intents import QueryIntent, detect_query_intent, has_medication_evidence


STOP_WORDS = {
    "what", "was", "were", "is", "are", "the", "a", "an", "this", "that",
    "patient", "patients", "latest", "recent", "last", "current", "please",
    "tell", "me", "about", "give", "show", "find", "check", "any", "there",
    "their", "her", "his", "has", "have", "had", "did", "does", "do",
    "from", "for", "with", "and", "or", "to", "of", "in", "on", "during",
    "consultation", "consultations", "conversation", "conversations",
    "session", "sessions", "report", "reports", "record", "records",
    "information", "details", "summarize", "summary", "history",
}

QUERY_ALIASES = {
    "hemoglobin": {"hemoglobin", "haemoglobin", "hgb", "hb"},
    "glucose": {"glucose", "sugar", "blood sugar", "hba1c"},
    "platelet": {"platelet", "platelets", "plt"},
    "wbc": {"wbc", "white blood", "white blood cell", "white blood cells"},
    "rbc": {"rbc", "red blood", "red blood cell", "red blood cells"},
    "creatinine": {"creatinine", "creat"},
    "medication": {
        "medication", "medications", "meds", "medicine", "medicines", "drug", "drugs",
        "prescription", "prescriptions", "prescribed", "dosage", "dose", "mg", "mcg",
        "tablet", "tablets", "capsule", "capsules", "daily", "oral", "po", "qd", "bid",
        "tid", "prn", "rx", "insulin", "statin", "inhaler", "therapy",
        "no medication", "no medications", "no active medication", "no current medication",
        "not taking any medication", "not on any medication", "denies medication", "none"
    },
    "sleep": {"sleep", "sleeping", "insomnia"},
    "mood": {"mood", "feeling", "feelings", "depressed", "anxious", "anxiety"},
    "symptoms": {"symptom", "symptoms", "complaint", "complaints"},
    "plan": {"plan", "planned", "discussed", "recommendation", "follow-up"},
}


def _tokens(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if token not in STOP_WORDS and len(token) > 2
    ]


def _expanded_query_terms(question: str) -> set[str]:
    lower = (question or "").lower()
    terms = set(_tokens(question))
    for aliases in QUERY_ALIASES.values():
        if any(alias in lower for alias in aliases):
            for alias in aliases:
                terms.update(_tokens(alias))
    return terms


def _score_text(text: str, question: str) -> float:
    if not text:
        return 0.0
    lower = text.lower()
    terms = _expanded_query_terms(question)
    if not terms:
        return 0.0
    hits = sum(1 for term in terms if term in lower)
    return min(0.95, hits / max(3.0, len(terms)) + (0.15 if hits else 0.0))


def _chunk_text(text: str, size: int = 220, overlap: int = 40) -> List[str]:
    words = (text or "").split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks: List[str] = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + size]).strip()
        if len(chunk) >= 20:
            chunks.append(chunk)
        if start + size >= len(words):
            break
    return chunks


def _record(
    *,
    source_type: str,
    source_id: str,
    patient_id: str,
    text: str,
    score: float,
    source_name: str | None = None,
    source_date: str | None = None,
    chunk_index: int = 0,
) -> Dict[str, Any]:
    return {
        "source_type": source_type,
        "source_id": source_id,
        "report_id": source_id if source_type == "report" else None,
        "patient_id": patient_id,
        "chunk_index": chunk_index,
        "chunk_text": text,
        "similarity_score": round(max(0.0, min(0.99, score)), 4),
        "source_name": source_name,
        "source_date": source_date,
        # Kept for backwards compatibility with the Ask UI.
        "report_source": source_name if source_type == "report" else None,
    }


def _date_string(value: Any) -> str | None:
    return value.isoformat() if value else None


def _note_text(note: Note) -> str:
    parts: List[str] = []
    for label, raw in (("Finalized doctor note", note.doctor_edited), ("AI draft", note.ai_draft)):
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                rendered = " ".join(
                    f"{key}: {value}"
                    for key, value in parsed.items()
                    if value not in (None, "", [], {})
                )
            else:
                rendered = str(parsed)
        except Exception:
            rendered = str(raw)
        if rendered.strip():
            parts.append(f"{label}: {rendered.strip()}")
        # Finalized doctor note is authoritative; don't duplicate the AI draft
        # when both are available.
        if label == "Finalized doctor note" and note.doctor_edited:
            break
    return " ".join(parts).strip()


def retrieve_patient_context(
    db,
    patient_id: str,
    question: str,
    top_k: int = 5,
    owner_id: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve evidence from all durable clinical-memory sources for one patient.

    The patient ownership check happens before retrieval. Every returned source
    is therefore already inside the requested patient's security boundary.
    """

    patient_query = db.query(Patient).filter(Patient.id == patient_id)
    if owner_id is not None:
        patient_query = patient_query.filter(Patient.owner_id == owner_id)
    patient = patient_query.first()
    if not patient:
        return []

    limit = max(1, min(int(top_k or 5), 10))
    intent = detect_query_intent(question)
    candidates: List[Dict[str, Any]] = []

    # Fetch patient's durable sessions and reports up front
    sessions = (
        db.query(SessionModel)
        .filter(SessionModel.patient_id == patient_id)
        .order_by(SessionModel.session_date.desc().nullslast(), SessionModel.created_at.desc())
        .limit(30)
        .all()
    )
    session_by_id = {str(session.id): session for session in sessions}
    session_ids = [session.id for session in sessions]

    transcripts: List[Transcript] = []
    notes: List[Note] = []
    if session_ids:
        transcripts = (
            db.query(Transcript)
            .filter(Transcript.session_id.in_(session_ids))
            .order_by(Transcript.created_at.desc())
            .all()
        )
        notes = (
            db.query(Note)
            .filter(Note.session_id.in_(session_ids))
            .order_by(Note.created_at.desc())
            .all()
        )

    reports = (
        db.query(Report)
        .filter(
            Report.patient_id == patient_id,
            Report.ocr_status == "ready",
            Report.ocr_text.isnot(None),
        )
        .order_by(Report.report_date.desc().nullslast(), Report.created_at.desc())
        .limit(30)
        .all()
    )

    # -------------------------------------------------------------------------
    # INTENT-SPECIFIC RETRIEVAL ROUTING
    # -------------------------------------------------------------------------

    if intent == QueryIntent.LAST_CONSULTATION:
        # Prioritize: 1. Latest consultation transcript, 2. Latest note, 3. Recent reports
        if transcripts:
            for idx, transcript in enumerate(transcripts[:2]):
                session = session_by_id.get(str(transcript.session_id))
                session_date = _date_string(session.session_date if session else transcript.created_at)
                chunks = _chunk_text(transcript.raw_text or "", size=260, overlap=30)
                for c_idx, chunk in enumerate(chunks):
                    base_score = 0.95 if idx == 0 else 0.85
                    score = max(0.60, base_score - (c_idx * 0.02))
                    candidates.append(_record(
                        source_type="transcript",
                        source_id=str(transcript.id),
                        patient_id=patient_id,
                        text=chunk,
                        score=score,
                        source_name=f"Consultation — {session_date or 'undated'}",
                        source_date=session_date,
                        chunk_index=c_idx,
                    ))

        if notes:
            for idx, note in enumerate(notes[:2]):
                text = _note_text(note)
                if text:
                    session = session_by_id.get(str(note.session_id))
                    session_date = _date_string(session.session_date if session else note.created_at)
                    chunks = _chunk_text(text, size=240, overlap=30)
                    for c_idx, chunk in enumerate(chunks):
                        score = 0.90 if (idx == 0 and note.is_finalized) else 0.80
                        candidates.append(_record(
                            source_type="note",
                            source_id=str(note.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=score,
                            source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                            source_date=session_date,
                            chunk_index=c_idx,
                        ))

    elif intent == QueryIntent.PATIENT_STATEMENTS:
        # Primary source is the consultation transcript (what the patient said/reported)
        if transcripts:
            for idx, transcript in enumerate(transcripts[:3]):
                session = session_by_id.get(str(transcript.session_id))
                session_date = _date_string(session.session_date if session else transcript.created_at)
                chunks = _chunk_text(transcript.raw_text or "", size=240, overlap=30)
                for c_idx, chunk in enumerate(chunks):
                    lex_score = _score_text(chunk, question)
                    base_score = 0.96 if idx == 0 else 0.88
                    score = max(base_score - (c_idx * 0.02), lex_score)
                    candidates.append(_record(
                        source_type="transcript",
                        source_id=str(transcript.id),
                        patient_id=patient_id,
                        text=chunk,
                        score=score,
                        source_name=f"Consultation — {session_date or 'undated'}",
                        source_date=session_date,
                        chunk_index=c_idx,
                    ))

        # Secondary context: latest doctor note
        if notes:
            for note in notes[:1]:
                text = _note_text(note)
                if text:
                    session = session_by_id.get(str(note.session_id))
                    session_date = _date_string(session.session_date if session else note.created_at)
                    chunks = _chunk_text(text, size=220, overlap=20)
                    for c_idx, chunk in enumerate(chunks):
                        candidates.append(_record(
                            source_type="note",
                            source_id=str(note.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=0.82,
                            source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                            source_date=session_date,
                            chunk_index=c_idx,
                        ))

    elif intent in (QueryIntent.ACTIVE_MEDICATIONS, QueryIntent.MEDICATION_HISTORY):
        # Dedicated medication retrieval: actual medication evidence gets high priority (0.85-0.95),
        # while non-medication text is severely down-weighted (0.15-0.25).
        for note in notes:
            text = _note_text(note)
            if not text:
                continue
            session = session_by_id.get(str(note.session_id))
            session_date = _date_string(session.session_date if session else note.created_at)
            chunks = _chunk_text(text)
            for c_idx, chunk in enumerate(chunks):
                has_med = has_medication_evidence(chunk)
                score = 0.95 if (has_med and note.is_finalized) else (0.90 if has_med else 0.25)
                candidates.append(_record(
                    source_type="note",
                    source_id=str(note.id),
                    patient_id=patient_id,
                    text=chunk,
                    score=score,
                    source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                    source_date=session_date,
                    chunk_index=c_idx,
                ))

        for transcript in transcripts:
            session = session_by_id.get(str(transcript.session_id))
            session_date = _date_string(session.session_date if session else transcript.created_at)
            chunks = _chunk_text(transcript.raw_text or "")
            for c_idx, chunk in enumerate(chunks):
                has_med = has_medication_evidence(chunk)
                score = 0.88 if has_med else 0.20
                candidates.append(_record(
                    source_type="transcript",
                    source_id=str(transcript.id),
                    patient_id=patient_id,
                    text=chunk,
                    score=score,
                    source_name=f"Consultation — {session_date or 'undated'}",
                    source_date=session_date,
                    chunk_index=c_idx,
                ))

        for report in reports:
            chunks = _chunk_text(report.ocr_text or "")
            for c_idx, chunk in enumerate(chunks):
                has_med = has_medication_evidence(chunk)
                score = 0.85 if has_med else 0.15
                candidates.append(_record(
                    source_type="report",
                    source_id=str(report.id),
                    patient_id=patient_id,
                    text=chunk,
                    score=score,
                    source_name=report.original_filename or report.title or str(report.id),
                    source_date=_date_string(report.report_date or report.created_at),
                    chunk_index=c_idx,
                ))

    elif intent == QueryIntent.PATIENT_OVERVIEW:
        # Balanced composition across structured patient profile, doctor note, transcript, and reports
        patient_text = f"Patient name: {patient.name}; age: {patient.age}; gender: {patient.gender or 'not recorded'}."
        candidates.append(_record(
            source_type="patient",
            source_id=str(patient.id),
            patient_id=patient_id,
            text=patient_text,
            score=0.98,
            source_name="Patient profile",
        ))

        if notes:
            for note in notes[:1]:
                text = _note_text(note)
                if text:
                    session = session_by_id.get(str(note.session_id))
                    session_date = _date_string(session.session_date if session else note.created_at)
                    chunks = _chunk_text(text, size=240, overlap=30)
                    for c_idx, chunk in enumerate(chunks[:2]):
                        candidates.append(_record(
                            source_type="note",
                            source_id=str(note.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=0.92 - (c_idx * 0.01),
                            source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                            source_date=session_date,
                            chunk_index=c_idx,
                        ))

        if transcripts:
            for transcript in transcripts[:1]:
                session = session_by_id.get(str(transcript.session_id))
                session_date = _date_string(session.session_date if session else transcript.created_at)
                chunks = _chunk_text(transcript.raw_text or "", size=240, overlap=30)
                for c_idx, chunk in enumerate(chunks[:2]):
                    candidates.append(_record(
                        source_type="transcript",
                        source_id=str(transcript.id),
                        patient_id=patient_id,
                        text=chunk,
                        score=0.88 - (c_idx * 0.01),
                        source_name=f"Consultation — {session_date or 'undated'}",
                        source_date=session_date,
                        chunk_index=c_idx,
                    ))

        if reports:
            for r_idx, report in enumerate(reports[:2]):
                chunks = _chunk_text(report.ocr_text or "", size=240, overlap=20)
                if chunks:
                    candidates.append(_record(
                        source_type="report",
                        source_id=str(report.id),
                        patient_id=patient_id,
                        text=chunks[0],
                        score=0.82 - (r_idx * 0.01),
                        source_name=report.original_filename or report.title or str(report.id),
                        source_date=_date_string(report.report_date or report.created_at),
                        chunk_index=0,
                    ))

    elif intent == QueryIntent.RECENT_HISTORY:
        # Retrieve a balanced set of recent consultations, doctor notes, and reports
        if transcripts:
            for transcript in transcripts[:2]:
                session = session_by_id.get(str(transcript.session_id))
                session_date = _date_string(session.session_date if session else transcript.created_at)
                chunks = _chunk_text(transcript.raw_text or "", size=240, overlap=30)
                for c_idx, chunk in enumerate(chunks[:2]):
                    candidates.append(_record(
                        source_type="transcript",
                        source_id=str(transcript.id),
                        patient_id=patient_id,
                        text=chunk,
                        score=0.92,
                        source_name=f"Consultation — {session_date or 'undated'}",
                        source_date=session_date,
                        chunk_index=c_idx,
                    ))

        if notes:
            for note in notes[:2]:
                text = _note_text(note)
                if text:
                    session = session_by_id.get(str(note.session_id))
                    session_date = _date_string(session.session_date if session else note.created_at)
                    chunks = _chunk_text(text, size=240, overlap=30)
                    for c_idx, chunk in enumerate(chunks[:2]):
                        candidates.append(_record(
                            source_type="note",
                            source_id=str(note.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=0.90 if note.is_finalized else 0.85,
                            source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                            source_date=session_date,
                            chunk_index=c_idx,
                        ))

        if reports:
            for report in reports[:2]:
                chunks = _chunk_text(report.ocr_text or "", size=240, overlap=20)
                if chunks:
                    candidates.append(_record(
                        source_type="report",
                        source_id=str(report.id),
                        patient_id=patient_id,
                        text=chunks[0],
                        score=0.85,
                        source_name=report.original_filename or report.title or str(report.id),
                        source_date=_date_string(report.report_date or report.created_at),
                        chunk_index=0,
                    ))

    else:
        # GENERAL_CLINICAL / LAB_RESULT / Default retrieval
        # 1) Existing FAISS report cache optimization
        try:
            faiss_results = search_similar_chunks(
                query=question,
                top_k=limit,
                owner_id=owner_id,
                patient_id=patient_id,
            )
            for hit in faiss_results:
                candidates.append(
                    _record(
                        source_type="report",
                        source_id=str(hit["report_id"]),
                        patient_id=patient_id,
                        text=hit["chunk_text"],
                        score=float(hit.get("similarity_score", 0.0)),
                        source_name=hit.get("report_source"),
                        chunk_index=int(hit.get("chunk_index", 0)),
                    )
                )
        except Exception:
            # A missing/corrupt local FAISS cache must never break Ask.
            pass

        # 2) Durable reports/OCR search
        for report in reports:
            chunks = _chunk_text(report.ocr_text or "")
            for index, chunk in enumerate(chunks):
                score = _score_text(chunk, question)
                if score > 0:
                    candidates.append(
                        _record(
                            source_type="report",
                            source_id=str(report.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=score,
                            source_name=report.original_filename or report.title or str(report.id),
                            source_date=_date_string(report.report_date or report.created_at),
                            chunk_index=index,
                        )
                    )

        # 3) Consultation transcripts search
        for transcript in transcripts:
            session = session_by_id.get(str(transcript.session_id))
            session_date = _date_string(session.session_date if session else transcript.created_at)
            for index, chunk in enumerate(_chunk_text(transcript.raw_text or "")):
                score = _score_text(chunk, question)
                if score > 0:
                    candidates.append(
                        _record(
                            source_type="transcript",
                            source_id=str(transcript.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=score,
                            source_name=f"Consultation — {session_date or 'undated'}",
                            source_date=session_date,
                            chunk_index=index,
                        )
                    )

        # 4) Notes search
        for note in notes:
            text = _note_text(note)
            if not text:
                continue
            session = session_by_id.get(str(note.session_id))
            session_date = _date_string(session.session_date if session else note.created_at)
            for index, chunk in enumerate(_chunk_text(text)):
                score = _score_text(chunk, question)
                if score > 0:
                    candidates.append(
                        _record(
                            source_type="note",
                            source_id=str(note.id),
                            patient_id=patient_id,
                            text=chunk,
                            score=score + (0.05 if note.is_finalized else 0.0),
                            source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                            source_date=session_date,
                            chunk_index=index,
                        )
                    )

        # 5) Demographic context if asked
        patient_question_terms = {"age", "gender", "sex", "name", "demographic", "demographics"}
        if patient_question_terms.intersection(_expanded_query_terms(question)):
            patient_text = f"Patient name: {patient.name}; age: {patient.age}; gender: {patient.gender or 'not recorded'}."
            candidates.append(
                _record(
                    source_type="patient",
                    source_id=str(patient.id),
                    patient_id=patient_id,
                    text=patient_text,
                    score=0.85,
                    source_name="Patient profile",
                )
            )

        # 6) Broad fallback: If lexical matching found nothing, provide a balanced sample of:
        # - latest report
        # - latest consultation transcript
        # - latest doctor note (preferring finalized doctor note)
        if not candidates:
            if reports:
                report = reports[0]
                chunks = _chunk_text(report.ocr_text or "", size=260, overlap=20)
                if chunks:
                    candidates.append(_record(
                        source_type="report",
                        source_id=str(report.id),
                        patient_id=patient_id,
                        text=chunks[0],
                        score=0.42,
                        source_name=report.original_filename or report.title or str(report.id),
                        source_date=_date_string(report.report_date or report.created_at),
                    ))
            if transcripts:
                transcript = transcripts[0]
                session = session_by_id.get(str(transcript.session_id))
                session_date = _date_string(session.session_date if session else transcript.created_at)
                chunks = _chunk_text(transcript.raw_text or "", size=260, overlap=20)
                if chunks:
                    candidates.append(_record(
                        source_type="transcript",
                        source_id=str(transcript.id),
                        patient_id=patient_id,
                        text=chunks[0],
                        score=0.40,
                        source_name=f"Consultation — {session_date or 'undated'}",
                        source_date=session_date,
                    ))
            if notes:
                note = notes[0]
                text = _note_text(note)
                if text:
                    session = session_by_id.get(str(note.session_id))
                    session_date = _date_string(session.session_date if session else note.created_at)
                    chunks = _chunk_text(text, size=260, overlap=20)
                    if chunks:
                        candidates.append(_record(
                            source_type="note",
                            source_id=str(note.id),
                            patient_id=patient_id,
                            text=chunks[0],
                            score=0.41 if note.is_finalized else 0.38,
                            source_name=f"{'Doctor note' if note.is_finalized else 'AI note'} — {session_date or 'undated'}",
                            source_date=session_date,
                        ))

    # Deduplicate identical evidence, preferring the higher score.
    deduped: Dict[tuple[str, str], Dict[str, Any]] = {}
    for candidate in candidates:
        key = (candidate["source_type"], " ".join(candidate["chunk_text"].lower().split()))
        existing = deduped.get(key)
        if existing is None or candidate["similarity_score"] > existing["similarity_score"]:
            deduped[key] = candidate

    results = list(deduped.values())

    # Favor explicit match score, then recency.
    def sort_key(item: Dict[str, Any]):
        date_value = item.get("source_date") or ""
        return (item["similarity_score"], date_value)

    results.sort(key=sort_key, reverse=True)
    return results[:limit]
