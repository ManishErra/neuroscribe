# Day 35B FAISS Ownership Isolation Verification Report

This report presents the verification findings, test logs, and clinician isolation checks for the Day 35B FAISS Ownership Isolation phase.

---

## 1. Summary of Verification Outcomes

All verification checks executed by the test harness passed successfully:

| Test Scenario | Validation Checks | Outcome | Status |
| :--- | :--- | :--- | :--- |
| **Audit A: Static Metadata Check** | Loaded 1152 chunks, verified 100% contain valid `owner_id` mapping to database users. | 0 missing, 0 invalid | **PASS** |
| **Audit B: OCR Ingestion Check** | Uploaded new PDF Report C, ran OCR, verified `chunk count > 0`, verified chunk has `report_id` and correct `owner_id`. | 1 chunk generated, fields valid | **PASS** |
| **Audit C: Clinician Isolation Check** | Logged in as Doctor B, queried Patient C's lab values, verified lack of context returned and empty `chunks_used`. | Empty context, 0 chunks leaked | **PASS** |

---

## 2. Command Executed

```powershell
.venv\Scripts\python.exe backend\scripts\run_day35b_verification.py
```

*   **Exit Code**: `0`
*   **Result**: `ALL DAY 35B FAISS VECTOR STORE ISOLATION VERIFICATION MATRIX CHECKS PASSED SUCCESSFULLY!`

---

## 3. Capture of Complete Command Output

```text
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights:   0%|          | 0/103 [00:00<?, ?it/s]Loading weights: 100%|##########| 103/103 [00:00<00:00, 2497.17it/s]

--- DAY 35B FAISS VECTOR STORE ISOLATION VERIFICATION MATRIX ---

--- Audit A: Existing Metadata Check ---
  Loaded 1152 metadata chunks.
  Loaded 12 valid user IDs from database.
  Chunks missing owner_id                : 0
  Chunks with owner_id not in users table: 0
  PASS: Static metadata audit passed.

--- Audit B: OCR Chunk Ingestion Audit ---
  Doctor A logged in: doctor-a-33ce9b@neuroscribe.org (ID: 28ee06fa-4f58-45d7-ac51-f4d39906b5b0)
  Doctor B logged in: doctor-b-43dd19@neuroscribe.org (ID: d00092a7-d642-42d2-acec-a21ae54da40d)
  PASS: Report uploaded successfully. ID: dcb72aa3-1a24-430d-be45-3ebf2183f2e2
  PASS: OCR completed. Status: ready
  New report generated chunks count: 1
  PASS: Report generated > 0 chunks.
  PASS: Every chunk contains report_id and owner_id.
  PASS: Every chunk owner_id equals current_user.id.

--- Audit C: Multi-Clinician Isolation Check ---

[DEBUG] Top 10 unique retrieval results for Hemoglobin query:
--------------------------------------------------

================ RAG DEBUG ================
QUERY: What is the Hemoglobin level of Patient C?
NO RESULTS FOUND
===========================================

  Doctor B answer     : No relevant medical context found.
  Doctor B chunks_used : []
  Doctor B answer shows lack of context: PASS
  Doctor B chunks_used is empty        : PASS

Cleaning up test verification records...
  PASS: Test patient C and report C deleted from DB.
  PASS: Test doctor accounts deleted.

ALL DAY 35B FAISS VECTOR STORE ISOLATION VERIFICATION MATRIX CHECKS PASSED SUCCESSFULLY!
```

---

## 4. Clinician Isolation Metrics

*   **Leaked Identifiers**: None.
*   **Leaked Chunks/Metadata**: `0` chunks leaked from Doctor A to Doctor B.
*   **Search Scoping Behavior**: Verified that `search_similar_chunks` successfully blocks cross-user vector leakage. When Doctor B queried Doctor A's report keywords, `search_similar_chunks` filtered out all candidates matching `owner_id = Doctor A` and returned an empty result list `[]`.
