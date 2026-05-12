from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from pydantic import BaseModel

from sqlalchemy.orm import Session as DBSession

from database import get_db

from embeddings import search_similar

from groq import Groq

from prompts import (
    RAG_SYSTEM,
    build_rag_prompt
)

from dotenv import load_dotenv

import os


# =========================================
# LOAD ENVIRONMENT
# =========================================

load_dotenv()


# =========================================
# GROQ CLIENT
# =========================================

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================
# ROUTER
# =========================================

router = APIRouter(
    prefix="/search",
    tags=["Semantic Search"]
)


# =========================================
# CONSTANTS
# =========================================

MAX_QUERY_LENGTH = 500

MIN_TOP_K = 1

MAX_TOP_K = 10

# Lower threshold for development dataset
# Increase later for production safety
SIMILARITY_THRESHOLD = 0.25


# =========================================
# REQUEST MODELS
# =========================================

class SearchRequest(BaseModel):

    query: str

    patient_id: str

    top_k: int = 3


class AskRequest(BaseModel):

    query: str

    patient_id: str


# =========================================
# HELPERS
# =========================================

def validate_query(query: str):

    cleaned = query.strip()

    if not cleaned:

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    if len(cleaned) > MAX_QUERY_LENGTH:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Query too long. "
                f"Max {MAX_QUERY_LENGTH} chars."
            )
        )

    return cleaned


def validate_top_k(top_k: int):

    if top_k < MIN_TOP_K or top_k > MAX_TOP_K:

        raise HTTPException(
            status_code=400,
            detail=(
                f"top_k must be between "
                f"{MIN_TOP_K} and {MAX_TOP_K}"
            )
        )


def filter_good_chunks(
    chunks: list,
    threshold: float = SIMILARITY_THRESHOLD
) -> list:

    """
    Remove weak semantic matches.
    """

    filtered = [

        chunk

        for chunk in chunks

        if chunk.get("similarity", 0) >= threshold
    ]

    # Highest similarity first
    filtered.sort(
        key=lambda x: x.get("similarity", 0),
        reverse=True
    )

    return filtered


def build_not_found_response(query: str):

    return {

        "answer":
            "Not found in available records.",

        "sources": [],

        "citation_verified": False,

        "query": query
    }


# =========================================
# RAW VECTOR SEARCH
# =========================================

@router.post("/")
def search(

    req: SearchRequest,

    db: DBSession = Depends(get_db)

):

    # =====================================
    # VALIDATION
    # =====================================

    cleaned_query = validate_query(
        req.query
    )

    validate_top_k(req.top_k)

    # =====================================
    # VECTOR SEARCH
    # =====================================

    try:

        results = search_similar(

            query=cleaned_query,

            patient_id=req.patient_id,

            db=db,

            top_k=req.top_k
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Search failed: {str(e)}"
        )

    # =====================================
    # EMPTY RESULTS
    # =====================================

    if not results:

        return {

            "query": cleaned_query,

            "results": [],

            "message":
                "No matching records found."
        }

    # =====================================
    # SUCCESS
    # =====================================

    return {

        "query": cleaned_query,

        "results": results,

        "count": len(results)
    }


# =========================================
# RAG QUESTION ANSWERING
# =========================================

@router.post("/ask")
def ask(

    req: AskRequest,

    db: DBSession = Depends(get_db)

):

    # =====================================
    # VALIDATION
    # =====================================

    cleaned_query = validate_query(
        req.query
    )

    # =====================================
    # STEP 1: VECTOR RETRIEVAL
    # =====================================

    try:

        chunks = search_similar(

            query=cleaned_query,

            patient_id=req.patient_id,

            db=db,

            top_k=4
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Retrieval failed: {str(e)}"
        )

    # =====================================
    # NO CHUNKS FOUND
    # =====================================

    if not chunks:

        return build_not_found_response(
            cleaned_query
        )

    # =====================================
    # FILTER LOW QUALITY CHUNKS
    # =====================================

    good_chunks = filter_good_chunks(
        chunks
    )

    if not good_chunks:

        return build_not_found_response(
            cleaned_query
        )

    # =====================================
    # STEP 2: LLM GENERATION
    # =====================================

    try:

        response = (
            groq_client.chat.completions.create(

                model="llama-3.3-70b-versatile",

                messages=[

                    {
                        "role": "system",

                        "content": RAG_SYSTEM
                    },

                    {
                        "role": "user",

                        "content":
                            build_rag_prompt(
                                cleaned_query,
                                good_chunks
                            )
                    }
                ],

                temperature=0.1,

                max_tokens=300
            )
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"LLM failed: {str(e)}"
        )

    # =====================================
    # EXTRACT ANSWER
    # =====================================

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    if not answer or not answer.strip():

        answer = (
            "Not found in available records."
        )

    answer = answer.strip()

    # =====================================
    # VERIFY DATE CITATIONS
    # =====================================

    cited_dates = [

        c["session_date"]

        for c in good_chunks

        if (
            c.get("session_date")
            and c["session_date"] in answer
        )
    ]

    citation_verified = (
        len(cited_dates) > 0
    )

    # =====================================
    # FORMAT SOURCES
    # =====================================

    sources = [

        {

            "date":
                c.get("session_date"),

            "similarity":
                c.get("similarity"),

            "excerpt":
                c.get("chunk", "")[:120]
                + "..."
        }

        for c in good_chunks
    ]

    # =====================================
    # SUCCESS
    # =====================================

    return {

        "answer": answer,

        "sources": sources,

        "citation_verified":
            citation_verified,

        "query":
            cleaned_query,

        "retrieved_chunks":
            len(good_chunks)
    }