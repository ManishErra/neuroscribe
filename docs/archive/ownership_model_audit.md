# Ownership Model Audit

This document audits the current database schema and API route design of NeuroScribe to identify security vulnerabilities, potential HIPAA violations (cross-user data exposure), and query isolation gaps. It provides a formal analysis and final recommendation for securing each clinical entity.

---

## 1. Direct vs. Inherited Ownership Analysis

To transition NeuroScribe from a single-user system to a multi-clinician model, we must establish how clinical records are partitioned. The table below evaluates whether each table should store a direct `owner_id` column (referencing `users.id`) or inherit ownership transitively through foreign key relationships.

| Entity | Current Foreign Keys | Proposed Ownership Model | Justification | Final Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **patients** | None | **Direct `owner_id`** | Patients are the root entity of the clinical data graph. A patient has no parent table from which they could inherit ownership. They must be directly associated with the clinician who manages their case. | **Direct** |
| **sessions** | `patient_id` | **Inherited** | Sessions are child records of patients. Ownership can be resolved transitively by joining the `patients` table and verifying `patients.owner_id`. Storing a duplicate `owner_id` on sessions violates database normalization (3NF) and increases schema maintenance overhead. | **Inherited** (via `patient_id`) |
| **transcripts** | `session_id` | **Inherited** | Transcripts are 1-to-1 children of sessions. Storing a direct `owner_id` is redundant. Restricting access to the parent session transitively restricts access to the transcript. | **Inherited** (via `session_id`) |
| **notes** | `session_id` | **Inherited** | Clinical notes (both AI draft and doctor edited) belong directly to a session. Ownership is inherited through the session. Safe transitive joins prevent any unauthorized leaks. | **Inherited** (via `session_id`) |
| **reports** | `patient_id` | **Inherited** | Reports (diagnostic PDFs, lab summaries) are uploaded under a specific patient. Ownership is inherited from the patient. Access control queries should join `patients` to verify ownership. | **Inherited** (via `patient_id`) |
| **embeddings** | `source_id` | **Hybrid (Direct/Query-Scoped)** | Embeddings are used for vector retrieval. Storing them in the database pgvector table with inherited joins would require multiple SQL joins (`embeddings -> notes/reports -> patients`) on every similarity search, degrading performance. Storing a direct `owner_id` on PostgreSQL `embeddings` allows fast database-level filtering. For local FAISS vector search, ownership must be query-scoped (filtered by owner's report list in memory). | **Direct (pgvector table) & Query-Scoped (local FAISS index)** |

---

## 2. Router-by-Router Authorization Audit

Currently, all clinical endpoints in the backend use `Depends(get_current_user)` at the router level. However, **none of the handlers verify that the authenticated user owns the record they are accessing**. Any user with a valid JWT token can access or modify another user's clinical data if they know the UUID.

Below is a detailed audit of the vulnerability in each clinical handler:

### Patients Router (`backend/routers/patients.py`)
*   `GET /patients/`: Fetches **all** patients in the database, regardless of which doctor created them.
*   `GET /patients/{patient_id}`: Fetches the patient record for *any* UUID, without verifying that the requesting user created or owns the patient.
*   `POST /patients/`: Creates a patient without associating an owner.
*   `DELETE /patients/{patient_id}`: Allows any authenticated clinician to delete another clinician's patient.

### Sessions Router (`backend/routers/sessions.py`)
*   `GET /sessions/patient/{patient_id}`: Lists all sessions for any patient ID. An attacker could brute-force patient IDs to list clinical consultations.
*   `GET /sessions/{session_id}`: Returns the session details, raw transcript, and SOAP note for any session UUID, crossing clinical boundaries.
*   `POST /sessions/`: Creates a session for any patient ID without verifying that the doctor owns the patient.

### Audio Router (`backend/routers/audio.py`)
*   `POST /upload-audio`: Uploads audio and generates a transcript for any session ID, allowing unauthorized write access to clinical records.

### Notes Router (`backend/routers/notes.py`)
*   `POST /generate-note`: Generates a SOAP note draft for any session ID.
*   `POST /notes/save` / `POST /notes/finalize`: Saves or finalizes notes for any session ID.

### Reports Router (`backend/routers/reports.py`)
*   `POST /reports/`: Creates report metadata for any patient.
*   `POST /reports/upload`: Saves a diagnostic PDF on disk and database under any patient ID.
*   `POST /reports/{report_id}/ocr`: Runs Textract OCR and appends vector embeddings for any report ID.
*   `GET /reports/patient/{patient_id}`: Lists all medical reports for any patient ID.
*   `GET /reports/{report_id}`: Fetches the full OCR text and file path of any medical report.

### Clinical Timeline & Comparison Routers (`backend/routers/timeline.py`, `backend/routers/comparison.py`, `backend/patient_insights.py`)
*   `GET /timeline/{patient_id}`: Returns the chronological timeline of sessions and reports for any patient.
*   `GET /compare/{patient_id}`: Computes laboratory changes over time for any patient.
*   `GET /patient-overview/{patient_id}`: Generates high-level alerts and key labs summaries for any patient.
*   `GET /patient-insights/{patient_id}`: Runs LLM-based cohort analysis and diagnostic summaries.

---

## 3. Scoped Vector Retrieval and RAG Scoping

One of the most critical vulnerabilities resides in the semantic search and RAG QA pipelines, which retrieve vector chunks globally.

### Database pgvector Search (`backend/embeddings.py`)
The `search_similar` function executes a pgvector cosine distance query:
```sql
SELECT e.chunk_text, e.source_id, s.session_date
FROM embeddings e
LEFT JOIN notes n ON e.source_id = n.id
LEFT JOIN sessions s ON n.session_id = s.id
WHERE s.patient_id = :patient_id
```
While this query is scoped to `patient_id`, the router `POST /embed/note` does not verify if the requesting doctor owns the patient. Additionally, joining `notes`, `sessions`, and `patients` to verify ownership on every vector search causes performance degradation on large datasets.
*   **Audit Recommendation**: Add a direct `owner_id` column to the `embeddings` table and filter directly: `WHERE e.owner_id = :owner_id AND s.patient_id = :patient_id`.

### Local FAISS Search (`backend/report_vector_store.py`)
The `search_similar_chunks` function queries a local on-disk FAISS index containing all report chunk embeddings for all patients globally:
```python
scores, indices = _index.search(query_vec, candidate_k)
```
This is a **global vector search**. Currently, the retrieved chunks are formatted and returned without checking if the reports belong to the requesting doctor's patients. A doctor querying `/ask/` could get synthesis answers and direct citations from another doctor's private patient files.
*   **Audit Recommendation (Query-Scoped Filtering)**: 
    1. Fetch the list of authorized `report_ids` belonging to the authenticated clinician's patients from the SQL database.
    2. Pass this list/set of allowed report IDs to `search_similar_chunks`.
    3. During the retrieval filter loop, discard any candidate hit that does not belong to the allowed reports:
       ```python
       if allowed_report_ids is not None and meta["report_id"] not in allowed_report_ids:
           continue
       ```
    This guarantees absolute data isolation without needing to partition physical FAISS files on disk.
