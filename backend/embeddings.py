from sentence_transformers import SentenceTransformer
from typing import List

# =========================
# LOAD MODEL
# =========================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# =========================
# GENERATE EMBEDDING
# =========================

def generate_embedding(
    text: str
) -> List[float]:

    """
    Convert text into
    384-dimensional vector.
    """

    if not text or not text.strip():

        raise ValueError(
            "Cannot embed empty text"
        )

    vec = model.encode(
        text,
        normalize_embeddings=True
    )

    return vec.tolist()

# =========================
# CHUNK TEXT
# =========================

def chunk_text(
    text: str,
    chunk_size: int = 200,
    overlap: int = 20
) -> List[str]:

    """
    Split text into
    overlapping chunks.
    """

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        start += (
            chunk_size - overlap
        )

    return [

        c for c in chunks

        if len(c.strip()) > 10
    ]