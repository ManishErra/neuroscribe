# Day 37C — FAISS Deletion Feasibility Audit

**Date:** 2026-06-20  
**Auditor:** Lead Engineer (Antigravity)  
**Scope:** Evaluate whether FAISS vector deletion is safe to implement in NeuroScribe production.

---

## 1. FAISS Index Type in Production

**Finding:** `IndexFlatIP`

```python
# report_vector_store.py line 94
_index: Optional[faiss.IndexFlatIP] = None
```

`IndexFlatIP` performs an exhaustive inner-product search over L2-normalized vectors for cosine similarity. It stores vectors as a flat array of `float32` values with no internal ID management — vectors are stored in insertion order, and their FAISS "index ID" is their ordinal position (0, 1, 2, ..., N-1).

---

## 2. Does `IndexFlatIP` Support `remove_ids`?

**Finding: YES, with critical caveats.**

FAISS `IndexFlat*` supports `remove_ids(IDSelectorArray)`. However, the implementation is:

```
IndexFlatIP → inherits from IndexFlat → inherits from IndexRefine
remove_ids performs a sequential scan and compacts the internal float array in-place.
```

**Critical behavior post-deletion:**

- FAISS renumbers all surviving vectors **sequentially** starting from 0.
- Any external mapping that uses the original ordinal position (the FAISS index ID) becomes **invalid** after deletion.
- NeuroScribe's `_chunk_metadata` list uses **positional indexing**: `meta = _chunk_metadata[idx]` (line 505 of `report_vector_store.py`).

This means: **if vector at position 3 is removed, the vector that was at position 4 becomes position 3**, but `_chunk_metadata[3]` still points to the old entry at position 3 — a **critical metadata desynchronization**.

---

## 3. Current Metadata Alignment Architecture

```python
# report_vector_store.py — retrieval path (line 500-505)
for score, idx in zip(scores[0], indices[0]):
    if idx < 0:
        continue
    meta = _chunk_metadata[idx]   # ← positional: FAISS idx == metadata list index
```

The current design assumes that `FAISS index position == _chunk_metadata list index`. This is guaranteed at insert time:

```python
_index.add(normalized)           # FAISS ordinal = len(_chunk_metadata) before append
for record in records:
    _chunk_metadata.append(...)  # metadata list grows in sync with FAISS
```

**After `remove_ids`:**  
FAISS compacts its internal array. The list `_chunk_metadata` is **not** automatically updated. Positional mapping breaks immediately unless a parallel compaction of `_chunk_metadata` is performed in the same transaction.

---

## 4. Deletion Survival: Save/Reload Cycle

**Finding: UNSAFE without synchronized save.**

Current `save_vector_store()` persists:
1. The FAISS `.index` file (post-compaction, renumbered)
2. The `_chunk_metadata` list as JSON (unchanged unless code explicitly modifies it)

If deletion is performed and the store is saved **without also compacting `_chunk_metadata`**, the on-disk state is corrupted: the next `load_vector_store()` will detect the mismatch via the integrity check:

```python
# load_vector_store() lines 359-368
if loaded_index.ntotal != len(metadata):
    logger.warning("Vector index mismatch (%s vs %s)", ...)
    initialize_vector_store()   # ← WIPES ENTIRE INDEX
    return
```

**This means a failed deletion would cause total data loss of the vector index on next restart.**

---

## 5. Retrieval Quality After Deletion

**Finding: Retrieval quality is preserved IF metadata alignment is maintained.**

`IndexFlatIP` is exhaustive — it searches all remaining vectors with no approximation. There is no inverted index, no cluster structure, and no graph that deletion could corrupt. Retrieval quality post-deletion is identical to a fresh re-insertion of only the surviving vectors.

The only risk to retrieval quality is the metadata misalignment risk described in sections 3 and 4. If metadata is correctly synchronized, retrieval quality is fully preserved.

---

## 6. Implementation Safety Assessment

| Check | Result | Risk |
|---|---|---|
| `IndexFlatIP` supports `remove_ids` | ✅ YES | — |
| Metadata survives positional compaction | ❌ REQUIRES synchronization | **CRITICAL** |
| Save/reload integrity check | ✅ Present (`ntotal != len(metadata)` → wipe) | Wipe = data loss |
| Retrieval quality after deletion | ✅ Preserved if metadata sync'd | — |
| Concurrent access safety | ⚠️ Module-level globals with no lock | Moderate |

---

## 7. Safe Deletion Protocol (If Approved for Implementation)

The following describes the **only safe approach** for FAISS vector deletion:

### Step 1 — Identify target FAISS positions

```python
def get_positions_for_report(report_id: str) -> list[int]:
    return [
        i for i, m in enumerate(_chunk_metadata)
        if m["report_id"] == report_id
    ]
```

### Step 2 — Remove from FAISS index atomically

```python
import faiss
id_selector = faiss.IDSelectorArray(np.array(positions, dtype=np.int64))
_index.remove_ids(id_selector)
```

### Step 3 — Compact `_chunk_metadata` in the same operation

```python
# Must happen in the exact same synchronous block as FAISS removal
positions_set = set(positions)
_chunk_metadata[:] = [
    m for i, m in enumerate(_chunk_metadata) if i not in positions_set
]
```

### Step 4 — Save immediately

```python
save_vector_store()   # persists both the compacted index and the compacted metadata list
```

### Step 5 — Verify integrity

```python
assert _index.ntotal == len(_chunk_metadata), "CRITICAL: metadata desync detected"
```

---

## 8. Verdict

> **FAISS vector deletion is feasible and safe ONLY when the synchronized deletion protocol (Steps 1–5 above) is followed atomically.**

**Conditions for implementation:**
1. All five steps must execute in a single synchronous code path — no async gaps between FAISS removal and metadata compaction.
2. The `save_vector_store()` integrity check already provides a self-healing fallback (wipe on mismatch), but this is a last resort and represents data loss.
3. The deletion function must be covered by verification tests confirming `_index.ntotal == len(_chunk_metadata)` post-deletion.

**Current production status:**  
`report_vector_store.py` does **not** implement deletion today. The `delete_report` endpoint in `routers/reports.py` deletes the DB record and file but leaves FAISS vectors as orphans.

---

## 9. Recommended Action

| Priority | Action |
|---|---|
| **Implement Now** | `remove_vectors_for_report(report_id)` function in `report_vector_store.py` using the safe protocol above |
| **Hook into** | `DELETE /reports/{report_id}` endpoint |
| **Add verification** | `run_day37c_verification.py` must confirm ntotal integrity before and after |

---

## 10. Remaining Limitation (After Implementation)

Even after implementing safe deletion:
- FAISS is a **local disk-based store** with no distributed locking.
- In a multi-process deployment (e.g., Gunicorn with multiple workers), two processes maintaining separate `_index` and `_chunk_metadata` globals will diverge if one process deletes while another reads. This is a known production scalability gap.
- **Mitigation:** Single-worker Uvicorn deployment (current), or migration to pgvector for multi-worker safety.
