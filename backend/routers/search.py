from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
import json

from clinical_memory import retrieve_patient_context
from llm_service import generate_answer
from auth_utils import get_current_user
from rate_limiter import rag_limiter

router = APIRouter(
    prefix="/ask",
    tags=["Ask"],
    dependencies=[Depends(get_current_user)],
)


class AskRequest(BaseModel):
    patient_id: str
    question: str
    top_k: int = 5


@router.post("/")
def ask_question(
    request: AskRequest,
    http_request: Request,
    current_user=Depends(get_current_user),
):
    content_length = http_request.headers.get("content-length")
    if content_length and int(content_length) > 20 * 1024:
        raise HTTPException(status_code=413, detail="Request payload exceeds 20 KB limit")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Clinical question cannot be empty")

    rag_limiter.check(http_request)

    from database import get_db
    db = next(get_db())

    # The backend patient lookup is the authoritative security boundary.
    # The LLM never receives records from another patient.
    from models import Patient

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == request.patient_id,
            Patient.owner_id == current_user.id,
        )
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or access denied")

    results = retrieve_patient_context(
        db=db,
        patient_id=str(request.patient_id),
        question=request.question,
        top_k=request.top_k,
        owner_id=str(current_user.id),
    )

    if not results:
        return {
            "question": request.question,
            "answer": "Not found in available records.",
            "chunks_used": [],
        }

    # Include source labels in the context so the LLM can distinguish a report
    # from a consultation or note and answer the user's actual question.
    context_parts = []
    for item in results:
        source_label = item.get("source_name") or item.get("source_type") or "clinical record"
        source_date = item.get("source_date")
        date_suffix = f" | Date: {source_date}" if source_date else ""
        context_parts.append(
            f"[Source: {source_label} | Type: {item.get('source_type')}{date_suffix}]\n"
            f"{item.get('chunk_text', '')}"
        )
    context = "\n\n".join(context_parts)

    from clinical_query_rewriter import rewrite_query
    expanded_query = rewrite_query(request.question)

    try:
        answer = generate_answer(
            context=context,
            question=expanded_query,
        )
    except Exception as exc:
        return {
            "question": request.question,
            "answer": "The clinical answer service is temporarily unavailable. Please retry.",
            "chunks_used": results,
            "error": str(exc),
        }

    try:
        if "\n\n" in answer.strip():
            parts = [part.strip() for part in answer.split("\n\n") if part.strip()]
            parsed_list = []
            for part in parts:
                try:
                    parsed_list.append(json.loads(part))
                except Exception:
                    pass
            parsed_answer = parsed_list if parsed_list else answer
        else:
            parsed_answer = json.loads(answer)
    except Exception:
        parsed_answer = answer

    try:
        from confidence_scoring import enrich_structured_answer
        if isinstance(parsed_answer, dict):
            parsed_answer = enrich_structured_answer(parsed_answer, results)
        elif isinstance(parsed_answer, list):
            parsed_answer = [
                enrich_structured_answer(item, results) if isinstance(item, dict) else item
                for item in parsed_answer
            ]
    except Exception:
        # Source retrieval should remain useful even if confidence enrichment
        # is unavailable.
        pass

    return {
        "question": request.question,
        "answer": parsed_answer,
        "chunks_used": results,
    }
