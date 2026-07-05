import requests
import uuid
import time
import json
import os
import sys
from datetime import date

# Import db session and models
from database import SessionLocal
from models import User, Patient, Session as SessionModel, Transcript, Note, Report, Embedding

BASE_URL = "http://localhost:8000"

def log_test(section, name, success, detail=""):
    status = "PASS" if success else "FAIL"
    icon = "[PASS]" if success else "[FAIL]"
    print(f"[{section}] {icon} {name}: {status} - {detail}")
    return success

def run_audit():
    print("=" * 60)
    print("RUNNING MULTI-ACCOUNT SECURITY AUDIT (HYBRID DB+API)")
    print("=" * 60)

    db = SessionLocal()

    # 1. Generate unique emails for Doctor A and Doctor B
    doc_a_email = f"doctor_a_{uuid.uuid4().hex[:6]}@neuroscribe.com"
    doc_b_email = f"doctor_b_{uuid.uuid4().hex[:6]}@neuroscribe.com"
    password = "TestPassword123!@"

    # 2. Register both doctors via API
    print(f"[*] Registering Doctor A: {doc_a_email}")
    res = requests.post(f"{BASE_URL}/auth/register", json={"email": doc_a_email, "password": password, "name": "Doctor Alpha"})
    if res.status_code != 201:
        print(f"[-] Registration failed for Doctor A: {res.text}")
        sys.exit(1)
    
    print(f"[*] Registering Doctor B: {doc_b_email}")
    res = requests.post(f"{BASE_URL}/auth/register", json={"email": doc_b_email, "password": password, "name": "Doctor Beta"})
    if res.status_code != 201:
        print(f"[-] Registration failed for Doctor B: {res.text}")
        sys.exit(1)

    # 3. Log in as Doctor A and Doctor B via API
    print("[*] Logging in as Doctor A...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": doc_a_email, "password": password})
    if res.status_code != 200:
        print(f"[-] Login failed for Doctor A: {res.text}")
        sys.exit(1)
    token_a = res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    print("[*] Logging in as Doctor B...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": doc_b_email, "password": password})
    if res.status_code != 200:
        print(f"[-] Login failed for Doctor B: {res.text}")
        sys.exit(1)
    token_b = res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Fetch User IDs from database to associate entities properly
    doc_a_user = db.query(User).filter(User.email == doc_a_email).first()
    doc_b_user = db.query(User).filter(User.email == doc_b_email).first()
    if not doc_a_user or not doc_b_user:
        print("[-] User accounts not found in database after registration")
        sys.exit(1)

    doc_a_id = doc_a_user.id
    doc_b_id = doc_b_user.id
    print(f"[+] Doctor A UUID: {doc_a_id}")
    print(f"[+] Doctor B UUID: {doc_b_id}")

    # 4. Doctor A: Create Patient Alpha (MR-A)
    print("[*] Doctor A: Creating Patient Alpha...")
    patient_a = Patient(
        id=uuid.uuid4(),
        name="Patient Alpha",
        age=42,
        gender="Male",
        owner_id=doc_a_id
    )
    db.add(patient_a)
    db.commit()
    pt_a_id = str(patient_a.id)
    print(f"[+] Created Patient Alpha: {pt_a_id}")

    # 5. Doctor A: Create Session A for Patient Alpha
    print("[*] Doctor A: Creating Session A...")
    session_a = SessionModel(
        id=uuid.uuid4(),
        patient_id=patient_a.id,
        session_date=date.today()
    )
    db.add(session_a)
    db.commit()
    sess_a_id = str(session_a.id)
    print(f"[+] Created Session A: {sess_a_id}")

    # 6. Doctor A: Create Transcript directly in DB (bypass Whisper limits)
    print("[*] Doctor A: Creating Transcript in DB...")
    transcript_text = "Patient reports worsening anxiety and sleep issues. Checked vitals and discussed starting sertraline 50mg daily."
    transcript_a = Transcript(
        id=uuid.uuid4(),
        session_id=session_a.id,
        raw_text=transcript_text
    )
    db.add(transcript_a)
    db.commit()
    trans_a_id = str(transcript_a.id)
    print(f"[+] Created Transcript A: {trans_a_id}")

    # 7. Doctor A: Generate SOAP note via API (checks ownership and calls LLM)
    print("[*] Doctor A: Generating SOAP note via API...")
    res = requests.post(f"{BASE_URL}/generate-note", json={
        "transcript_id": trans_a_id,
        "patient_name": "Patient Alpha",
        "patient_age": 42
    }, headers=headers_a)
    if res.status_code != 200:
        print(f"[-] Failed to generate SOAP note: {res.status_code} - {res.text}")
        sys.exit(1)
    
    note_a_id = res.json()["note_id"]
    ai_draft = res.json()["ai_draft"]
    print(f"[+] Generated note AI draft: {note_a_id}")

    # 8. Doctor A: Save/finalize note via API (triggers SQLite/FAISS note embeddings)
    print("[*] Doctor A: Finalizing SOAP note...")
    res = requests.post(f"{BASE_URL}/save-note", json={
        "note_id": note_a_id,
        "doctor_edited": ai_draft
    }, headers=headers_a)
    if res.status_code != 200:
        print(f"[-] Failed to save note: {res.text}")
        sys.exit(1)
    print("[+] Finalized note and auto-embedded.")

    # 9. Doctor A: Upload a PDF Report for Patient Alpha via API
    print("[*] Doctor A: Uploading Patient Alpha Report...")
    report_a_path = os.path.join(os.path.dirname(__file__), "patient_a_report.pdf")
    with open(report_a_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/reports/upload", data={"patient_id": pt_a_id}, files={"file": ("patient_a_report.pdf", f, "application/pdf")}, headers=headers_a)
    if res.status_code != 200:
        print(f"[-] Failed to upload report for Patient Alpha: {res.text}")
        sys.exit(1)
    report_a_id = res.json()["id"]
    print(f"[+] Uploaded report: {report_a_id}")

    # 10. Doctor A: Run OCR on Report Alpha via API (generates FAISS embeddings)
    print("[*] Doctor A: Running OCR on Report Alpha...")
    res = requests.post(f"{BASE_URL}/reports/{report_a_id}/ocr", headers=headers_a)
    if res.status_code != 200:
        print(f"[-] Failed to run OCR on Report Alpha: {res.text}")
        sys.exit(1)
    print("[+] OCR processing and RAG index addition complete.")

    print("\n" + "=" * 50)
    print("VERIFYING ISOLATION (DOCTOR B QUERIES DOCTOR A'S DATA)")
    print("=" * 50)

    results = []

    # Test 1: Doctor B lists patients. Doctor A's patient must NOT be in the list.
    res = requests.get(f"{BASE_URL}/patients/", headers=headers_b)
    has_pt_a = any(p["id"] == pt_a_id for p in res.json())
    results.append(log_test("DIRECTORY", "Patient Directory Isolation", not has_pt_a, "Doctor A's patient is not returned to Doctor B"))

    # Test 2: Doctor B tries to fetch Doctor A's patient directly. Must be 404.
    res = requests.get(f"{BASE_URL}/patients/{pt_a_id}", headers=headers_b)
    results.append(log_test("PROFILE", "Patient Profile GET Isolation", res.status_code == 404, f"GET patient returns status {res.status_code} (Expected 404)"))

    # Test 3: Doctor B tries to list sessions for Doctor A's patient. Must be 404.
    res = requests.get(f"{BASE_URL}/sessions/patient/{pt_a_id}", headers=headers_b)
    results.append(log_test("SESSIONS", "Sessions Patient List Isolation", res.status_code == 404, f"List sessions returns status {res.status_code} (Expected 404)"))

    # Test 4: Doctor B tries to fetch Doctor A's session directly. Must be 404.
    res = requests.get(f"{BASE_URL}/sessions/{sess_a_id}", headers=headers_b)
    results.append(log_test("SESSIONS", "Session Detail GET Isolation", res.status_code == 404, f"GET session returns status {res.status_code} (Expected 404)"))

    # Test 5: Doctor B tries to list reports for Doctor A's patient. Must be 404.
    res = requests.get(f"{BASE_URL}/reports/patient/{pt_a_id}", headers=headers_b)
    results.append(log_test("REPORTS", "Reports Patient List Isolation", res.status_code == 404, f"List reports returns status {res.status_code} (Expected 404)"))

    # Test 6: Doctor B tries to fetch Doctor A's report details. Must be 404.
    res = requests.get(f"{BASE_URL}/reports/{report_a_id}", headers=headers_b)
    results.append(log_test("REPORTS", "Report Detail GET Isolation", res.status_code == 404, f"GET report returns status {res.status_code} (Expected 404)"))

    # Test 7: Doctor B tries to download Doctor A's report file. Must be 404.
    res = requests.get(f"{BASE_URL}/reports/{report_a_id}/download", headers=headers_b)
    results.append(log_test("REPORTS", "Report Download Authorization Isolation", res.status_code == 404, f"Download report returns status {res.status_code} (Expected 404)"))

    # Test 8: Doctor B tries to ask a question referencing Patient Alpha. Must be 404.
    res = requests.post(f"{BASE_URL}/ask/", json={"patient_id": pt_a_id, "question": "What is the patient diagnosis?", "top_k": 5}, headers=headers_b)
    results.append(log_test("RAG", "Ask NeuroScribe Patient Authorization Isolation", res.status_code == 404, f"RAG query returns status {res.status_code} (Expected 404)"))

    # Test 9: Doctor B tries to fetch Doctor A's patient overview. Must be 404.
    res = requests.get(f"{BASE_URL}/patient-overview/{pt_a_id}", headers=headers_b)
    results.append(log_test("INSIGHTS", "Patient Overview GET Isolation", res.status_code == 404, f"Overview query returns status {res.status_code} (Expected 404)"))

    # Test 10: Doctor B tries to fetch Doctor A's patient insights. Must be 404.
    res = requests.get(f"{BASE_URL}/patient-insights/{pt_a_id}", headers=headers_b)
    results.append(log_test("INSIGHTS", "Patient Insights GET Isolation", res.status_code == 404, f"Insights query returns status {res.status_code} (Expected 404)"))

    # Test 11: Doctor B tries to fetch Doctor A's clinical comparison. Must be 404.
    res = requests.get(f"{BASE_URL}/compare/{pt_a_id}", headers=headers_b)
    results.append(log_test("TRENDS", "Clinical Comparison GET Isolation", res.status_code == 404, f"Comparison query returns status {res.status_code} (Expected 404)"))

    # Test 12: Doctor B tries to fetch Doctor A's clinical timeline. Must be 404.
    res = requests.get(f"{BASE_URL}/timeline/{pt_a_id}", headers=headers_b)
    results.append(log_test("TRENDS", "Clinical Timeline GET Isolation", res.status_code == 404, f"Timeline query returns status {res.status_code} (Expected 404)"))

    # Test 13: Doctor B creates their own patient (Patient Beta) and asks a question.
    # The question should NOT retrieve any information from Doctor A's patients (Patient Alpha).
    print("\n[*] Doctor B: Creating Patient Beta...")
    patient_b = Patient(
        id=uuid.uuid4(),
        name="Patient Beta",
        age=28,
        gender="Female",
        owner_id=doc_b_id
    )
    db.add(patient_b)
    db.commit()
    pt_b_id = str(patient_b.id)

    print("[*] Doctor B: Uploading Patient Beta Report...")
    report_b_path = os.path.join(os.path.dirname(__file__), "patient_b_report.pdf")
    with open(report_b_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/reports/upload", data={"patient_id": pt_b_id}, files={"file": ("patient_b_report.pdf", f, "application/pdf")}, headers=headers_b)
    if res.status_code != 200:
        print(f"[-] Failed to upload report for Patient Beta: {res.text}")
        sys.exit(1)
    report_b_id = res.json()["id"]
    
    print("[*] Doctor B: Running OCR on Report Beta...")
    res = requests.post(f"{BASE_URL}/reports/{report_b_id}/ocr", headers=headers_b)
    if res.status_code != 200:
        print(f"[-] Failed OCR on Report Beta: {res.text}")
        sys.exit(1)

    print("[*] Doctor B: Querying Ask NeuroScribe for Patient Beta...")
    res = requests.post(f"{BASE_URL}/ask/", json={"patient_id": pt_b_id, "question": "What is the hemoglobin level?", "top_k": 5}, headers=headers_b)
    if res.status_code == 200:
        answer_text = str(res.json()["answer"]).lower()
        citations = res.json()["chunks_used"]
        citations_text = "".join(c["chunk_text"] for c in citations).lower()
        
        # Check if Doctor A's patient findings leaked.
        # Doctor A's patient (Patient Alpha) report is 'patient_a_report.pdf' which has hemoglobin 8.2 and diabetes.
        # Doctor B's patient (Patient Beta) report is 'patient_b_report.pdf' which has hemoglobin 14.5 and migraine.
        has_leak = "8.2" in answer_text or "8.2" in citations_text or "diabetes" in answer_text or "diabetes" in citations_text
        results.append(log_test("RAG", "RAG Cross-User/Doctor Context Leakage Isolation", not has_leak, 
                 "No leaked context from Doctor A's patient in Doctor B's RAG query response" if not has_leak else "Leaked Doctor A's data!"))
    else:
        results.append(log_test("RAG", "RAG Cross-User/Doctor Context Leakage Isolation", False, f"Ask query failed with status {res.status_code}"))

    db.close()

    print("\n" + "=" * 50)
    print("AUDIT COMPLETED")
    print("=" * 50)
    
    if all(results):
        print("SUCCESS: 100% of data isolation test checks passed!")
    else:
        print("FAILURE: Some data isolation test checks failed!")

if __name__ == "__main__":
    run_audit()
