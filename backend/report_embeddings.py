"""
Report embedding orchestration: chunk cleaned OCR text and produce vectors.

Each chunk is embedded in document order. Returned records are structured for
future pgvector persistence (chunk_index, chunk_text, normalized embedding).
This module performs no database I/O.
"""

from __future__ import annotations

from typing import List, TypedDict

from embeddings import generate_embedding
from report_chunking import chunk_text


class ReportChunkEmbedding(TypedDict):
    """One embedded report chunk, ready for vector-store insert."""

    chunk_index: int
    chunk_text: str
    embedding: List[float]


def build_report_embeddings(report_text: str) -> List[ReportChunkEmbedding]:
    """
    Split report text into chunks and embed each chunk in order.

    Args:
        report_text: Cleaned OCR or otherwise extracted report body.

    Returns:
        Ordered records with ``chunk_index`` (0-based), ``chunk_text``, and
        ``embedding`` (384-dimensional, L2-normalized). Empty or
        whitespace-only input returns an empty list.

    Raises:
        ValueError: If ``chunk_text`` receives invalid sizing parameters, or if
            a chunk cannot be embedded.
        RuntimeError: If the embedding model fails for any chunk.
    """
    if not report_text or not report_text.strip():
        return []

    chunks = chunk_text(report_text)
    if not chunks:
        return []

    records: List[ReportChunkEmbedding] = []
    for index, text in enumerate(chunks):
        embedding = generate_embedding(text)
        records.append(
            {
                "chunk_index": index,
                "chunk_text": text,
                "embedding": embedding,
            }
        )

    return records
