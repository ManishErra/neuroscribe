# Day 35B FAISS Ownership Isolation Final Pre-Implementation Report (Revised)

This report defines the final implementation plan, algorithms, backup policies, validation strategies, and verification matrices for the Day 35B FAISS Ownership Isolation phase.

---

## 1. Search Layer Enforcement (Security Boundary)

To isolate the file-based FAISS vector store, all semantic searches must be strictly scoped to the requesting clinician. 

### A. Identification of Target Files & Functions:
*   **Vector Query Core**: [`backend/report_vector_store.py`](file:///c:/Users/Manish/AI-Projects/neuroscribe/backend/report_vector_store.py)
    *   **Core Function**: `search_similar_chunks` (the exact function where FAISS search results are retrieved, filtered, and returned to downstream callers).
*   **Search Request Router**: [`backend/routers/search.py`](file:///c:/Users/Manish/AI-Projects/neuroscribe/backend/routers/search.py)
    *   **Router Function**: `ask_question` (the FastAPI route handler matching `POST /ask/` that handles user-facing question-answering).

### B. Ownership Filtering Principle & Constraints:
The security model mandates a strict identity check at the vector retrieval level. The system must explicitly enforce that:
> [!IMPORTANT]
> **NO FAISS search result (chunk) may be returned from a semantic search query unless it satisfies the following check:**
> $$\text{chunk["owner\_id"]} == \text{current\_user.id}$$
> If a chunk fails this equality check, it must be completely excluded from the result list.

### C. Show Where Owner Filtering Will Occur:
Ownership filtering will occur within `search_similar_chunks` in [`backend/report_vector_store.py`](file:///c:/Users/Manish/AI-Projects/neuroscribe/backend/report_vector_store.py) at the beginning of the candidate processing loop. After `_index.search()` returns the top candidates, the function loops through the candidate indices, loads each chunk's metadata, and evaluates `chunk["owner_id"]` against the passed `owner_id`. If they do not match, the chunk is silently skipped, preventing it from entering the keyword boost calculations or the final returned list.

### D. Planned Scoping Algorithm:

#### 1. In [`backend/report_vector_store.py`](file:///c:/Users/Manish/AI-Projects/neuroscribe/backend/report_vector_store.py):
```python
def search_similar_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    *,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    owner_id: Optional[str] = None, # Enforce ownership boundary
) -> List[SimilarChunkResult]:
    """
    Hybrid semantic + keyword boosted retrieval, scoped to the current owner.
    """
    # ... [Embedding generation and search on FAISS IndexFlatIP] ...
    scores, indices = _index.search(query_vec, candidate_k)
    
    results: List[SimilarChunkResult] = []
    seen_chunks = set()
    
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
            
        meta = _chunk_metadata[idx]
        
        # CRITICAL OWNERSHIP ISOLATION GATE:
        # Enforce that no chunk is returned unless owner_id matches.
        if owner_id is not None:
            chunk_owner = meta.get("owner_id")
            if chunk_owner is None or str(chunk_owner) != str(owner_id):
                continue # Skip chunk entirely to prevent leaks
                
        # De-duplicate by normalized chunk text
        norm_text = " ".join(meta["chunk_text"].lower().split())
        if norm_text in seen_chunks:
            continue
        seen_chunks.add(norm_text)
        
        # ... [process similarity score, keyword/hemoglobin boosts, and final filtering] ...
```

#### 2. In [`backend/routers/search.py`](file:///c:/Users/Manish/AI-Projects/neuroscribe/backend/routers/search.py):
```python
@router.post("/")
def ask_question(
    request: AskRequest,
    current_user: User = Depends(get_current_user), # Retrieve JWT authenticated clinician
):
    # STEP 1 — retrieve relevant chunks, filtering by the requesting user's ID
    results = search_similar_chunks(
        query=request.question,
        top_k=request.top_k,
        owner_id=str(current_user.id),
    )
    # ... [remain unchanged] ...
```


---

## 2. Final Migration Algorithm (Loud Failure & Hardened Checks)

The FAISS metadata migration will be executed by a dedicated Python script `backend/scripts/migrate_faiss_metadata.py`. It enforces strict validation, loud exceptions on missing mappings, and atomic file replacements.

```python
import json
import shutil
from pathlib import Path
from sqlalchemy import text
from database import SessionLocal

def run_faiss_metadata_migration():
    metadata_path = Path("backend/vector_metadata.json")
    backup_path = Path("backend/vector_metadata.backup.json")
    tmp_path = Path("backend/vector_metadata.json.tmp")
    
    print("--- Starting Day 35B FAISS Metadata Migration ---")
    
    # STEP 1: Verify file exists
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Source metadata file not found at: {metadata_path}")
        
    # STEP 2: Automatic Backup Strategy
    print(f"Creating metadata backup: {backup_path}")
    shutil.copy2(metadata_path, backup_path)
    
    # STEP 3: Load existing metadata
    with open(metadata_path, "r") as f:
        chunks = json.load(f)
    original_count = len(chunks)
    print(f"Loaded {original_count} original metadata chunks.")
    
    # STEP 4: Query Database Mappings
    db = SessionLocal()
    mapping = {}
    try:
        query = "SELECT r.id, p.owner_id FROM reports r JOIN patients p ON r.patient_id = p.id"
        rows = db.execute(text(query)).fetchall()
        for r_id, owner_id in rows:
            mapping[str(r_id)] = str(owner_id)
        print(f"Loaded {len(mapping)} active report-to-owner mappings from database.")
    except Exception as e:
        db.close()
        raise RuntimeError(f"Database query failed during mapping fetch: {e}")
    finally:
        db.close()
        
    # STEP 5: Patch Chunks In-Memory (Loud Failure Enforcement)
    patched_chunks = []
    for idx, chunk in enumerate(chunks):
        r_id = chunk.get("report_id") or chunk.get("report_source")
        if not r_id:
            raise RuntimeError(f"Defect found: Metadata chunk at index {idx} has no report identifier.")
            
        r_id_str = str(r_id)
        
        # Loud failure if database has no owner mappings for the report
        if r_id_str not in mapping:
            raise RuntimeError(
                f"LOUD MIGRATION FAILURE: Database contains no ownership records for report_id '{r_id_str}' "
                f"at metadata index {idx}. Fallback is disabled."
            )
            
        # Patch chunk dictionary
        chunk["owner_id"] = mapping[r_id_str]
        patched_chunks.append(chunk)
        
    # STEP 6: Validate Chunk Counts Match Exactly
    patched_count = len(patched_chunks)
    if original_count != patched_count:
        raise RuntimeError(
            f"LOUD MIGRATION FAILURE: Patched count ({patched_count}) does not match "
            f"original count ({original_count}). Aborting replacement."
        )
    print(f"Validation successful: Patched chunk count matches original count ({patched_count}).")
    
    # STEP 7: Atomic Write Replacement
    with open(tmp_path, "w") as f:
        json.dump(patched_chunks, f, indent=2)
    tmp_path.replace(metadata_path)
    
    print("Day 35B FAISS Metadata Migration completed successfully!")
```

> [!NOTE]
> **Hardening Note on Atomic Replacement**: Metadata file replacement must be atomic to prevent data corruption or partial writes in case of runtime interruptions. The migration script writes the patched metadata array into a temporary file (`vector_metadata.json.tmp`) and then calls `Path.replace()` (which under the hood uses the atomic `os.replace` syscall on both POSIX and Windows systems) to swap the files instantaneously.

---

## 3. Rollback Algorithm

If the application fails on boot or encounters schema/data errors after applying Day 35B, the rollback procedure is defined as follows:

1.  **Stop application server** to prevent write actions.
2.  **Restore the backup file**:
    ```python
    import shutil
    from pathlib import Path
    
    backup_path = Path("backend/vector_metadata.backup.json")
    metadata_path = Path("backend/vector_metadata.json")
    
    if backup_path.is_file():
        shutil.copy2(backup_path, metadata_path)
        print("Successfully rolled back FAISS metadata from backup.")
    else:
        raise FileNotFoundError("Rollback failed: vector_metadata.backup.json does not exist.")
    ```
3.  **Restore application code** by discarding local edits to `report_vector_store.py` and `routers/search.py`.
4.  **Re-launch application server**.

---

## 4. Post-Migration Verification Matrix

After applying the migration, a new verification script `backend/scripts/run_day35b_verification.py` will validate both existing records and the report upload/OCR pipeline path.

### A. Existing Metadata Verification (Static Check)
*   **Action**: Load `backend/vector_metadata.json`.
*   **Validation Checks**:
    *   Confirm total chunk count matches the baseline count (1152 chunks).
    *   Verify that **every** chunk has an `owner_id` attribute.
    *   Verify that **no** chunk has a `NULL` or missing `owner_id` attribute.
    *   Check that all `owner_id` values match valid user UUIDs in the `users` table.

### B. New Report Verification (Dynamic Ingestion & OCR Check)
*   **Action**: Log in as **Doctor A** (authenticated current user) and execute the full clinical ingestion pipeline:
    1.  Create a new patient **Patient C**.
    2.  Upload a new PDF report **Report C** for Patient C (`POST /reports/upload`).
    3.  Run OCR on Report C (`POST /reports/{id}/ocr`) to trigger OCR chunk generation and write to the vector store.
*   **Validation Checks**:
    1.  Load the vector store metadata file `backend/vector_metadata.json` and select all chunks where `report_id` (or `report_source`) matches Report C.
    2.  **Verify Chunk Count**:
        *   Verify that the count of generated chunks for Report C is **greater than 0** (`chunk count > 0`).
        *   > [!WARNING]
        *   **A report that generates zero chunks must be classified as FAIL.**
    3.  **Verify Field Completeness & Ownership**:
        *   Verify that **every generated chunk** contains a non-empty `report_id`.
        *   Verify that **every generated chunk** contains an `owner_id`.
        *   Verify that **every owner_id** in the generated chunks equals the authenticated clinician's ID (`owner_id == current_user.id`) exactly.
        *   If any chunk is missing either `report_id` or `owner_id`, or if the `owner_id` does not match `current_user.id`, classify the verification audit as **FAIL**.

### C. Multi-Clinician Search Isolation Check
*   **Action**: Log in as **Doctor B** and execute similarity search via `POST /ask/` with queries matching text in Doctor A's reports.
*   **Validation Check**:
    *   Confirm that Doctor B's response returns `No relevant medical context found.` and `chunks_used` is `[]` (empty list).

---

## 5. Verification Classification Rules

*   **PASS**: 
    1.  100% of the 1152 existing chunks have been successfully patched with correct clinician `owner_id` values.
    2.  New reports successfully generate `> 0` chunks and write matching `owner_id` values into the metadata file.
    3.  Doctor B cannot retrieve any of Doctor A's report chunks through global or semantic searches.
*   **FAIL**:
    *   Any chunk in the metadata file is missing an `owner_id`.
    *   Any chunk is mapped to an incorrect owner.
    *   Any search query leaks chunks across clinician boundaries.
    *   A newly uploaded report generates `0` vector chunks (or chunk count is not > 0).
    *   Any newly generated chunk is missing `report_id` or `owner_id`, or has an `owner_id` that is not equal to `current_user.id`.
