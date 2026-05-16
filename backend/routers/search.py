from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from report_vector_store import search_similar_chunks

router = APIRouter(prefix="/search", tags=["Search"])


class SearchQueryRequest(BaseModel):
    query: str
    top_k: int = 5

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("query cannot be empty")
        return value.strip()

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        if value < 1:
            raise ValueError("top_k must be at least 1")
        return value


@router.post("/query")
def query_search(request: SearchQueryRequest):
    try:
        return search_similar_chunks(
            query=request.query,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
