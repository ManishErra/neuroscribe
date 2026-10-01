# Final Day 35 Architecture Review

This document provides the final architectural review for the Day 35 User-Patient Ownership Model migration. It synthesizes ownership strategies, FAISS vector store metadata validation, and the security risk matrix.

---

## 1. Ownership Decision Summary

Below is the architectural analysis and final recommendation for partitioning and isolating each clinical entity:

### patients
*   **Final Recommendation**: **Direct `owner_id`**
*   **Query Complexity**: **Low (O(1))**. Simple database filtering: `WHERE owner_id = :current_user_id`. No SQL joins required.
*   **Index Requirements**: B-tree index on `patients(owner_id)`.
*   **Maintenance Impact**: Extremely low. Set once at creation.
*   **Security Implications**: **Critical**. Establishes the perimeter gate for the entire clinical record graph. All access-control checks for child entities flow from this association.

### sessions
*   **Final Recommendation**: **Inherited ownership** (via `patient_id -> patients.id`)
*   **Query Complexity**: **Medium**. Requires joining the `patients` table:
    `JOIN patients p ON sessions.patient_id = p.id WHERE p.owner_id = :current_user_id`.
*   **Index Requirements**: B-tree index on `sessions(patient_id)`.
*   **Maintenance Impact**: Low. Adheres to standard relational normalization (3NF) and prevents duplicate/drifting constraints.
*   **Security Implications**: High. Securely isolated transitively through the parent patient check.

### transcripts
*   **Final Recommendation**: **Inherited ownership** (via `session_id -> sessions.id`)
*   **Query Complexity**: **Medium**. Transitive query through sessions:
    `JOIN sessions s ON transcripts.session_id = s.id JOIN patients p ON s.patient_id = p.id WHERE p.owner_id = :current_user_id`.
*   **Index Requirements**: B-tree index on `transcripts(session_id)`.
*   **Maintenance Impact**: Low. Normalized data architecture.
*   **Security Implications**: Medium. Inherited path is structurally secure.

### notes
*   **Final Recommendation**: **Inherited ownership** (via `session_id -> sessions.id`)
*   **Query Complexity**: **Medium**. Joins through sessions to patients.
*   **Index Requirements**: B-tree index on `notes(session_id)`.
*   **Maintenance Impact**: Low. Keeps schema normalized.
*   **Security Implications**: **Critical**. SOAP notes are sensitive clinical data; access is gated transitively through session ownership.

### reports
*   **Final Recommendation**: **Inherited ownership** (via `patient_id -> patients.id`)
*   **Query Complexity**: **Medium**. Join with `patients` to verify ownership.
*   **Index Requirements**: B-tree index on `reports(patient_id)`.
*   **Maintenance Impact**: Low. Normalized structure.
*   **Security Implications**: High. Contains diagnostic PDFs and parsed OCR text; secured via patient ownership checks.

### embeddings
*   **Final Recommendation**: **Hybrid (Direct on pgvector, Query-Scoped on FAISS)**
*   **Query Complexity**: 
    *   *pgvector*: Low query complexity. Adding direct `owner_id` allows direct filtering (`WHERE e.owner_id = :owner_id`) during expensive cosine distance queries.
    *   *FAISS*: Global vector search followed by in-memory filtering against authorized patient report IDs.
*   **Index Requirements**: B-tree index on pgvector table `embeddings(owner_id)`.
*   **Maintenance Impact**: Medium. Requires maintaining `owner_id` consistency on embedding additions and deletion cascades.
*   **Security Implications**: **Critical**. Ensures that vector search does not leak semantic information across clinician boundaries.

---

## 2. FAISS Metadata Validation Review

### Current Metadata Structure (`vector_metadata.json`)
Currently, chunks are mapped to `report_id` only:
```json
[
  {
    "report_id": "51773efc-479b-469d-931d-cd483786c20e",
    "chunk_index": 0,
    "chunk_text": "Patient Hemoglobin count is normal at 14.5 g/dL...",
    "chunk_length": 50,
    "report_source": "51773efc-479b-469d-931d-cd483786c20e",
    "chunk_position": 0
  }
]
```

### Proposed Metadata Structure
We inject `owner_id` to enforce fast database-free filtering:
```json
[
  {
    "report_id": "51773efc-479b-469d-931d-cd483786c20e",
    "owner_id": "d35e8400-e29b-41d4-a716-446655440000",
    "chunk_index": 0,
    "chunk_text": "Patient Hemoglobin count is normal at 14.5 g/dL...",
    "chunk_length": 50,
    "report_source": "51773efc-479b-469d-931d-cd483786c20e",
    "chunk_position": 0
  }
]
```

### Migration Steps
1.  Query SQL database to construct a mapping dictionary: `report_id -> owner_id`.
2.  Read the existing `vector_metadata.json` file.
3.  Loop through metadata objects, lookup their `report_id`, and inject `"owner_id": "<UUID>"`.
4.  Write to `vector_metadata.json.tmp` and replace the original file atomically.

### Why metadata patching is safe:
*   It alters only the metadata JSON file, which is separate from the binary FAISS index file.
*   The data modification is deterministic, preserves existing properties, and can be dry-run.

### Why re-embedding is not required:
*   Vectors represent semantic text representations of `chunk_text` which is unaltered. Re-calculating them would yield the exact same floats and consume unnecessary resources.

---

## 3. Migration Risk Matrix

| Risk Area | Risk Level | Description | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Schema Migration** | **Medium** | Database lock contention when applying foreign key constraints on `patients`. | Set a local lock timeout (`SET local lock_timeout = '2s';`). Add column as nullable, backfill data, and alter to `NOT NULL` in a single transaction during off-peak hours. |
| **Orphan Cleanup** | **Low** | Deleting orphaned transcripts (12) and notes (8) could lead to unintended data loss. | Verify that the orphans are indeed invalid development records. Clean them or assign them to a dummy session before applying constraints. |
| **Owner Backfill** | **Medium** | Exposure of legacy owner credentials if insecure passwords or pre-computed hashes are committed. | Generate a cryptographically secure random 32-character password using Python's `secrets` module at migration runtime, hash it with `bcrypt` on the fly, and flag the account for an immediate forced password reset. |
| **Router Query Scoping** | **High** | Oversight leaving an endpoint (e.g. `/sessions/{id}`) without user-scoping, permitting authorization bypass. | Enforce line-by-line code review of all 10 clinical modules. Execute the updated integration isolation test script (`run_day35_verification.py`) immediately post-deploy. |
| **FAISS Ownership Filtering**| **High** | Candidate chunks from another doctor leaking into RAG Q&A responses because FAISS is queried globally. | Enforce strict query-scoped filtering inside `/ask` router. Pass the current user's ID to `search_similar_chunks` and discard any vector matches that do not match the requesting user's `owner_id`. |

---

## 4. Final Recommendation

Based on the completed audit, migration hardening DDL, rollback safety checks, and the risk matrix:

**APPROVED FOR DAY 35A IMPLEMENTATION**
