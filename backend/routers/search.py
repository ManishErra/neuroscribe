from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import json
import re
from datetime import datetime

from report_vector_store import search_similar_chunks
from llm_service import generate_answer
from auth_utils import get_current_user
from rate_limiter import rag_limiter

router = APIRouter(
    prefix="/ask",
    tags=["Ask"],
    dependencies=[Depends(get_current_user)]
)


class AskRequest(BaseModel):
    patient_id: str
    question: str
    top_k: int = 5


def _fallback_report_context(db, patient_id: str, question: str, top_k: int):
    """Retrieve context directly from ready OCR reports when FAISS has no usable hits.

    Railway/container restarts can reset the local FAISS files. This DB-backed
    fallback keeps Ask functional without re-running embeddings synchronously.
    It is strictly scoped to the authenticated patient's reports.
    """
    from models import Report

    reports = (
        db.query(Report)
        .filter(
            Report.patient_id == patient_id,
            Report.ocr_status == "ready",
            Report.ocr_text.isnot(None),
        )
        .order_by(Report.report_date.desc().nullslast(), Report.created_at.desc())
        .limit(20)
        .all()
    )

    if not reports:
        return []

    q = question.lower()
    # Include clinical synonyms so "hemoglobin", "Hb", and "Hgb" retrieve the
    # same OCR text even when OCR preserved a different abbreviation.
    synonym_groups = [
        ("hemoglobin", ("hemoglobin", "haemoglobin", "hgb", "hb")),
        ("glucose", ("glucose", "blood sugar", "sugar")),
        ("platelet", ("platelet", "platelets", "plt")),
        ("wbc", ("wbc", "white blood", "white blood cell")),
        ("rbc", ("rbc", "red blood", "red blood cell")),
        ("creatinine", ("creatinine", "creat")),
    ]
    terms = set(re.findall(r"[a-z0-9]+", q))
    expanded_terms = set(terms)
    for _, aliases in synonym_groups:
        if any(alias in q for alias in aliases):
            expanded_terms.update(re.findall(r"[a-z0-9]+", " ".join(aliases)))

    candidates = []
    for report in reports:
        text = (report.ocr_text or "").strip()
        if not text:
            continue

        # Keep chunks small enough for the LLM context while preserving nearby
        # lab values and labels. Prefer chunks containing query terms.
        words = text.split()
        window = 180
        step = 140
        for start in range(0, len(words), step):
            chunk = " ".join(words[start:start + window]).strip()
            if len(chunk) < 20:
                continue
            lower = chunk.lower()
            term_hits = sum(1 for term in expanded_terms if len(term) > 1 and term in lower)
            if term_hits:
                candidates.append((term_hits, report, chunk))
            if start + window >= len(words):
                break

    # If lexical matching finds nothing, use the latest report as context for
    # broad questions such as "summarize the latest report".
    if not candidates:
        latest = reports[0]
        text = (latest.ocr_text or "").strip()
        if text:
            words = text.split()
            candidates = [(0, latest, " ".join(words[:360]))]

    candidates.sort(key=lambda item: (item[0], item[1].report_date or datetime.min.date()), reverse=True)

    results = []
    for idx, (_, report, chunk) in enumerate(candidates[:top_k]):
        results.append({
            "report_id": str(report.id),
            "patient_id": str(report.patient_id),
            "chunk_index": idx,
            "chunk_text": chunk,
            "similarity_score": 0.5,
            "report_source": report.original_filename or report.title or str(report.id),
            "owner_id": None,
        })
    return results


@router.post("/")
def ask_question(
    request: AskRequest,
    http_request: Request,
    current_user = Depends(get_current_user),
):
    content_length = http_request.headers.get('content-length')
    if content_length and int(content_length) > 20 * 1024:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="Request payload exceeds 20 KB limit")

    from database import get_db
    from models import Patient
    db = next(get_db())
    patient = db.query(Patient).filter(
        Patient.id == request.patient_id,
        Patient.owner_id == current_user.id
    ).first()
    if not patient:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Patient not found or access denied")

    rag_limiter.check(http_request)

    # STEP 1 — retrieve relevant chunks
    results = search_similar_chunks(
        query=request.question,
        top_k=request.top_k,
        owner_id=str(current_user.id),
        patient_id=str(request.patient_id),
    )

    # STEP 2 — resilient DB fallback.
    # FAISS is a local on-disk cache and can be empty after a Railway restart or
    # deployment. Do not make the user re-index reports just to ask a question.
    if not results:
        results = _fallback_report_context(
            db=db,
            patient_id=str(request.patient_id),
            question=request.question,
            top_k=request.top_k,
        )

    # STEP 3 — build retrieval context
    if not results:
        return {
            "question": request.question,
            "answer": "No relevant medical context found in this patient's ready reports.",
            "chunks_used": [],
        }
    context = "\n\n".join(
        chunk.get("chunk_text", "")
        for chunk in results
    )

    from clinical_query_rewriter import rewrite_query
    expanded_query = rewrite_query(request.question)

    # STEP 4 — generate answer
    try:

        answer = generate_answer(
            context=context,
            question=expanded_query,
        )

    except Exception as e:

        return {
            "question": request.question,
            "answer": f"LLM generation failed: {str(e)}",
            "chunks_used": results,
        }

    # STEP 5 — attempt JSON parsing and confidence/source attribution enrichment
    parsed_answer = None
    try:
        # Check if multiple JSON objects are separated by double newline
        if "\n\n" in answer.strip():
            parts = [p.strip() for p in answer.split("\n\n") if p.strip()]
            parsed_list = []
            for part in parts:
                try:
                    parsed_list.append(json.loads(part))
                except Exception:
                    pass
            if parsed_list:
                parsed_answer = parsed_list
        
        if parsed_answer is None:
            parsed_answer = json.loads(answer)
    except Exception:
        parsed_answer = answer

    # Enrich structured clinical answers
    try:
        from confidence_scoring import enrich_structured_answer
        if isinstance(parsed_answer, dict):
            parsed_answer = enrich_structured_answer(parsed_answer, results)
        elif isinstance(parsed_answer, list):
            parsed_answer = [
                enrich_structured_answer(item, results) if isinstance(item, dict) else item
                for item in parsed_answer
            ]
    except Exception as e:
        print(f"[ERROR] Failed to enrich structured answer: {e}")

    # STEP 5.5 — Clear chunks_used if no relevant information is present in the report
    if isinstance(parsed_answer, str) and ("does not contain" in parsed_answer.lower() or "no relevant medical context" in parsed_answer.lower()):
        results = []

    # STEP 6 — final API response
    return {
        "question": request.question,
        "answer": parsed_answer,
        "chunks_used": results,
    }