import requests
import sys

BASE = "http://localhost:8000"

def run_validation():
    print("Starting RAG isolation verification script...")
    
    # 1. Register a fresh user
    import uuid
    email = f"doc_{uuid.uuid4().hex[:6]}@hospital.org"
    password = "Password12345!"
    
    print(f"Registering user: {email} ...")
    r = requests.post(f"{BASE}/auth/register", json={
        "email": email,
        "password": password,
        "name": "Dr. Validation"
    })
    if r.status_code != 201:
        print(f"Registration failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    # 2. Login
    print("Logging in...")
    r = requests.post(f"{BASE}/auth/login", json={
        "email": email,
        "password": password
    })
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Patient A (Diabetes, Age 30)
    print("Creating Patient A...")
    r = requests.post(f"{BASE}/patients/", json={
        "name": "Patient A",
        "age": 30,
        "gender": "male"
    }, headers=headers)
    if r.status_code != 200:
        print(f"Failed to create Patient A: {r.text}")
        sys.exit(1)
    patient_a_id = r.json()["id"]
    print(f"Patient A ID: {patient_a_id}")
    
    # 4. Create Patient B (Migraine, Age 35)
    print("Creating Patient B...")
    r = requests.post(f"{BASE}/patients/", json={
        "name": "Patient B",
        "age": 35,
        "gender": "female"
    }, headers=headers)
    if r.status_code != 200:
        print(f"Failed to create Patient B: {r.text}")
        sys.exit(1)
    patient_b_id = r.json()["id"]
    print(f"Patient B ID: {patient_b_id}")
    
    # 5. Upload Patient A Report
    print("Uploading report for Patient A...")
    with open("patient_a_report.pdf", "rb") as f:
        r = requests.post(f"{BASE}/reports/upload", 
                          data={"patient_id": patient_a_id},
                          files={"file": ("patient_a_report.pdf", f, "application/pdf")},
                          headers=headers)
    if r.status_code != 200:
        print(f"Upload A failed: {r.text}")
        sys.exit(1)
    report_a_id = r.json()["id"]
    print(f"Report A ID: {report_a_id}")
    
    # 6. Run OCR on Report A
    print("Running OCR on Report A...")
    r = requests.post(f"{BASE}/reports/{report_a_id}/ocr", headers=headers)
    if r.status_code != 200:
        print(f"OCR A failed: {r.text}")
        sys.exit(1)
    print("OCR A succeeded!")
    
    # 7. Upload Patient B Report
    print("Uploading report for Patient B...")
    with open("patient_b_report.pdf", "rb") as f:
        r = requests.post(f"{BASE}/reports/upload", 
                          data={"patient_id": patient_b_id},
                          files={"file": ("patient_b_report.pdf", f, "application/pdf")},
                          headers=headers)
    if r.status_code != 200:
        print(f"Upload B failed: {r.text}")
        sys.exit(1)
    report_b_id = r.json()["id"]
    print(f"Report B ID: {report_b_id}")
    
    # 8. Run OCR on Report B
    print("Running OCR on Report B...")
    r = requests.post(f"{BASE}/reports/{report_b_id}/ocr", headers=headers)
    if r.status_code != 200:
        print(f"OCR B failed: {r.text}")
        sys.exit(1)
    print("OCR B succeeded!")
    
    # 9. Query Patient A: "What is my hemoglobin level?"
    print("\n--- Querying Ask Patient A ---")
    r = requests.post(f"{BASE}/ask/", json={
        "patient_id": patient_a_id,
        "question": "What is my hemoglobin level?"
    }, headers=headers)
    if r.status_code != 200:
        print(f"Query A failed: {r.text}")
        sys.exit(1)
    
    res_a = r.json()
    print("Patient A Answer:")
    print(res_a["answer"])
    print("\nPatient A Citations:")
    for chunk in res_a["chunks_used"]:
        print(f"- [Score: {chunk['similarity_score']:.3f}] {chunk['chunk_text']}")
        
    # 10. Query Patient B: "What is my hemoglobin level?"
    print("\n--- Querying Ask Patient B ---")
    r = requests.post(f"{BASE}/ask/", json={
        "patient_id": patient_b_id,
        "question": "What is my hemoglobin level?"
    }, headers=headers)
    if r.status_code != 200:
        print(f"Query B failed: {r.text}")
        sys.exit(1)
        
    res_b = r.json()
    print("Patient B Answer:")
    print(res_b["answer"])
    print("\nPatient B Citations:")
    for chunk in res_b["chunks_used"]:
        print(f"- [Score: {chunk['similarity_score']:.3f}] {chunk['chunk_text']}")
        
    # 11. Verification Checks
    print("\n--- Verification Assertions ---")
    # A should contain 8.2 and Diabetes, must NOT contain 14.5 or Migraine
    ans_a_str = str(res_a["answer"]).lower()
    citations_a_str = "".join(c["chunk_text"] for c in res_a["chunks_used"]).lower()
    
    assert "8.2" in ans_a_str or "8.2" in citations_a_str, "Patient A result missing hemoglobin 8.2"
    assert "diabetes" in ans_a_str or "diabetes" in citations_a_str, "Patient A result missing diabetes context"
    assert "14.5" not in ans_a_str and "14.5" not in citations_a_str, "CROSS-CONTAMINATION: Patient A retrieved Patient B's hemoglobin 14.5!"
    assert "migraine" not in ans_a_str and "migraine" not in citations_a_str, "CROSS-CONTAMINATION: Patient A retrieved Patient B's migraine diagnosis!"
    
    # B should contain 14.5 and Migraine, must NOT contain 8.2 or Diabetes
    ans_b_str = str(res_b["answer"]).lower()
    citations_b_str = "".join(c["chunk_text"] for c in res_b["chunks_used"]).lower()
    
    assert "14.5" in ans_b_str or "14.5" in citations_b_str, "Patient B result missing hemoglobin 14.5"
    assert "migraine" in ans_b_str or "migraine" in citations_b_str, "Patient B result missing migraine context"
    assert "8.2" not in ans_b_str and "8.2" not in citations_b_str, "CROSS-CONTAMINATION: Patient B retrieved Patient A's hemoglobin 8.2!"
    assert "diabetes" not in ans_b_str and "diabetes" not in citations_b_str, "CROSS-CONTAMINATION: Patient B retrieved Patient A's diabetes diagnosis!"
    
    print("SUCCESS: Zero cross-patient contamination exists. Patient-level RAG isolation is fully verified!")

if __name__ == "__main__":
    run_validation()
