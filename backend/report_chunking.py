"""
Character-based text chunking with sentence-aware boundaries and overlap.

Designed for report OCR output and downstream embedding pipelines.
"""

from __future__ import annotations

import re
from typing import List, TypedDict


class ChunkSpan(TypedDict):
    """One text chunk with its start offset in the source document."""

    text: str
    char_start: int

# Sentence ends before a likely new sentence; paragraph breaks; avoid decimals/abbrevs.
_SENTENCE_SPLIT = re.compile(
    r"(?<!\d)"
    r"(?<!Dr)(?<!Mr)(?<!Mrs)(?<!Ms)(?<!Sr)(?<!Jr)(?<!St)(?<!No)(?<!vs)"
    r"(?<=[.!?])\s+(?=[A-Z0-9])"
    r"|\n{2,}"
)


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving non-empty segments."""
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [part.strip() for part in parts if part.strip()]


def _split_long_segment(segment: str, max_len: int) -> List[str]:
    """
    Split an oversized segment on word boundaries (hard-split words if needed).
    """
    words = segment.split()
    if not words:
        return []

    pieces: List[str] = []
    current: List[str] = []
    current_len = 0

    for word in words:
        extra = len(word) if not current else 1 + len(word)

        if current and current_len + extra > max_len:
            pieces.append(" ".join(current))
            current = []
            current_len = 0

        if len(word) > max_len:
            if current:
                pieces.append(" ".join(current))
                current = []
                current_len = 0
            for start in range(0, len(word), max_len):
                pieces.append(word[start : start + max_len])
            continue

        current.append(word)
        current_len += extra

    if current:
        pieces.append(" ".join(current))

    return pieces


def _units_for_chunking(text: str, chunk_size: int) -> List[str]:
    """Normalize text into units that each fit within chunk_size when possible."""
    units: List[str] = []
    for sentence in _split_sentences(text):
        if len(sentence) <= chunk_size:
            units.append(sentence)
        else:
            units.extend(_split_long_segment(sentence, chunk_size))
    return units


def _overlap_prefix(chunk: str, overlap: int) -> str:
    """
    Take text from the end of chunk for overlap with the next chunk.

    Prefers the longest suffix that starts on a sentence or word boundary and
    is at least ``overlap`` characters when possible; otherwise uses the
    shortest word-aligned suffix within the overlap window.
    """
    if overlap <= 0 or not chunk:
        return ""

    if len(chunk) <= overlap:
        return chunk

    min_start = len(chunk) - overlap
    best = ""

    for pattern in (r"(?<=[.!?])\s+", r"\s+"):
        for match in re.finditer(pattern, chunk):
            suffix = chunk[match.end() :].lstrip()
            if not suffix:
                continue
            if len(suffix) <= overlap and len(suffix) > len(best):
                best = suffix

    if best:
        return best

    start = min_start
    if start > 0 and not chunk[start - 1].isspace():
        last_space = chunk.rfind(" ", 0, start)
        if last_space != -1:
            start = last_space + 1

    return chunk[start:].lstrip()


def _unit_char_offsets(source: str, units: List[str]) -> List[int]:
    """Map each chunking unit to its first occurrence offset in ``source``."""
    offsets: List[int] = []
    search_from = 0
    for unit in units:
        idx = source.find(unit, search_from)
        if idx == -1:
            idx = search_from
        offsets.append(idx)
        search_from = max(search_from, idx + max(len(unit), 1))
    return offsets


def _chunk_impl(
    text: str, chunk_size: int = 500, overlap: int = 125
) -> List[ChunkSpan]:
    """Core chunking: sentence-aware spans with overlap and document offsets."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("chunk_size must be greater than overlap")

    if not text or not text.strip():
        return []

    stripped = text.strip()
    units = _units_for_chunking(stripped, chunk_size)
    if not units:
        return []

    unit_offsets = _unit_char_offsets(stripped, units)
    spans: List[ChunkSpan] = []
    index = 0
    prefix = ""

    while index < len(units):
        start_index = index
        parts: List[str] = []
        if prefix:
            parts.append(prefix)

        length = len(prefix)

        while index < len(units):
            unit = units[index]
            separator = 1 if parts else 0
            projected = length + separator + len(unit)

            if parts and projected > chunk_size:
                break

            if not parts and len(unit) > chunk_size:
                parts.append(unit)
                index += 1
                break

            if projected > chunk_size:
                break

            parts.append(unit)
            length = projected
            index += 1

        if not parts:
            break

        chunk = " ".join(parts).strip()
        if not chunk:
            break

        position_index = start_index
        if prefix and index > start_index:
            position_index = start_index + 1
        char_start = (
            unit_offsets[position_index]
            if position_index < len(unit_offsets)
            else 0
        )

        spans.append({"text": chunk, "char_start": char_start})

        if index >= len(units):
            break

        prefix = _overlap_prefix(chunk, overlap)
        if index == start_index:
            prefix = ""

    return spans


def chunk_text_with_spans(
    text: str, chunk_size: int = 500, overlap: int = 125
) -> List[ChunkSpan]:
    """
    Split text into overlapping chunks with character offsets.

    Default sizing targets 400–600 character chunks with 100–150 character overlap.
    """
    return _chunk_impl(text, chunk_size=chunk_size, overlap=overlap)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 125) -> List[str]:
    """
    Split text into overlapping chunks sized by character count.

    Chunks are built from sentences when possible; long sentences are split on
    word boundaries. Consecutive chunks share up to ``overlap`` characters from
    the end of the previous chunk, aligned to a sentence or word boundary when
    feasible.
    """
    return [span["text"] for span in _chunk_impl(text, chunk_size, overlap)]
