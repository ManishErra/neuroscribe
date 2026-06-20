#!/usr/bin/env python3
"""
Day 37C Verification Script — RAG & FAISS Deletion Pipeline
============================================================
Verifies the FAISS vector store deletion protocol without touching
the production database (no database.py import).

Tests:
  T01 — Vector store initializes with correct dimension
  T02 — Adding vectors increases ntotal and metadata list equally
  T03 — remove_vectors_for_report removes correct count
  T04 — Index/metadata integrity: ntotal == len(metadata) post-deletion
  T05 — Deleted report_id chunks are absent from metadata post-deletion
  T06 — Surviving report_id chunks remain intact post-deletion
  T07 — search_similar_chunks never returns deleted-report chunks
  T08 — Deleting non-existent report returns 0 (idempotent)
  T09 — save/load cycle preserves integrity after deletion
  T10 — Empty transcript → no vectors added (boundary condition)

Usage:
  cd backend
  python scripts/run_day37c_verification.py
"""

import sys
import os
import json
import tempfile

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
results = []


def record(test_id: str, name: str, status: str, detail: str = ""):
    icon = "✅" if status == PASS else ("⚠️" if status == SKIP else "❌")
    results.append({"id": test_id, "name": name, "status": status, "detail": detail})
    print(f"  {icon} [{status}] {test_id}: {name}" + (f" — {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────────
# ISOLATION: Redirect FAISS on-disk paths to a temp dir so tests don't
# touch the production vector.index / vector_metadata.json files.
# ─────────────────────────────────────────────────────────────────────────────
import report_vector_store as rvs
import numpy as np

_tmpdir = tempfile.mkdtemp(prefix="day37c_test_")
_orig_index_path = rvs.VECTOR_INDEX_PATH
_orig_metadata_path = rvs.VECTOR_METADATA_PATH
rvs.VECTOR_INDEX_PATH = os.path.join(_tmpdir, "test_vector.index")
rvs.VECTOR_METADATA_PATH = os.path.join(_tmpdir, "test_vector_metadata.json")

# Helpers to inject synthetic embeddings without real model calls
FAKE_DIM = 384

def _fake_embedding(seed: int = 42) -> list:
    rng = np.random.default_rng(seed)
    vec = rng.random(FAKE_DIM).astype(np.float32)
    vec /= np.linalg.norm(vec)
    return vec.tolist()


def _inject_report(report_id: str, n_chunks: int, owner_id: str = "owner-A"):
    """Directly inject synthetic vectors and metadata (bypasses OCR/embedding model)."""
    import faiss

    vectors = np.array([_fake_embedding(i + hash(report_id) % 1000) for i in range(n_chunks)], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors /= norms

    if rvs._index is None:
        rvs._index = faiss.IndexFlatIP(FAKE_DIM)

    rvs._index.add(vectors)
    for i in range(n_chunks):
        rvs._chunk_metadata.append({
            "report_id": report_id,
            "chunk_index": i,
            "chunk_text": f"Synthetic chunk {i} for {report_id}",
            "chunk_length": 60,
            "owner_id": owner_id,
        })


# ─────────────────────────────────────────────────────────────────────────────
print("\n=== DAY 37C — FAISS DELETION VERIFICATION ===\n")
# ─────────────────────────────────────────────────────────────────────────────

# T01 — Initialize
try:
    rvs.initialize_vector_store(FAKE_DIM)
    ok = rvs._index is not None and rvs._index.ntotal == 0 and rvs._index.d == FAKE_DIM
    record("T01", "Vector store initializes empty with correct dimension", PASS if ok else FAIL,
           f"ntotal={rvs._index.ntotal}, dim={rvs._index.d}")
except Exception as e:
    record("T01", "Vector store initializes empty with correct dimension", FAIL, str(e))

# T02 — Add vectors → ntotal and metadata stay in sync
try:
    rvs.initialize_vector_store(FAKE_DIM)
    _inject_report("report-A", 3)
    _inject_report("report-B", 2)
    ntotal = rvs._index.ntotal
    meta_len = len(rvs._chunk_metadata)
    ok = ntotal == 5 and meta_len == 5
    record("T02", "Adding vectors keeps ntotal == len(metadata)", PASS if ok else FAIL,
           f"ntotal={ntotal}, meta_len={meta_len}")
except Exception as e:
    record("T02", "Adding vectors keeps ntotal == len(metadata)", FAIL, str(e))

# T03 — remove_vectors_for_report returns correct count
try:
    removed = rvs.remove_vectors_for_report("report-A")
    ok = removed == 3
    record("T03", "remove_vectors_for_report returns correct removal count", PASS if ok else FAIL,
           f"removed={removed}, expected=3")
except Exception as e:
    record("T03", "remove_vectors_for_report returns correct removal count", FAIL, str(e))

# T04 — ntotal == len(metadata) after deletion
try:
    ntotal = rvs._index.ntotal
    meta_len = len(rvs._chunk_metadata)
    ok = ntotal == meta_len == 2
    record("T04", "Index/metadata integrity: ntotal == len(metadata) post-deletion", PASS if ok else FAIL,
           f"ntotal={ntotal}, meta_len={meta_len}, expected=2")
except Exception as e:
    record("T04", "Index/metadata integrity: ntotal == len(metadata) post-deletion", FAIL, str(e))

# T05 — Deleted report's chunks absent from metadata
try:
    remaining_ids = {m["report_id"] for m in rvs._chunk_metadata}
    ok = "report-A" not in remaining_ids
    record("T05", "Deleted report chunks absent from metadata", PASS if ok else FAIL,
           f"remaining_report_ids={remaining_ids}")
except Exception as e:
    record("T05", "Deleted report chunks absent from metadata", FAIL, str(e))

# T06 — Surviving report chunks intact
try:
    remaining_ids = {m["report_id"] for m in rvs._chunk_metadata}
    surviving_count = sum(1 for m in rvs._chunk_metadata if m["report_id"] == "report-B")
    ok = "report-B" in remaining_ids and surviving_count == 2
    record("T06", "Surviving report chunks remain intact post-deletion", PASS if ok else FAIL,
           f"surviving_count={surviving_count}")
except Exception as e:
    record("T06", "Surviving report chunks remain intact post-deletion", FAIL, str(e))

# T07 — search never returns deleted-report chunks
try:
    # Inject a third known-owner report, then delete report-A (already gone) and search
    rvs.initialize_vector_store(FAKE_DIM)
    _inject_report("rep-X", 3, "owner-1")
    _inject_report("rep-Y", 2, "owner-1")
    rvs.remove_vectors_for_report("rep-X")

    # Patch generate_embedding to return a deterministic vector
    import unittest.mock as mock
    fake_vec = _fake_embedding(0)
    with mock.patch("report_vector_store.generate_embedding", return_value=fake_vec):
        with mock.patch("report_vector_store.prepare_text_for_embedding", return_value="test"):
            hits = rvs.search_similar_chunks("test", top_k=10, owner_id="owner-1")

    for_deleted = [h for h in hits if h["report_id"] == "rep-X"]
    ok = len(for_deleted) == 0
    record("T07", "search_similar_chunks never returns deleted-report chunks", PASS if ok else FAIL,
           f"hits_for_deleted={len(for_deleted)}, total_hits={len(hits)}")
except Exception as e:
    record("T07", "search_similar_chunks never returns deleted-report chunks", FAIL, str(e))

# T08 — Deleting non-existent report is idempotent (returns 0)
try:
    rvs.initialize_vector_store(FAKE_DIM)
    _inject_report("rep-Z", 2)
    removed = rvs.remove_vectors_for_report("rep-NONEXISTENT")
    ok = removed == 0 and rvs._index.ntotal == 2
    record("T08", "Deleting non-existent report returns 0 (idempotent)", PASS if ok else FAIL,
           f"removed={removed}")
except Exception as e:
    record("T08", "Deleting non-existent report returns 0 (idempotent)", FAIL, str(e))

# T09 — Save/load cycle preserves integrity after deletion
try:
    rvs.initialize_vector_store(FAKE_DIM)
    _inject_report("rep-save-A", 4, "owner-persist")
    _inject_report("rep-save-B", 3, "owner-persist")
    rvs.remove_vectors_for_report("rep-save-A")
    rvs.save_vector_store()

    # Reset globals and reload from disk
    rvs._index = None
    rvs._chunk_metadata = []
    rvs.load_vector_store()

    ntotal = rvs._index.ntotal
    meta_len = len(rvs._chunk_metadata)
    ok = ntotal == meta_len == 3
    record("T09", "Save/load cycle preserves integrity after deletion", PASS if ok else FAIL,
           f"ntotal={ntotal}, meta_len={meta_len}, expected=3")
except Exception as e:
    record("T09", "Save/load cycle preserves integrity after deletion", FAIL, str(e))

# T10 — Empty report text → 0 vectors added
try:
    rvs.initialize_vector_store(FAKE_DIM)
    before = rvs._index.ntotal
    # build_report_embeddings returns [] for empty text (verified in report_embeddings.py)
    import report_embeddings
    result = report_embeddings.build_report_embeddings("")
    ok = result == [] and rvs._index.ntotal == before
    record("T10", "Empty report text produces 0 embeddings (boundary condition)", PASS if ok else FAIL,
           f"embeddings={len(result)}")
except Exception as e:
    record("T10", "Empty report text produces 0 embeddings (boundary condition)", FAIL, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# Restore production paths
rvs.VECTOR_INDEX_PATH = _orig_index_path
rvs.VECTOR_METADATA_PATH = _orig_metadata_path
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== PASS/FAIL MATRIX ===\n")
print(f"{'ID':<6} {'Name':<60} {'Status'}")
print("-" * 80)
total = len(results)
passed = sum(1 for r in results if r["status"] == PASS)
failed = sum(1 for r in results if r["status"] == FAIL)
skipped = sum(1 for r in results if r["status"] == SKIP)

for r in results:
    status_icon = "✅ PASS" if r["status"] == PASS else ("⚠️ SKIP" if r["status"] == SKIP else "❌ FAIL")
    print(f"{r['id']:<6} {r['name'][:60]:<60} {status_icon}")

print("-" * 80)
print(f"\nTotal: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}")

if failed > 0:
    print("\n❌ DAY 37C VERIFICATION: FAILED")
    sys.exit(1)
else:
    print("\n✅ DAY 37C VERIFICATION: PASSED")
    sys.exit(0)
