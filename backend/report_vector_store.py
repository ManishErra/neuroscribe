"""
FAISS vector store for report chunk embeddings with on-disk persistence.

Uses IndexFlatIP on L2-normalized vectors for cosine similarity.
Metadata is stored alongside FAISS indices.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import List, NotRequired, Optional, TypedDict

import faiss
import numpy as np

from embeddings import generate_embedding
from report_embeddings import build_report_embeddings
from report_text_preprocess import prepare_text_for_embedding

DEFAULT_DIMENSION = 384

VECTOR_INDEX_PATH = "vector.index"
VECTOR_METADATA_PATH = "vector_metadata.json"

DEFAULT_TOP_K = 5

# Lower threshold helps OCR-heavy medical reports
SIMILARITY_THRESHOLD = 0.40

SEARCH_OVERSAMPLE_FACTOR = 3

PREVIEW_CHARS = 120

LAB_VALUE_PATTERN = re.compile(
    r"\b\d+(\.\d+)?\s?(g/dl|mg/dl|%|cells/ul|x10\^3/ul|mmol/l)?\b",
    re.IGNORECASE,
)

MEDICAL_QUERY_SYNONYMS = {
    "hemoglobin": ["hb", "hgb"],
    "glucose": ["sugar", "blood glucose"],
    "wbc": ["white blood cell"],
    "rbc": ["red blood cell"],
    "platelets": ["platelet count"],
    "creatinine": ["creat"],
    "bilirubin": ["bili"],
}

_MODULE_DIR = Path(__file__).resolve().parent

logger = logging.getLogger(__name__)


class ChunkMetadata(TypedDict):
    """Metadata for one indexed report chunk."""

    report_id: str
    chunk_index: int
    chunk_text: str
    chunk_length: NotRequired[int]
    report_source: NotRequired[str]
    chunk_position: NotRequired[int]


class SimilarChunkResult(TypedDict):
    """One chunk returned from similarity search."""

    report_id: str
    chunk_index: int
    chunk_text: str
    similarity_score: float
    chunk_length: NotRequired[int]
    report_source: NotRequired[str]
    chunk_position: NotRequired[int]


_index: Optional[faiss.IndexFlatIP] = None

_chunk_metadata: List[ChunkMetadata] = []


def _index_path() -> Path:
    return _MODULE_DIR / VECTOR_INDEX_PATH


def _metadata_path() -> Path:
    return _MODULE_DIR / VECTOR_METADATA_PATH


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors for cosine similarity."""

    vectors = vectors.astype(np.float32, copy=False)

    norms = np.linalg.norm(
        vectors,
        axis=1,
        keepdims=True,
    )

    norms = np.where(
        norms == 0.0,
        1.0,
        norms,
    )

    return vectors / norms


def _expand_medical_query(query: str) -> str:
    """
    Expand medical query using lightweight synonyms.
    """

    expanded = [query]

    lower_query = query.lower()

    for term, synonyms in MEDICAL_QUERY_SYNONYMS.items():

        if term in lower_query:
            expanded.extend(synonyms)

    return " ".join(expanded)


def _parse_metadata(raw: object) -> List[ChunkMetadata]:
    """Parse metadata safely."""

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

        meta: ChunkMetadata = {
            "report_id": report_id,
            "chunk_index": chunk_index,
            "chunk_text": chunk_text,
        }

        chunk_length = item.get("chunk_length")

        if isinstance(chunk_length, int):
            meta["chunk_length"] = chunk_length

        report_source = item.get("report_source")

        if isinstance(report_source, str):
            meta["report_source"] = report_source

        chunk_position = item.get("chunk_position")

        if isinstance(chunk_position, int):
            meta["chunk_position"] = chunk_position

        parsed.append(meta)

    return parsed


def _result_from_metadata(
    meta: ChunkMetadata,
    similarity_score: float,
) -> SimilarChunkResult:
    """Build retrieval result."""

    result: SimilarChunkResult = {
        "report_id": meta["report_id"],
        "chunk_index": meta["chunk_index"],
        "chunk_text": meta["chunk_text"],
        "similarity_score": round(similarity_score, 4),
    }

    if "chunk_length" in meta:
        result["chunk_length"] = meta["chunk_length"]

    if "report_source" in meta:
        result["report_source"] = meta["report_source"]

    if "chunk_position" in meta:
        result["chunk_position"] = meta["chunk_position"]

    return result


def _log_retrieval_debug(
    query: str,
    results: List[SimilarChunkResult],
) -> None:
    """Print retrieval debug information."""

    print("\n================ RAG DEBUG ================")

    print(f"QUERY: {query}")

    if not results:

        print("NO RESULTS FOUND")

        print("===========================================\n")

        return

    for rank, hit in enumerate(results, start=1):

        preview = (
            hit["chunk_text"][:PREVIEW_CHARS]
            .replace("\n", " ")
        )

        print(
            f"""
RESULT #{rank}
Score   : {hit['similarity_score']}
Chunk   : {hit['chunk_index']}
Preview : {preview}
"""
        )

    print("===========================================\n")


def initialize_vector_store(
    dimension: int = DEFAULT_DIMENSION,
) -> None:
    """Initialize empty FAISS vector store."""

    global _index
    global _chunk_metadata

    if dimension < 1:
        raise ValueError("dimension must be at least 1")

    _index = faiss.IndexFlatIP(dimension)

    _chunk_metadata = []


def reset_vector_store() -> None:
    """Reset vector database."""

    initialize_vector_store(DEFAULT_DIMENSION)

    save_vector_store()


def save_vector_store() -> None:
    """Persist vector index + metadata."""

    if _index is None:
        return

    faiss.write_index(
        _index,
        str(_index_path()),
    )

    with open(
        _metadata_path(),
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            _chunk_metadata,
            handle,
            ensure_ascii=False,
        )


def load_vector_store() -> None:
    """Load vector store from disk."""

    global _index
    global _chunk_metadata

    index_file = _index_path()

    metadata_file = _metadata_path()

    if not index_file.is_file() or not metadata_file.is_file():

        initialize_vector_store()

        return

    try:

        loaded_index = faiss.read_index(
            str(index_file)
        )

        with open(
            metadata_file,
            encoding="utf-8",
        ) as handle:

            raw_metadata = json.load(handle)

    except (
        OSError,
        json.JSONDecodeError,
        RuntimeError,
        ValueError,
    ) as exc:

        logger.warning(
            "Failed to load vector store: %s",
            exc,
        )

        initialize_vector_store()

        return

    metadata = _parse_metadata(raw_metadata)

    if loaded_index.ntotal != len(metadata):

        logger.warning(
            "Vector index mismatch (%s vs %s)",
            loaded_index.ntotal,
            len(metadata),
        )

        initialize_vector_store()

        return

    _index = loaded_index

    _chunk_metadata = metadata


def add_report_embeddings(
    report_id: str,
    report_text: str,
) -> int:
    """Embed report chunks and store them."""

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
            f"Embedding dimension {dimension} "
            f"does not match index dimension {_index.d}"
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
                "chunk_length": record["chunk_length"],
                "report_source": report_id,
                "chunk_position": record["char_start"],
            }
        )

    save_vector_store()

    return len(records)


def search_similar_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    *,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> List[SimilarChunkResult]:
    """
    Hybrid semantic + keyword boosted retrieval.
    """

    if not query or not query.strip():
        raise ValueError("query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if _index is None or _index.ntotal == 0:

        logger.info("Vector store is empty")

        return []

    expanded_query = _expand_medical_query(query)

    embed_query = prepare_text_for_embedding(expanded_query)

    if not embed_query:
        raise ValueError("query cannot be empty")

    query_vec = np.array(
        [generate_embedding(embed_query)],
        dtype=np.float32,
    )

    query_vec = _normalize_vectors(query_vec)

    candidate_k = min(
        max(
            top_k,
            top_k * SEARCH_OVERSAMPLE_FACTOR,
        ),
        _index.ntotal,
    )

    scores, indices = _index.search(
        query_vec,
        candidate_k,
    )

    results: List[SimilarChunkResult] = []

    query_terms = {
        term.strip().lower()
        for term in expanded_query.split()
        if len(term.strip()) > 1
    }

    seen_chunks = set()

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0:
            continue

        meta = _chunk_metadata[idx]

        chunk_key = (
            meta["report_id"],
            meta["chunk_index"],
        )

        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)

        similarity = float(score)

        chunk_lower = meta["chunk_text"].lower()

        keyword_matches = sum(
            1
            for term in query_terms
            if term in chunk_lower
        )

        keyword_bonus = keyword_matches * 0.03

        lab_bonus = 0.0

        if LAB_VALUE_PATTERN.search(chunk_lower):
            lab_bonus = 0.08

        final_score = (
            similarity
            + keyword_bonus
            + lab_bonus
        )

        if final_score < similarity_threshold:
            continue

        result = _result_from_metadata(
            meta,
            final_score,
        )

        results.append(result)

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True,
    )

    results = results[:top_k]

    _log_retrieval_debug(
        query,
        results,
    )

    return results


load_vector_store()