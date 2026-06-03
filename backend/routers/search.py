from fastapi import APIRouter, Depends
from pydantic import BaseModel
import json

from report_vector_store import search_similar_chunks
from llm_service import generate_answer
from auth_utils import get_current_user

router = APIRouter(
    prefix="/ask",
    tags=["Ask"],
    dependencies=[Depends(get_current_user)]
)


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/")
def ask_question(
    request: AskRequest,
    current_user = Depends(get_current_user),
):

    # STEP 1 — retrieve relevant chunks
    results = search_similar_chunks(
        query=request.question,
        top_k=request.top_k,
        owner_id=str(current_user.id),
    )

    # STEP 2 — no context found
    if not results:

        return {
            "question": request.question,
            "answer": "No relevant medical context found.",
            "chunks_used": [],
        }

    # STEP 3 — build retrieval context
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

    # STEP 6 — final API response
    return {
        "question": request.question,
        "answer": parsed_answer,
        "chunks_used": results,
    }