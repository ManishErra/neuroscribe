# Expanded Verification Matrix

This document defines the comprehensive test matrix to verify clinician-level data isolation, RAG scoping, and schema protection. It ensures that after the implementation of the Day 35 User-Patient Ownership Model, clinicians are restricted exclusively to their own patient records.

---

## 1. Backend API Integration Isolation Matrix

The backend verification suite will test the security perimeter across all clinical endpoints. In these tests, **Doctor A** and **Doctor B** are two distinct, authenticated users with separate valid JWTs.

| Module | Tested Router | Condition | Request Details | Expected Status | Verification Check |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Patients** | `/patients` | GET list | Doctor A requests patients list. | `200 OK` | Returns Doctor A's patients only. Does not include Doctor B's patients. |
| | `/patients/{id}` | GET single | Doctor B requests Doctor A's patient UUID. | `404 Not Found` or `403 Forbidden` | Access blocked. |
| | `/patients/{id}` | DELETE | Doctor B attempts to delete Doctor A's patient. | `404 Not Found` or `403 Forbidden` | Record remains intact. |
| **Sessions** | `/sessions/patient/{id}` | GET list | Doctor B requests sessions for Doctor A's patient. | `404 Not Found` or `403 Forbidden` | Access blocked. |
| | `/sessions/{id}` | GET details | Doctor B requests Doctor A's session UUID. | `404 Not Found` or `403 Forbidden` | Access blocked. |
| | `/sessions` | POST create | Doctor B attempts to create session for Doctor A's patient. | `404 Not Found` or `403 Forbidden` | Session is not created. |
| **Audio** | `/upload-audio` | POST upload | Doctor B attempts to upload audio to Doctor A's session. | `404 Not Found` or `403 Forbidden` | Upload rejected. |
| **Notes** | `/generate-note` | POST generate | Doctor B attempts to trigger note generation on Doctor A's session. | `404 Not Found` or `403 Forbidden` | Generation blocked. |
| | `/notes/save` | POST save | Doctor B attempts to update Doctor A's SOAP note draft. | `404 Not Found` or `403 Forbidden` | Save rejected. |
| **Reports** | `/reports/patient/{id}`| GET list | Doctor B requests reports list for Doctor A's patient. | `404 Not Found` or `403 Forbidden` | List empty/blocked. |
| | `/reports/{id}/ocr` | POST OCR | Doctor B triggers OCR on Doctor A's report file. | `404 Not Found` or `403 Forbidden` | Textract execution blocked. |
| **Search** | `/ask/` | POST query | Doctor B asks a question. Doctor A has reports on "hemoglobin". | `200 OK` | Answer states "No relevant context found". Doctor A's reports are **not** searched or cited. |
| **Timeline** | `/timeline/{id}` | GET timeline | Doctor B requests timeline for Doctor A's patient. | `404 Not Found` or `403 Forbidden` | Access blocked. |
| **Comparison**| `/compare/{id}` | GET labs | Doctor B requests comparison for Doctor A's patient. | `404 Not Found` or `403 Forbidden` | Access blocked. |

---

## 2. Frontend Client Isolation Verification

To verify that the React client SPA compiles with data isolation requirements, the QA team will perform manual walk-through testing. In these tests, **Doctor A** creates a patient, a session, a report, and a note. Then, **Doctor B** logs in.

The following visual surfaces must be verified to ensure Doctor B cannot view Doctor A's records:

### 1. Dashboard Metrics (`/` - DashboardPage)
*   **Total Patients Widget**: Doctor B's dashboard must count only Doctor B's patients (e.g. if Doctor B has 0 patients, count must display `0`, ignoring Doctor A's 4 patients).
*   **Critical Alerts Widget**: High-level alert banners derived from clinical lab ranges must display only Doctor B's critical alerts.
*   **Recent Activity Feed**: The chronological feed of file uploads and note finalizations must not list any session uploads or finalizations performed by Doctor A.
*   **Patients Table**: The dashboard quick-access table must show only Doctor B's patient listing.

### 2. Patient Directory (`/patients` - PatientDirectoryPage)
*   **Listing Grid**: The catalog of active patient cards must exclude all patients owned by Doctor A.
*   **Directory Search**: Searching for name keywords belonging to Doctor A's patients (e.g. "Radhika") must return an empty list or "No patients found" feedback.
*   **Filters**: Age, Gender, and Status badges must filter only Doctor B's records.

### 3. Patient Profile (`/patients/:id` - PatientProfilePage)
*   **Direct URL Navigation**: Navigating directly to `http://localhost:5173/patients/{id_A}` (using Doctor A's patient UUID) must trigger the `ErrorBoundary` or redirect the clinician to a `404 Not Found` page.
*   **Demographic Header**: Header metrics (e.g. name, age, gender) must be blank or display a warning.

### 4. Sessions Workspace (`/patients/:id/sessions` - SessionsTab & SessionDetailPage)
*   **Sessions Consultation List**: The chronological list of session cards under the patient profile tab must not display Doctor A's session consultations.
*   **SOAP Note Editor**: Text area fields (Subjective, Objective, Assessment, Plan) must remain empty or inaccessible for Doctor A's session UUID.
*   **Finalization locks**: The save/finalize controls must be disabled or hidden.

### 5. Reports Workspace (`/patients/:id/reports` - ReportsTab)
*   **Uploaded Files Archive List**: The document timeline list on the left section of the workspace must be empty, excluding Doctor A's diagnostic PDFs.
*   **Parsed Text Monospace View**: The right-panel OCR monospace text preview container must not render any parsed characters from Doctor A's reports.
*   **Pipeline Checklist**: The processing status indicators must remain inactive.

### 6. Clinical Timeline (`/patients/:id` - OverviewTab)
*   **Timeline Events**: Chronological markers for diagnostic uploads and transcript finalizations must exclude Doctor A's session dates.

### 7. Semantic Search Results (`/search` - SearchPage)
*   **Clinical Synthesis Answer**: Synthesized text answers returned from the QA panel must not retrieve or utilize information from Doctor A's report files.
*   **Cited Snippets (Attribution Sources)**: The citation card stack must contain 0 source cards referencing Doctor A's reports, preventing any cross-user data leakage.
