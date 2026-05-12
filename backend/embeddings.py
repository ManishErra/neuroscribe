from sentence_transformers import SentenceTransformer

from typing import List, Dict, Any

from sqlalchemy import text as sql_text


# =========================================
# LOAD EMBEDDING MODEL
# =========================================

# Model loaded once globally
# Prevents reloading on every request

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================
# GENERATE EMBEDDING
# =========================================

def generate_embedding(
    text: str
) -> List[float]:

    """
    Convert text into
    normalized 384-dimensional vector.
    """

    if not text or not text.strip():

        raise ValueError(
            "Cannot embed empty text"
        )

    try:

        vec = model.encode(

            text,

            normalize_embeddings=True

        )

        return vec.tolist()

    except Exception as e:

        raise RuntimeError(
            f"Embedding generation failed: {str(e)}"
        )


# =========================================
# CHUNK TEXT
# =========================================

def chunk_text(

    text: str,

    chunk_size: int = 200,

    overlap: int = 20

) -> List[str]:

    """
    Split large text into
    overlapping chunks.

    chunk_size:
        Approximate words per chunk

    overlap:
        Shared words between chunks
        for semantic continuity
    """

    if not text or not text.strip():
        return []

    if chunk_size <= overlap:

        raise ValueError(
            "chunk_size must be greater than overlap"
        )

    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0

    step = chunk_size - overlap

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        ).strip()

        if len(chunk) > 10:

            chunks.append(chunk)

        start += step

    return chunks


# =========================================
# SEMANTIC SEARCH
# =========================================

def search_similar(

    query: str,

    patient_id: str,

    db,

    top_k: int = 3

) -> List[Dict[str, Any]]:

    """
    Semantic similarity search
    using pgvector cosine distance.
    """

    if not query or not query.strip():

        raise ValueError(
            "Query cannot be empty"
        )

    if top_k < 1:
        top_k = 1

    # -------------------------------------
    # GENERATE QUERY VECTOR
    # -------------------------------------

    query_vec = generate_embedding(
        query
    )

    query_vec_str = str(query_vec)

    # -------------------------------------
    # VECTOR SEARCH
    # -------------------------------------

    try:

        results = db.execute(

            sql_text("""

                SELECT

                    e.chunk_text,

                    e.source_id,

                    e.source_type,

                    n.session_id,

                    s.session_date,

                    1 - (
                        e.embedding <=>
                        CAST(:query_vec AS vector)
                    ) AS similarity

                FROM embeddings e

                LEFT JOIN notes n
                    ON e.source_id = n.id

                LEFT JOIN sessions s
                    ON n.session_id = s.id

                WHERE s.patient_id = :patient_id

                ORDER BY

                    e.embedding <=>
                    CAST(:query_vec AS vector)

                LIMIT :top_k

            """),

            {

                "query_vec": query_vec_str,

                "patient_id": patient_id,

                "top_k": top_k

            }

        ).fetchall()

    except Exception as e:

        raise RuntimeError(
            f"Vector search failed: {str(e)}"
        )

    # -------------------------------------
    # FORMAT RESULTS
    # -------------------------------------

    formatted_results = []

    for row in results:

        similarity = float(row.similarity)

        formatted_results.append({

            "chunk": row.chunk_text,

            "session_date": (
                str(row.session_date)
                if row.session_date
                else None
            ),

            "similarity": round(
                similarity,
                3
            )

        })

    return formatted_results