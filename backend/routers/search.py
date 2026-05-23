from fastapi import APIRouter
from pydantic import BaseModel

from report_vector_store import search_similar_chunks

router = APIRouter(prefix="/ask", tags=["Ask"])


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/")
def ask_question(request: AskRequest):
    results = search_similar_chunks(
        query=request.question,
        top_k=request.top_k,
    )

    if not results:
        return {
            "question": request.question,
            "answer": "No relevant medical context found.",
            "chunks_used": [],
        }

    context = "\n\n".join(
        chunk["chunk_text"]
        for chunk in results
    )

    from llm_service import generate_answer

    answer = generate_answer(
        context=context,
        question=request.question,
    )

    return {
        "question": request.question,
        "answer": answer,
        "chunks_used": results,
    }