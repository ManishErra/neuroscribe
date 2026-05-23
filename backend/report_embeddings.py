"""
Report embedding orchestration: chunk cleaned OCR text and produce vectors.

Each chunk is embedded in document order. Returned records are structured for
future pgvector persistence (chunk_index, chunk_text, normalized embedding).
This module performs no database I/O.
"""

from __future__ import annotations

from typing import List, TypedDict

from embeddings import generate_embedding
from report_chunking import chunk_text_with_spans
from report_text_preprocess import (
    is_embeddable_chunk,
    prepare_text_for_embedding,
    remove_ocr_artifacts,
)


class ReportChunkEmbedding(TypedDict):
    """One embedded report chunk, ready for vector-store insert."""

    chunk_index: int
    chunk_text: str
    embedding: List[float]
    chunk_length: int
    char_start: int


def build_report_embeddings(report_text: str) -> List[ReportChunkEmbedding]:
    """
    Split report text into chunks and embed each chunk in order.

    Chunks are preprocessed (whitespace normalization, OCR cleanup, lowercasing)
    before embedding while original casing is kept in ``chunk_text`` for display.

    Args:
        report_text: Cleaned OCR or otherwise extracted report body.

    Returns:
        Ordered records with chunk metadata and L2-normalized embeddings.
        Empty or whitespace-only input returns an empty list.

    Raises:
        ValueError: If chunking receives invalid sizing parameters.
        RuntimeError: If the embedding model fails for any chunk.
    """
    if not report_text or not report_text.strip():
        return []

    cleaned_report = remove_ocr_artifacts(report_text)
    spans = chunk_text_with_spans(cleaned_report)
    if not spans:
        return []

    records: List[ReportChunkEmbedding] = []
    chunk_index = 0

    for span in spans:
        display_text = span["text"]
        if not is_embeddable_chunk(display_text):
            continue

        embed_text = prepare_text_for_embedding(display_text)
        if not embed_text:
            continue

        embedding = generate_embedding(embed_text)
        records.append(
            {
                "chunk_index": chunk_index,
                "chunk_text": display_text,
                "embedding": embedding,
                "chunk_length": len(display_text),
                "char_start": span["char_start"],
            }
        )
        chunk_index += 1

    return records
