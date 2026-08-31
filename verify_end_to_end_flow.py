import sys
import os
import time
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app
from database import get_db

client = TestClient(app)

def run_verification():
    print("==========================================")
    print("  NEUROSCRIBE END-TO-END VERIFICATION  ")
    print("==========================================")

    # Ensure tables are created in SQLite for test runner
    import models
    from database import engine, Base
    Base.metadata.create_all(bind=engine)

    # 1. Root endpoint test
    r = client.get("/")
    assert r.status_code == 200, f"Root endpoint failed: {r.text}"
    print("[OK] 1. GET / -> 200 OK")

    # 2. Register test user
    timestamp = int(time.time())
    email = f"test_doctor_{timestamp}@neuroscribe.demo"
    password = "DemoUser@Pass123!"

    reg_payload = {
        "email": email,
        "password": password,
        "full_name": "Dr. Alex Demo",
        "specialty": "Psychiatry / Neurology"
    }

    r = client.post("/auth/register", json=reg_payload)
    assert r.status_code == 200 or r.status_code == 201, f"Registration failed ({r.status_code}): {r.text}"
    reg_data = r.json()
    print(f"[OK] 2. Registration successful for {email}")

    # 3. Login test
    login_payload = {
        "email": email,
        "password": password
    }
    r = client.post("/auth/login", json=login_payload)
    assert r.status_code == 200, f"Login failed ({r.status_code}): {r.text}"
    token_data = r.json()
    access_token = token_data.get("access_token")
    assert access_token, "No access_token returned in login response"
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"[OK] 3. Login successful, token acquired")

    # 4. Get Current User (/auth/me)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200, f"/auth/me failed ({r.status_code}): {r.text}"
    user_me = r.json()
    assert user_me["email"] == email
    print(f"[OK] 4. Authenticated /auth/me verified: {user_me['name']}")

    # 5. Create Patient ("Alex Chen")
    patient_payload = {
        "name": "Alex Chen",
        "age": 34,
        "gender": "Male",
        "notes": "Synthetic patient for demo showcase"
    }
    r = client.post("/patients/", json=patient_payload, headers=headers)
    assert r.status_code == 200 or r.status_code == 201, f"Create patient failed ({r.status_code}): {r.text}"
    patient = r.json()
    patient_id = patient["id"]
    print(f"[OK] 5. Patient created: {patient['name']} (ID: {patient_id})")

    # 6. List Patients
    r = client.get("/patients/", headers=headers)
    assert r.status_code == 200, f"List patients failed: {r.text}"
    patients_list = r.json()
    assert any(p["id"] == patient_id for p in patients_list)
    print(f"[OK] 6. Patient listing verified ({len(patients_list)} patients found)")

    # 7. Upload Report (Alex Chen synthetic PDF)
    pdf_path = Path("demo_data/alex_chen_lab_report.pdf")
    assert pdf_path.exists(), "demo_data/alex_chen_lab_report.pdf does not exist!"

    with open(pdf_path, "rb") as f:
        files = {"file": ("alex_chen_lab_report.pdf", f, "application/pdf")}
        data = {"patient_id": patient_id}
        r = client.post("/reports/upload", files=files, data=data, headers=headers)
    
    assert r.status_code == 200 or r.status_code == 201, f"Report upload failed ({r.status_code}): {r.text}"
    report = r.json()
    report_id = report["id"]
    print(f"[OK] 7. PDF Report uploaded: ID {report_id}")

    # 8. Trigger OCR on uploaded report
    r = client.post(f"/reports/{report_id}/ocr", headers=headers)
    assert r.status_code == 200, f"OCR failed ({r.status_code}): {r.text}"
    ocr_result = r.json()
    print(f"[OK] 8. OCR extraction & FAISS indexing completed: status '{ocr_result.get('ocr_status')}'")

    # 9. Get Patient Overview
    r = client.get(f"/patient-overview/{patient_id}", headers=headers)
    assert r.status_code == 200, f"Patient overview failed ({r.status_code}): {r.text}"
    overview = r.json()
    print(f"[OK] 9. Patient Overview loaded: Status='{overview.get('status')}', Flags={overview.get('clinical_flags')}")

    # 10. Ask NeuroScribe — Deterministic lab value question ("What is the hemoglobin level?")
    ask_payload_1 = {
        "patient_id": patient_id,
        "question": "What is the hemoglobin level?",
        "top_k": 5
    }
    r = client.post("/ask/", json=ask_payload_1, headers=headers)
    assert r.status_code == 200, f"Ask question 1 failed ({r.status_code}): {r.text}"
    ask_res_1 = r.json()
    ans_1 = ask_res_1.get("answer")
    print(f"[OK] 10. Ask NeuroScribe (Lab Value): Answer received -> {str(ans_1)[:120]}")

    # 11. Ask NeuroScribe — Free-text LLM question (Groq API test)
    ask_payload_2 = {
        "patient_id": patient_id,
        "question": "Summarize the main clinical abnormalities present in this report.",
        "top_k": 5
    }
    r = client.post("/ask/", json=ask_payload_2, headers=headers)
    assert r.status_code == 200, f"Ask question 2 failed ({r.status_code}): {r.text}"
    ask_res_2 = r.json()
    ans_2 = ask_res_2.get("answer")
    print(f"[OK] 11. Ask NeuroScribe (Groq LLM Fallback): Answer received -> {str(ans_2)[:150]}")

    # 12. Timeline / Trends Endpoint
    r = client.get(f"/timeline/{patient_id}", headers=headers)
    assert r.status_code == 200, f"Timeline endpoint failed ({r.status_code}): {r.text}"
    timeline = r.json()
    print(f"[OK] 12. Patient Timeline/Trends loaded successfully")

    # 13. Multi-Tenant Security / Patient Isolation Test
    # Create User 2
    email_2 = f"other_doctor_{timestamp}@neuroscribe.demo"
    r2 = client.post("/auth/register", json={
        "email": email_2,
        "password": password,
        "full_name": "Dr. Unauthorized",
        "specialty": "Internal Medicine"
    })
    r2 = client.post("/auth/login", json={"email": email_2, "password": password})
    user2_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    # User 2 tries to access User 1's patient overview
    r_unauth = client.get(f"/patient-overview/{patient_id}", headers=user2_headers)
    assert r_unauth.status_code == 404, f"Security Breach! Unauth user got status {r_unauth.status_code}"
    
    # User 2 tries to ask question on User 1's patient
    r_ask_unauth = client.post("/ask/", json=ask_payload_1, headers=user2_headers)
    assert r_ask_unauth.status_code == 404, f"Security Breach! Unauth RAG query got status {r_ask_unauth.status_code}"
    
    # Unauthenticated request (no token)
    r_no_token = client.get(f"/patient-overview/{patient_id}")
    assert r_no_token.status_code == 401, f"Unauthenticated request got status {r_no_token.status_code}"

    print("[OK] 13. Security & Multi-tenant Isolation verified! (404 on unowned patient, 401 on missing token)")

    print("\n==========================================")
    print("  ALL 13 END-TO-END VERIFICATIONS PASSED! ")
    print("==========================================")

if __name__ == "__main__":
    run_verification()
