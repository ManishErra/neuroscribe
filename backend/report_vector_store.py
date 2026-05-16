"""
FAISS vector store for report chunk embeddings with on-disk persistence.

Uses IndexFlatIP on L2-normalized vectors for cosine similarity. Metadata is
kept in a parallel list aligned with FAISS row indices.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional, TypedDict

import faiss
import numpy as np

from embeddings import generate_embedding
from report_embeddings import build_report_embeddings

DEFAULT_DIMENSION = 384
VECTOR_INDEX_PATH = "vector.index"
VECTOR_METADATA_PATH = "vector_metadata.json"

_MODULE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


class ChunkMetadata(TypedDict):
    """Metadata for one indexed report chunk."""

    report_id: str
    chunk_index: int
    chunk_text: str


class SimilarChunkResult(TypedDict):
    """One chunk returned from similarity search."""

    report_id: str
    chunk_index: int
    chunk_text: str
    similarity_score: float


_index: Optional[faiss.IndexFlatIP] = None
_chunk_metadata: List[ChunkMetadata] = []


def _index_path() -> Path:
    return _MODULE_DIR / VECTOR_INDEX_PATH


def _metadata_path() -> Path:
    return _MODULE_DIR / VECTOR_METADATA_PATH


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize rows so inner product equals cosine similarity."""
    vectors = vectors.astype(np.float32, copy=False)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, 1.0, norms)
    return vectors / norms


def _parse_metadata(raw: object) -> List[ChunkMetadata]:
    """Parse metadata JSON into a validated list; empty list on invalid input."""
    if not isinstance(raw, list):
        return []

    parsed: List[ChunkMetadata] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        report_id = item.get("report_id")
        chunk_index = item.get("chunk_index")
        chunk_text = item.get("chunk_text")
        if (
            not isinstance(report_id, str)
            or not report_id.strip()
            or not isinstance(chunk_index, int)
            or not isinstance(chunk_text, str)
        ):
            continue
        parsed.append(
            {
                "report_id": report_id,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
            }
        )
    return parsed


def initialize_vector_store(dimension: int = DEFAULT_DIMENSION) -> None:
    """
    Create a fresh in-memory FAISS index and clear chunk metadata.

    Args:
        dimension: Embedding vector size (384 for all-MiniLM-L6-v2).
    """
    global _index, _chunk_metadata

    if dimension < 1:
        raise ValueError("dimension must be at least 1")

    _index = faiss.IndexFlatIP(dimension)
    _chunk_metadata = []


def reset_vector_store() -> None:
    """Drop all vectors and metadata, reinitializing the default empty index."""
    initialize_vector_store(DEFAULT_DIMENSION)


def save_vector_store() -> None:
    """Persist the FAISS index and chunk metadata to disk."""
    if _index is None:
        return

    faiss.write_index(_index, str(_index_path()))
    with open(_metadata_path(), "w", encoding="utf-8") as handle:
        json.dump(_chunk_metadata, handle, ensure_ascii=False)


def load_vector_store() -> None:
    """Load persisted index and metadata, or initialize an empty store."""
    global _index, _chunk_metadata

    index_file = _index_path()
    metadata_file = _metadata_path()

    if not index_file.is_file() or not metadata_file.is_file():
        initialize_vector_store()
        return

    try:
        loaded_index = faiss.read_index(str(index_file))
        with open(metadata_file, encoding="utf-8") as handle:
            raw_metadata = json.load(handle)
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        logger.warning("Failed to load vector store files: %s", exc)
        initialize_vector_store()
        return

    metadata = _parse_metadata(raw_metadata)
    if loaded_index.ntotal != len(metadata):
        logger.warning(
            "Vector index/metadata size mismatch (%s vs %s); starting fresh.",
            loaded_index.ntotal,
            len(metadata),
        )
        initialize_vector_store()
        return

    _index = loaded_index
    _chunk_metadata = metadata


def add_report_embeddings(report_id: str, report_text: str) -> int:
    """
    Chunk and embed a report, then append vectors and metadata to the store.

    Args:
        report_id: Identifier for the source report.
        report_text: Cleaned report body to chunk and embed.

    Returns:
        Number of chunks added (0 if text is empty or yields no chunks).

    Raises:
        ValueError: If ``report_id`` is empty or embedding dimension mismatches.
        RuntimeError: If embedding generation fails.
    """
    global _index

    if not report_id or not report_id.strip():
        raise ValueError("report_id cannot be empty")

    records = build_report_embeddings(report_text)
    if not records:
        return 0

    vectors = np.array(
        [record["embedding"] for record in records],
        dtype=np.float32,
    )
    dimension = vectors.shape[1]

    if _index is None:
        initialize_vector_store(dimension)
    elif _index.d != dimension:
        raise ValueError(
            f"Embedding dimension {dimension} does not match index dimension {_index.d}"
        )

    normalized = _normalize_vectors(vectors)
    assert _index is not None
    _index.add(normalized)

    for record in records:
        _chunk_metadata.append(
            {
                "report_id": report_id,
                "chunk_index": record["chunk_index"],
                "chunk_text": record["chunk_text"],
            }
        )

    save_vector_store()
    return len(records)


def search_similar_chunks(
    query: str,
    top_k: int = 5,
) -> List[SimilarChunkResult]:
    """
    Find the most similar indexed chunks to a natural-language query.

    Args:
        query: Search text; embedded and compared via cosine similarity.
        top_k: Maximum number of results (capped by index size).

    Returns:
        Up to ``top_k`` hits with similarity scores in descending order.
        Returns an empty list when the index is uninitialized or empty.

    Raises:
        ValueError: If ``query`` is empty or ``top_k`` is less than 1.
        RuntimeError: If query embedding fails.
    """
    if not query or not query.strip():
        raise ValueError("query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if _index is None or _index.ntotal == 0:
        return []

    query_vec = np.array([generate_embedding(query)], dtype=np.float32)
    query_vec = _normalize_vectors(query_vec)

    k = min(top_k, _index.ntotal)
    scores, indices = _index.search(query_vec, k)

    results: List[SimilarChunkResult] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        meta = _chunk_metadata[idx]
        results.append(
            {
                "report_id": meta["report_id"],
                "chunk_index": meta["chunk_index"],
                "chunk_text": meta["chunk_text"],
                "similarity_score": round(float(score), 4),
            }
        )

    return results


load_vector_store()
