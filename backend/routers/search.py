from fastapi import APIRouter
from pydantic import BaseModel
import json

from report_vector_store import search_similar_chunks
from llm_service import generate_answer


router = APIRouter(
    prefix="/ask",
    tags=["Ask"],
)


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/")
def ask_question(request: AskRequest):

    # STEP 1 — retrieve relevant chunks
    results = search_similar_chunks(
        query=request.question,
        top_k=request.top_k,
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

    # STEP 4 — generate answer
    try:

        answer = generate_answer(
            context=context,
            question=request.question,
        )

    except Exception as e:

        return {
            "question": request.question,
            "answer": f"LLM generation failed: {str(e)}",
            "chunks_used": results,
        }

    # STEP 5 — attempt JSON parsing
    try:

        parsed_answer = json.loads(answer)

    except Exception:

        parsed_answer = answer

    # STEP 6 — final API response
    return {
        "question": request.question,
        "answer": parsed_answer,
        "chunks_used": results,
    }