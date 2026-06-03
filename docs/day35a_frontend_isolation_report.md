# Day 35A Frontend Ownership Isolation Audit Report

This report documents the Frontend Ownership Isolation Audit executed for the Day 35A User-Patient Ownership Model. It verifies whether clinical screens on the client frontend correctly prevent cross-tenant data leakage between two authenticated users (**Doctor A** and **Doctor B**).

---

## 1. Audit Methodology & Test Execution

A Python-based user-session simulator (`backend/scripts/run_frontend_isolation_audit.py`) was executed to:
1.  Register and authenticate **Doctor A** and **Doctor B**.
2.  Perform Doctor A actions:
    *   Create **Patient A** (`Audit Patient A`, Age: 42, Male).
    *   Create **Session A** for Patient A.
    *   Upload audio and generate/finalize **Note A** for Session A.
    *   Create **Report A** and mark it as `"ready"` with laboratory text: `"Hemoglobin is normal at 14.5 g/dL. Glucose is 95 mg/dL."`
3.  Simulate frontend API requests triggered by Doctor B's client interface when trying to access Doctor A's records.

---

## 2. Screen-by-Screen Isolation Status

### 1. Dashboard
*   **API Requests**:
    *   `GET /patients/` (to list patients and compute Total Patients count)
    *   `GET /patient-overview/{patientId}` (to compute Critical Alerts count and show latest labs)
*   **Doctor B Responses**:
    *   `GET /patients/` -> returns `200 OK` with `[]` (empty array)
    *   `GET /patient-overview/PatientA_ID` -> returns `404 Not Found`
*   **Visible UI State**: Doctor B's dashboard shows **0 Patients** and **0 Critical Alerts**. The Patient Cases Directory is empty, displaying: *"No patients registered in the system yet."*
*   **Status**: **PASS** (No counts, metrics, or identifiers are leaked).

---

### 2. Patient Directory
*   **API Request**: `GET /patients/`
*   **Doctor B Response**: `200 OK` with `[]`
*   **Visible UI State**: Displays an empty directory grid with no patient rows.
*   **Status**: **PASS** (Zero patient profiles are visible).

---

### 3. Patient Profile
*   **API Request**: `GET /patients/{patientId}`
*   **Doctor B Response**: `404 Not Found`
*   **Visible UI State**: The client renders an Error Boundary fallback displaying *"Patient not found"* or matches the 404 Route redirect.
*   **Status**: **PASS** (Demographics and profile headers are fully isolated).

---

### 4. Sessions
*   **API Requests**:
    *   `GET /sessions/patient/{patientId}` (list patient sessions)
    *   `GET /sessions/{sessionId}` (view session details & SOAP note)
*   **Doctor B Responses**:
    *   `GET /sessions/patient/PatientA_ID` -> returns `404 Not Found`
    *   `GET /sessions/SessionA_ID` -> returns `404 Not Found`
*   **Visible UI State**: The Sessions tab/editor shows an error or empty state. No transcript text or finalized SOAP note data is visible.
*   **Status**: **PASS** (Sessions and SOAP drafts are fully isolated).

---

### 5. Reports
*   **API Request**: `GET /reports/patient/{patientId}`
*   **Doctor B Response**: `404 Not Found`
*   **Visible UI State**: The reports grid shows no files. PDF file list is empty.
*   **Status**: **PASS** (Diagnostics and lab files are fully isolated).

---

### 6. Timeline
*   **API Request**: `GET /timeline/{patientId}`
*   **Doctor B Response**: `404 Not Found`
*   **Visible UI State**: Rejects with 404, showing an error page. No chronological medical events are visible.
*   **Status**: **PASS** (Timeline tracks are fully isolated).

---

### 7. Insights
*   **API Request**: `GET /patient-insights/{patientId}`
*   **Doctor B Response**: `404 Not Found`
*   **Visible UI State**: Rejects with 404, showing an error page. AI clinical summary and recommendations are hidden.
*   **Status**: **PASS** (AI insights are fully isolated).

---

### 8. Comparison
*   **API Request**: `GET /compare/{patientId}`
*   **Doctor B Response**: `404 Not Found`
*   **Visible UI State**: Rejects with 404. Historical lab trends and charts are hidden.
*   **Status**: **PASS** (Lab trends comparison is fully isolated).

---

### 9. Semantic Search Hub
*   **API Request**: `POST /ask/` with body `{"question": "What is the hemoglobin level for Patient A?"}`
*   **Doctor B Response**: `200 OK`
    *   `answer`: `"The hemoglobin level is normal at 14.5 g/dL."`
    *   `chunks_used`: Citations containing Patient A's diagnostic text.
*   **Visible UI State**: **DATA LEAK**. The search results display Doctor A's patient lab metrics (Hemoglobin: `14.5 g/dL`) to Doctor B.
*   **Status**: **FAIL** (Semantic search query is executed globally across FAISS vector indexes, bypassing clinician ownership boundaries).

---

## 3. Leaks and Abnormalities Identified

1.  **Leaked Identifiers / Data**:
    *   **Page**: Semantic Search Hub (`/search` or `POST /ask/` API)
    *   **Data Leaked**: Doctor A's patient lab readings (Hemoglobin level `14.5 g/dL`) and text snippets from the parsed PDF report.
2.  **Leaked Counts or Metrics**:
    *   None. Dashboard patient and alert counts are properly isolated and scoped.

---

## 4. Final Conclusion

### **Day35A Requires Additional Fixes**

**Justification**:
While 8 out of the 9 clinical views are successfully isolated and prevent all unauthorized data leakage, the **Semantic Search Hub (POST /ask/ endpoint) failed the isolation audit**. It returns Doctor A's patient diagnostic metrics and report chunks to Doctor B because the FAISS vector index is queried globally without matching ownership constraints.

**Next Steps**:
This failure is the direct target of the upcoming **Day 35B (FAISS Ownership Isolation)** phase, which will patch `report_vector_store.py` and the `/ask` router to scope vector searches by the requesting user's `owner_id`. 

Since Day 35B was explicitly excluded from the current implementation scope ("Do not start Day 35B yet" and "Do not modify FAISS code"), this failure represents the expected pre-Day 35B state. However, to strictly satisfy the audit criteria, it is marked as **Requires Additional Fixes** to prevent premature sign-off before Day 35B is applied.
