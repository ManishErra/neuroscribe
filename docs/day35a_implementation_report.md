# Day 35A Implementation Report

This report documents the architectural and code changes made to enforce clinician-level data isolation (User-Patient Ownership Model) across the NeuroScribe backend codebase.

---

## 1. SQLAlchemy Model Changes (`backend/models.py`)

To support user association at the application database layer, the following models were updated:

*   **`Patient`**: Added the `owner_id` column.
    ```python
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    ```
*   **`Embedding`**: Added the `owner_id` column to pgvector embeddings to support direct, join-free isolation during similarity search queries.
    ```python
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    ```
*   **`User`**: Added a boolean flag `force_password_reset` to support security-first account backfills for legacy users.
    ```python
    force_password_reset = Column(Boolean, default=False, nullable=False)
    ```

---

## 2. Router Query Scoping Modifications

All clinical route handlers were updated to capture the authenticated `current_user` object via FastAPI Dependency Injection (`Depends(get_current_user)`) and filter all SQL query executions.

### Patients Router (`backend/routers/patients.py`)
*   **GET `/patients/`**: Filtered patients list by owner.
    `db.query(Patient).filter(Patient.owner_id == current_user.id)`
*   **GET `/patients/{patient_id}`**: Restricts retrieval.
    `db.query(Patient).filter(Patient.id == patient_id, Patient.owner_id == current_user.id)`
*   **POST `/patients/`**: Sets the `owner_id` to `current_user.id` upon record creation.
*   **DELETE `/patients/{patient_id}`**: Blocks deleting other clinician's patients.
    `db.query(Patient).filter(Patient.id == patient_id, Patient.owner_id == current_user.id)`

### Sessions Router (`backend/routers/sessions.py`)
*   **GET `/sessions/patient/{patient_id}`**: Checks patient ownership before listing consultation sessions.
*   **GET `/sessions/{session_id}`**: Restricts session details, raw transcripts, and SOAP notes. Checks patient ownership.
*   **POST `/sessions/`**: Verifies patient ownership before allowing a new session creation.

### Audio Router (`backend/routers/audio.py`)
*   **POST `/upload-audio`**: Verifies that the session's patient belongs to the logged-in clinician before allowing Whisper uploads and transcription saves.

### Notes Router (`backend/routers/notes.py`)
*   **POST `/generate-note`**: Validates transcript ownership before generating a SOAP note draft.
*   **POST `/save-note`**: Validates note ownership. In addition, the raw SQL statement inserting note chunks into pgvector `embeddings` was updated to insert `owner_id` to prevent `NotNullViolation` errors.
    ```sql
    INSERT INTO embeddings (..., owner_id) VALUES (..., :owner_id)
    ```

### Reports Router (`backend/routers/reports.py`)
*   **POST `/reports/`** & **POST `/reports/upload`**: Validates target patient ownership before creating metadata or saving diagnostic PDFs.
*   **POST `/reports/{report_id}/ocr`**: Restricts Textract OCR execution and FAISS vector index additions to owned documents.
*   **GET `/reports/patient/{patient_id}`**: Restricts files listing.
*   **GET `/reports/{report_id}`**: Restricts parsed OCR previews.

### Timeline, Comparison, & Insights Routers
*   **GET `/timeline/{patient_id}`** (`backend/routers/timeline.py`): Restricts timeline event tracking.
*   **GET `/compare/{patient_id}`** (`backend/routers/comparison.py`): Restricts lab comparison.
*   **GET `/patient-insights/{patient_id}`** & **GET `/patient-overview/{patient_id}`** (`backend/patient_insights.py`): Scopes AI overview cards and clinical cohort analysis to the authenticated owner.

### Embed Router (`backend/routers/embed.py`)
*   **POST `/embed/note`**: Verifies note ownership and writes `owner_id` to the inserted embeddings rows.
