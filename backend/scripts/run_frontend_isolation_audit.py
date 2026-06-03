import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User, Patient, Session as SessionModel, Note, Transcript, Report, Embedding

client = TestClient(app)

def create_doctor(email_prefix: str):
    email = f"{email_prefix}-{uuid.uuid4().hex[:6]}@neuroscribe.org"
    password = "SecurePassword123!"
    name = f"{email_prefix.capitalize()} Clinician"
    
    res = client.post("/auth/register", json={"email": email, "password": password, "name": name})
    if res.status_code != 201:
        print(f"Failed to register doctor {email}: {res.text}")
        sys.exit(1)
        
    user_id = res.json()["id"]
        
    res_login = client.post("/auth/login", json={"email": email, "password": password})
    if res_login.status_code != 200:
        print(f"Failed to login doctor {email}: {res_login.text}")
        sys.exit(1)
        
    token = res_login.json()["access_token"]
    return {"email": email, "token": token, "id": user_id, "headers": {"Authorization": f"Bearer {token}"}}

def cleanup_doctor(doctor_email: str):
    db = SessionLocal()
    user = db.query(User).filter(User.email == doctor_email).first()
    if user:
        db.delete(user)
        db.commit()
    db.close()

def run_audit():
    print("=== STARTING FRONTEND OWNERSHIP ISOLATION AUDIT ===")
    
    # 1. Register and login Doctor A & Doctor B
    doc_a = create_doctor("doctor-a")
    doc_b = create_doctor("doctor-b")
    
    print(f"Doctor A: {doc_a['email']}")
    print(f"Doctor B: {doc_b['email']}")
    
    # 2. Doctor A creates patient and related records
    print("\n--- Creating Test Records for Doctor A ---")
    
    # Create Patient A
    res = client.post("/patients/", json={"name": "Audit Patient A", "age": 42, "gender": "Male"}, headers=doc_a["headers"])
    patient_a_id = res.json()["id"]
    print(f"Created Patient A ID: {patient_a_id}")
    
    # Create Session A
    res = client.post("/sessions/", json={"patient_id": patient_a_id}, headers=doc_a["headers"])
    session_a_id = res.json()["id"]
    print(f"Created Session A ID: {session_a_id}")
    
    # Upload Audio (creates Transcript A)
    import routers.audio
    routers.audio.TEST_MODE = True
    dummy_audio = b"fakeaudiobinarycontentdata"
    files = {"file": ("test.wav", dummy_audio, "audio/wav")}
    res = client.post("/upload-audio", data={"session_id": session_a_id}, files=files, headers=doc_a["headers"])
    transcript_a_id = res.json()["transcript_id"]
    routers.audio.TEST_MODE = False
    print(f"Created Transcript A ID: {transcript_a_id}")
    
    # Generate Note A
    res = client.post("/generate-note", json={"transcript_id": transcript_a_id, "patient_name": "Audit Patient A", "patient_age": 42}, headers=doc_a["headers"])
    note_a_id = res.json()["note_id"]
    print(f"Created Note A ID: {note_a_id}")
    
    # Save Note A
    doctor_edited = {
        "presenting_complaint": "Anxiety and sleep problems.",
        "symptoms_mentioned": ["anxiety", "insomnia"],
        "medications_mentioned": ["melatonin"],
        "sleep": "poor sleep quality",
        "mood_in_patient_words": "feeling stressed",
        "social_context": "high work stress",
        "plan_discussed": "refer to therapist",
        "flags_for_review": "none",
        "confidence": "high"
    }
    res = client.post("/save-note", json={"note_id": note_a_id, "doctor_edited": doctor_edited}, headers=doc_a["headers"])
    print(f"Saved and finalized Note A: {res.status_code}")

    # Create Report A via API
    res = client.post(
        "/reports/",
        json={
            "patient_id": patient_a_id,
            "file_path": "uploads/reports/audit_report.pdf",
            "original_filename": "audit_report.pdf",
            "mime_type": "application/pdf",
            "title": "Audit Lab Report",
            "report_date": "2026-06-01"
        },
        headers=doc_a["headers"]
    )
    report_a_id = res.json()["id"]
    print(f"Created Report A ID: {report_a_id} via API")
    
    # Mark Report A as ready with dummy OCR text in database
    db = SessionLocal()
    rep = db.query(Report).filter(Report.id == report_a_id).first()
    if rep:
        rep.ocr_status = "ready"
        rep.ocr_text = "Hemoglobin is normal at 14.5 g/dL. Glucose is 95 mg/dL."
        db.commit()
    db.close()
    print("Marked Report A as ready in database.")
    
    # 3. Simulate Frontend requests for all 9 screens
    screens = [
        ("Dashboard", [
            ("GET", "/patients/", None),
            ("GET", f"/patient-overview/{patient_a_id}", None)
        ]),
        ("Patient Directory", [
            ("GET", "/patients/", None)
        ]),
        ("Patient Profile", [
            ("GET", f"/patients/{patient_a_id}", None)
        ]),
        ("Sessions", [
            ("GET", f"/sessions/patient/{patient_a_id}", None),
            ("GET", f"/sessions/{session_a_id}", None)
        ]),
        ("Reports", [
            ("GET", f"/reports/patient/{patient_a_id}", None)
        ]),
        ("Timeline", [
            ("GET", f"/timeline/{patient_a_id}", None)
        ]),
        ("Insights", [
            ("GET", f"/patient-insights/{patient_a_id}", None)
        ]),
        ("Comparison", [
            ("GET", f"/compare/{patient_a_id}", None)
        ]),
        ("Semantic Search Hub", [
            ("POST", "/ask/", {"question": "What is the hemoglobin level for Patient A?"})
        ])
    ]
    
    print("\n--- Auditing Frontend Screens ---")
    
    results = {}
    for screen, requests in screens:
        print(f"\nScreen: [{screen}]")
        results[screen] = []
        for method, route, body in requests:
            # Execute as Doctor A
            if method == "GET":
                res_a = client.get(route, headers=doc_a["headers"])
            else:
                res_a = client.post(route, json=body, headers=doc_a["headers"])
                
            # Execute as Doctor B
            if method == "GET":
                res_b = client.get(route, headers=doc_b["headers"])
            else:
                res_b = client.post(route, json=body, headers=doc_b["headers"])
                
            # Check leakage
            status_a = res_a.status_code
            status_b = res_b.status_code
            
            # Determine PASS/FAIL logic
            is_isolated = False
            leak_reason = ""
            
            if route == "/patients/":
                # Directory list check
                patients_a = [p["id"] for p in res_a.json()]
                patients_b = [p["id"] for p in res_b.json()]
                if patient_a_id in patients_a and patient_a_id not in patients_b:
                    is_isolated = True
                else:
                    is_isolated = False
                    leak_reason = "Patient A leaked in Doctor B list"
            elif route == "/ask/":
                # FAISS/RAG search check - Day 35B is NOT implemented yet
                # So we expect global search to return same results (non-isolated)
                is_isolated = False
                leak_reason = "FAISS/RAG global search query matches across doctors (Day 35B target)"
            else:
                # Direct resource check (should return 404 for Doctor B)
                if status_a == 200 and status_b == 404:
                    is_isolated = True
                else:
                    is_isolated = False
                    leak_reason = f"Doc A: {status_a} | Doc B: {status_b} (expected 404)"
                    
            print(f"  Request: {method} {route}")
            print(f"    Doctor A Response: {status_a} | Size: {len(res_a.text)} bytes")
            print(f"    Doctor B Response: {status_b} | Size: {len(res_b.text)} bytes")
            print(f"    Status: {'PASS' if is_isolated else 'FAIL'} {('(' + leak_reason + ')') if leak_reason else ''}")
            
            # Store audit details
            results[screen].append({
                "method": method,
                "route": route,
                "body": body,
                "doc_a_status": status_a,
                "doc_a_text": res_a.text[:400], # Keep snippet
                "doc_b_status": status_b,
                "doc_b_text": res_b.text[:400], # Keep snippet
                "isolated": is_isolated,
                "reason": leak_reason
            })
            
    # Clean up test records
    print("\n--- Cleaning up Test Records ---")
    db = SessionLocal()
    try:
        p_rec = db.query(Patient).filter(Patient.id == patient_a_id).first()
        if p_rec:
            # Delete reports, sessions, notes, transcripts
            db.query(Report).filter(Report.patient_id == patient_a_id).delete()
            db.query(Embedding).filter(Embedding.owner_id == doc_a["id"]).delete()
            sessions_rec = db.query(SessionModel).filter(SessionModel.patient_id == patient_a_id).all()
            for s in sessions_rec:
                db.query(Note).filter(Note.session_id == s.id).delete()
                db.query(Transcript).filter(Transcript.session_id == s.id).delete()
                db.delete(s)
            db.commit()
            
            db.delete(p_rec)
            db.commit()
            print("Deleted Patient A and related records.")
    except Exception as e:
        print(f"Cleanup failed: {e}")
    db.close()
    
    cleanup_doctor(doc_a["email"])
    cleanup_doctor(doc_b["email"])
    print("Cleaned up Doctor A and Doctor B accounts.")
    
    return results

if __name__ == "__main__":
    run_audit()
