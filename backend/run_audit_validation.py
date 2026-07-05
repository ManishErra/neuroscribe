import requests
import os
import sys

BASE_URL = "http://localhost:8000"
PATIENT_ID = "ef5add2e-baa8-4a74-8402-da164196aebc"

def run_validation():
    print("=" * 60)
    print("RUNNING WORKFLOW VALIDATION SCRIPT")
    print("=" * 60)

    # 1. Login
    print("[*] Logging in as audit_doc_99@neuroscribe.com...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": "audit_doc_99@neuroscribe.com", "password": "Password123!@"})
    if res.status_code != 200:
        print("[-] Login failed:", res.text)
        sys.exit(1)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[+] Logged in successfully. Token obtained.")

    # 2. Upload report (Workflow B / C)
    print("[*] Uploading patient_a_report.pdf...")
    report_path = os.path.join(os.path.dirname(__file__), "patient_a_report.pdf")
    with open(report_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/reports/upload", data={"patient_id": PATIENT_ID}, files={"file": ("patient_a_report.pdf", f, "application/pdf")}, headers=headers)
    print("Upload Status:", res.status_code)
    if res.status_code != 200:
        print("[-] Upload failed:", res.text)
        sys.exit(1)
    report_id = res.json()["id"]
    print(f"[+] Report uploaded successfully. ID: {report_id}")

    # 3. Run OCR (Workflow B)
    print(f"[*] Running OCR for report {report_id}...")
    res = requests.post(f"{BASE_URL}/reports/{report_id}/ocr", headers=headers)
    print("OCR Status:", res.status_code)
    if res.status_code != 200:
        print("[-] OCR failed:", res.text)
        sys.exit(1)
    ocr_result = res.json()
    print(f"[+] OCR Succeeded. Text Preview: {ocr_result['text_preview'][:100]}...")

    # 4. Ask NeuroScribe (Workflow E)
    print("[*] Submitting RAG query: 'What is the hemoglobin level?'...")
    res = requests.post(f"{BASE_URL}/ask/", json={"patient_id": PATIENT_ID, "question": "What is the hemoglobin level?", "top_k": 5}, headers=headers)
    print("RAG Query Status:", res.status_code)
    if res.status_code != 200:
        print("[-] RAG Query failed:", res.text)
        sys.exit(1)
    rag_result = res.json()
    print("[+] RAG Answer:", rag_result["answer"])

    # 5. Report Download Validation (Workflow F)
    print("\n" + "=" * 50)
    print("TESTING DOWNLOAD METHODS (WORKFLOW F)")
    print("=" * 50)

    # Method A: Download using query parameter token (NO Bearer header)
    print("[*] Method A: Querying GET /reports/{id}/download?token=... (WITHOUT Bearer header)")
    url_with_token = f"{BASE_URL}/reports/{report_id}/download?token={token}"
    res_a = requests.get(url_with_token)
    print(f"Method A Status: {res_a.status_code}")
    print(f"Method A Body: {res_a.text[:200]}")

    # Method B: Download using Bearer header (WITHOUT query parameter token)
    print("[*] Method B: Querying GET /reports/{id}/download (WITH Bearer header)")
    url_without_token = f"{BASE_URL}/reports/{report_id}/download"
    res_b = requests.get(url_without_token, headers=headers)
    print(f"Method B Status: {res_b.status_code}")
    print(f"Method B Content length: {len(res_b.content)} bytes")

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Workflow B Ingestion & OCR: {'PASS' if ocr_result['ocr_status'] == 'ready' else 'FAIL'}")
    print(f"Workflow E Ask NeuroScribe: {'PASS' if '8.2' in str(rag_result['answer']) else 'FAIL'}")
    print(f"Workflow F (Query Param Download): {'FAIL (Reproduced 401)' if res_a.status_code == 401 else 'PASS'}")
    print(f"Workflow F (Header Bearer Download): {'PASS' if res_b.status_code == 200 else 'FAIL'}")

if __name__ == "__main__":
    run_validation()
