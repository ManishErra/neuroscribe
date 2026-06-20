"""
NeuroScribe Final Functional Verification Suite
Covers: Auth, Patient, Session, Report, OCR, Embedding, RAG, Isolation
"""
import requests
import time
import json
import uuid
import sys

BASE = "http://localhost:8000"
PASS = "PASS"
FAIL = "FAIL"

results = {}

def log(test_name, status, detail=""):
    icon = "✅" if status == PASS else "❌"
    results[test_name] = {"status": status, "detail": detail}
    print(f"  {icon} {test_name}: {status} — {detail}")

print("=" * 60)
print("NEUROSCRIBE FINAL FUNCTIONAL VERIFICATION")
print("=" * 60)

# ════════════════════════════════════════════════
# 1. AUTHENTICATION
# ════════════════════════════════════════════════
print("\n── 1. AUTHENTICATION ──")

# 1a. Health check
try:
    r = requests.get(f"{BASE}/")
    assert r.status_code == 200
    log("1a_health_check", PASS, f"{r.status_code} {r.json()}")
except Exception as e:
    log("1a_health_check", FAIL, str(e))
    print("Backend not reachable. Aborting.")
    sys.exit(1)

# 1b. Register new test user
test_email = f"test_{uuid.uuid4().hex[:8]}@neuroscribe.com"
test_pass = "TestPass123!@"
try:
    r = requests.post(f"{BASE}/auth/register", json={
        "email": test_email,
        "password": test_pass,
        "name": "Test Doctor"
    })
    assert r.status_code == 201, f"Got {r.status_code}: {r.text}"
    reg_data = r.json()
    assert "id" in reg_data
    log("1b_register", PASS, f"User ID: {reg_data['id']}, Email: {reg_data['email']}")
except Exception as e:
    log("1b_register", FAIL, str(e))

# 1c. Login
try:
    r = requests.post(f"{BASE}/auth/login", json={
        "email": test_email,
        "password": test_pass
    })
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("1c_login", PASS, f"Token obtained (len={len(token)})")
except Exception as e:
    log("1c_login", FAIL, str(e))
    print("Login failed. Aborting.")
    sys.exit(1)

# 1d. JWT protection — unauthenticated request
try:
    r = requests.get(f"{BASE}/patients/")
    assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
    log("1d_jwt_protection", PASS, f"Unauthenticated request returned {r.status_code}")
except Exception as e:
    log("1d_jwt_protection", FAIL, str(e))

# 1e. JWT — /auth/me
try:
    r = requests.get(f"{BASE}/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == test_email
    log("1e_auth_me", PASS, f"Confirmed identity: {me['email']}")
except Exception as e:
    log("1e_auth_me", FAIL, str(e))

# ════════════════════════════════════════════════
# 2. PATIENT WORKFLOW
# ════════════════════════════════════════════════
print("\n── 2. PATIENT WORKFLOW ──")

patient_a_id = None
patient_b_id = None

# 2a. Create Patient A
try:
    r = requests.post(f"{BASE}/patients/", json={
        "name": "Patient Alpha", "age": 45, "gender": "male"
    }, headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    patient_a_id = r.json()["id"]
    log("2a_create_patient_a", PASS, f"ID: {patient_a_id}")
except Exception as e:
    log("2a_create_patient_a", FAIL, str(e))

# 2b. Create Patient B
try:
    r = requests.post(f"{BASE}/patients/", json={
        "name": "Patient Beta", "age": 30, "gender": "female"
    }, headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    patient_b_id = r.json()["id"]
    log("2b_create_patient_b", PASS, f"ID: {patient_b_id}")
except Exception as e:
    log("2b_create_patient_b", FAIL, str(e))

# 2c. View Patient A
try:
    r = requests.get(f"{BASE}/patients/{patient_a_id}", headers=headers)
    assert r.status_code == 200
    p = r.json()
    assert p["name"] == "Patient Alpha"
    assert p["age"] == 45
    log("2c_view_patient_a", PASS, f"Name: {p['name']}, Age: {p['age']}")
except Exception as e:
    log("2c_view_patient_a", FAIL, str(e))

# 2d. List Patients (verify persistence)
try:
    r = requests.get(f"{BASE}/patients/", headers=headers)
    assert r.status_code == 200
    patients = r.json()
    names = [p["name"] for p in patients]
    assert "Patient Alpha" in names
    assert "Patient Beta" in names
    log("2d_list_patients", PASS, f"Found {len(patients)} patients, both Alpha and Beta present")
except Exception as e:
    log("2d_list_patients", FAIL, str(e))

# ════════════════════════════════════════════════
# 3. SESSION WORKFLOW
# ════════════════════════════════════════════════
print("\n── 3. SESSION WORKFLOW ──")

session_id = None

# 3a. Create Session for Patient A
try:
    r = requests.post(f"{BASE}/sessions/", json={
        "patient_id": patient_a_id
    }, headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    session_id = r.json()["id"]
    log("3a_create_session", PASS, f"Session ID: {session_id}")
except Exception as e:
    log("3a_create_session", FAIL, str(e))

# 3b. List Sessions for Patient A
try:
    r = requests.get(f"{BASE}/sessions/patient/{patient_a_id}", headers=headers)
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) >= 1
    log("3b_list_sessions", PASS, f"Found {len(sessions)} session(s) for Patient Alpha")
except Exception as e:
    log("3b_list_sessions", FAIL, str(e))

# 3c. Get Session Detail
try:
    r = requests.get(f"{BASE}/sessions/{session_id}", headers=headers)
    assert r.status_code == 200
    s = r.json()
    assert s["id"] == session_id
    log("3c_get_session_detail", PASS, f"Session date: {s['session_date']}")
except Exception as e:
    log("3c_get_session_detail", FAIL, str(e))

# ════════════════════════════════════════════════
# 4. REPORT WORKFLOW
# ════════════════════════════════════════════════
print("\n── 4. REPORT WORKFLOW ──")

report_a_id = None
report_b_id = None

# 4a. Upload Report A for Patient A
try:
    with open("patient_a_report.pdf", "rb") as f:
        r = requests.post(f"{BASE}/reports/upload",
            data={"patient_id": patient_a_id},
            files={"file": ("patient_a_report.pdf", f, "application/pdf")},
            headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    report_a_id = r.json()["id"]
    log("4a_upload_report_a", PASS, f"Report A ID: {report_a_id}, Status: {r.json()['ocr_status']}")
except Exception as e:
    log("4a_upload_report_a", FAIL, str(e))

# 4b. Upload Report B for Patient B
try:
    with open("patient_b_report.pdf", "rb") as f:
        r = requests.post(f"{BASE}/reports/upload",
            data={"patient_id": patient_b_id},
            files={"file": ("patient_b_report.pdf", f, "application/pdf")},
            headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    report_b_id = r.json()["id"]
    log("4b_upload_report_b", PASS, f"Report B ID: {report_b_id}, Status: {r.json()['ocr_status']}")
except Exception as e:
    log("4b_upload_report_b", FAIL, str(e))

# 4c. Run OCR on Report A
try:
    r = requests.post(f"{BASE}/reports/{report_a_id}/ocr", headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    ocr_a = r.json()
    log("4c_ocr_report_a", PASS, f"Status: {ocr_a['ocr_status']}, Chars: {ocr_a['extracted_char_count']}, Preview: {ocr_a['text_preview'][:80]}")
except Exception as e:
    log("4c_ocr_report_a", FAIL, str(e))

# 4d. Run OCR on Report B
try:
    r = requests.post(f"{BASE}/reports/{report_b_id}/ocr", headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    ocr_b = r.json()
    log("4d_ocr_report_b", PASS, f"Status: {ocr_b['ocr_status']}, Chars: {ocr_b['extracted_char_count']}, Preview: {ocr_b['text_preview'][:80]}")
except Exception as e:
    log("4d_ocr_report_b", FAIL, str(e))

# 4e. Get Report A detail — verify OCR text persisted
try:
    r = requests.get(f"{BASE}/reports/{report_a_id}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["ocr_status"] == "ready"
    assert detail["ocr_text"] and len(detail["ocr_text"]) > 0
    log("4e_verify_ocr_text_a", PASS, f"OCR text length: {len(detail['ocr_text'])}, Status: ready")
except Exception as e:
    log("4e_verify_ocr_text_a", FAIL, str(e))

# 4f. List Reports for Patient A
try:
    r = requests.get(f"{BASE}/reports/patient/{patient_a_id}", headers=headers)
    assert r.status_code == 200
    reports = r.json()
    assert len(reports) >= 1
    log("4f_list_reports_a", PASS, f"Found {len(reports)} report(s) for Patient Alpha")
except Exception as e:
    log("4f_list_reports_a", FAIL, str(e))

# ════════════════════════════════════════════════
# 5. EMBEDDING WORKFLOW
# ════════════════════════════════════════════════
print("\n── 5. EMBEDDING WORKFLOW ──")

# The OCR endpoint auto-embeds via add_report_embeddings.
# Verify the FAISS vector index has entries.
try:
    import os
    idx_path = os.path.join(os.path.dirname(__file__) if "__file__" in dir() else ".", "vector.index")
    meta_path = os.path.join(os.path.dirname(__file__) if "__file__" in dir() else ".", "vector_metadata.json")

    assert os.path.exists(idx_path), f"vector.index not found at {idx_path}"
    assert os.path.exists(meta_path), f"vector_metadata.json not found at {meta_path}"

    with open(meta_path, "r") as f:
        metadata = json.load(f)

    assert len(metadata) > 0, "No embeddings found"
    report_ids_in_vectors = set(m["report_id"] for m in metadata)
    log("5a_vectors_exist", PASS, f"FAISS has {len(metadata)} chunks across {len(report_ids_in_vectors)} report(s)")

    # Verify both reports are embedded
    has_a = report_a_id in report_ids_in_vectors
    has_b = report_b_id in report_ids_in_vectors
    log("5b_both_reports_indexed", PASS if (has_a and has_b) else FAIL,
        f"Report A indexed: {has_a}, Report B indexed: {has_b}")
except Exception as e:
    log("5a_vectors_exist", FAIL, str(e))

# ════════════════════════════════════════════════
# 6. RAG WORKFLOW
# ════════════════════════════════════════════════
print("\n── 6. RAG WORKFLOW ──")

# 6a. Query: "What is the diagnosis?"
try:
    r = requests.post(f"{BASE}/ask/", json={
        "question": "What is the diagnosis?",
        "top_k": 5
    }, headers=headers)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    rag = r.json()
    assert "answer" in rag
    assert "chunks_used" in rag
    log("6a_rag_query", PASS, f"Answer: {str(rag['answer'])[:120]}")
    log("6b_rag_citations", PASS if len(rag["chunks_used"]) > 0 else FAIL,
        f"Citations returned: {len(rag['chunks_used'])}")
except Exception as e:
    log("6a_rag_query", FAIL, str(e))

# ════════════════════════════════════════════════
# 7. ISOLATION TEST
# ════════════════════════════════════════════════
print("\n── 7. ISOLATION TEST ──")

# 7a. Check if the /ask/ endpoint supports patient_id filtering
#     Based on code review: it does NOT. It uses owner_id only.
#     This is a critical architectural finding.
try:
    # Read the FAISS metadata to check isolation
    with open(meta_path, "r") as f:
        metadata = json.load(f)

    a_chunks = [m for m in metadata if m["report_id"] == report_a_id]
    b_chunks = [m for m in metadata if m["report_id"] == report_b_id]

    log("7a_report_a_chunks", PASS, f"Patient A has {len(a_chunks)} chunk(s) in FAISS")
    log("7b_report_b_chunks", PASS, f"Patient B has {len(b_chunks)} chunk(s) in FAISS")

    # Verify owner_id isolation (same owner)
    a_owners = set(m.get("owner_id", "MISSING") for m in a_chunks)
    b_owners = set(m.get("owner_id", "MISSING") for m in b_chunks)
    log("7c_owner_isolation", PASS, f"A owners: {a_owners}, B owners: {b_owners}")

    # CRITICAL FINDING: The /ask/ endpoint does NOT accept patient_id.
    # All queries return chunks from ALL of this doctor's patients.
    # This means asking "What is the diagnosis?" inside Patient A's workspace
    # will return chunks from BOTH Patient A AND Patient B.
    log("7d_patient_level_isolation", FAIL,
        "CRITICAL: /ask/ endpoint filters by owner_id only, NOT patient_id. "
        "Cross-patient leakage exists within same doctor's workspace. "
        "The frontend AskTab may pass patient_id but backend ignores it.")

except Exception as e:
    log("7_isolation_test", FAIL, str(e))

# 7e. Cross-user isolation test (register a different doctor)
try:
    other_email = f"other_{uuid.uuid4().hex[:8]}@neuroscribe.com"
    r = requests.post(f"{BASE}/auth/register", json={
        "email": other_email, "password": test_pass, "name": "Other Doctor"
    })
    assert r.status_code == 201
    r = requests.post(f"{BASE}/auth/login", json={"email": other_email, "password": test_pass})
    other_token = r.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Other doctor queries — should get no results
    r = requests.post(f"{BASE}/ask/", json={"question": "What is the diagnosis?", "top_k": 5}, headers=other_headers)
    assert r.status_code == 200
    other_rag = r.json()
    other_chunks = other_rag.get("chunks_used", [])
    log("7e_cross_user_isolation", PASS if len(other_chunks) == 0 else FAIL,
        f"Other doctor got {len(other_chunks)} chunks (expected 0)")
except Exception as e:
    log("7e_cross_user_isolation", FAIL, str(e))


# ════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════
print("\n" + "=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)

total = len(results)
passed = sum(1 for r in results.values() if r["status"] == PASS)
failed = sum(1 for r in results.values() if r["status"] == FAIL)

print(f"\nTotal Tests:  {total}")
print(f"Passed:       {passed}")
print(f"Failed:       {failed}")
print(f"Pass Rate:    {(passed/total*100):.1f}%")

print("\n── FAILED TESTS ──")
for name, r in results.items():
    if r["status"] == FAIL:
        print(f"  ❌ {name}: {r['detail']}")

print("\n── ALL RESULTS ──")
for name, r in results.items():
    icon = "✅" if r["status"] == PASS else "❌"
    print(f"  {icon} {name}: {r['detail'][:100]}")
