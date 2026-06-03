import sys
import uuid
import secrets
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine
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

def run_verification():
    print("\n--- DAY 35A CLINICIAN ISOLATION VERIFICATION MATRIX ---")
    
    # 1. Register and login Doctor A & Doctor B
    doc_a = create_doctor("doctor-a")
    doc_b = create_doctor("doctor-b")
    
    print(f"Doctor A logged in: {doc_a['email']}")
    print(f"Doctor B logged in: {doc_b['email']}")
    
    all_passed = True
    
    try:
        # 2. Doctor A creates a Patient
        print("\nStep 1: Doctor A creates a patient...")
        res_create = client.post(
            "/patients/",
            json={"name": "Patient Owned By A", "age": 35, "gender": "Female"},
            headers=doc_a["headers"]
        )
        if res_create.status_code != 200:
            print(f"  FAIL: Doctor A could not create patient: {res_create.text}")
            all_passed = False
            return
        
        patient_a_id = res_create.json()["id"]
        print(f"  PASS: Patient created with ID: {patient_a_id}")
        
        # 3. Doctor A gets Patient list
        print("\nStep 2: Testing Patient Directory listings scoping...")
        res_list_a = client.get("/patients/", headers=doc_a["headers"])
        patients_a = [p["id"] for p in res_list_a.json()]
        passed_list_a = patient_a_id in patients_a
        print(f"  Doctor A Patient Directory includes Patient A: {'PASS' if passed_list_a else 'FAIL'}")
        if not passed_list_a:
            all_passed = False
            
        res_list_b = client.get("/patients/", headers=doc_b["headers"])
        patients_b = [p["id"] for p in res_list_b.json()]
        passed_list_b = patient_a_id not in patients_b
        print(f"  Doctor B Patient Directory excludes Patient A: {'PASS' if passed_list_b else 'FAIL'}")
        if not passed_list_b:
            all_passed = False
            
        # 4. Doctor B attempts to view Patient A (should fail 404)
        print("\nStep 3: Testing single patient retrieval scoping...")
        res_get_a = client.get(f"/patients/{patient_a_id}", headers=doc_a["headers"])
        print(f"  Doctor A GET /patients/PatientA_ID           | Expected: 200 | Actual: {res_get_a.status_code} | {'PASS' if res_get_a.status_code == 200 else 'FAIL'}")
        if res_get_a.status_code != 200:
            all_passed = False
            
        res_get_b = client.get(f"/patients/{patient_a_id}", headers=doc_b["headers"])
        print(f"  Doctor B GET /patients/PatientA_ID (Excludes) | Expected: 404 | Actual: {res_get_b.status_code} | {'PASS' if res_get_b.status_code == 404 else 'FAIL'}")
        if res_get_b.status_code != 404:
            all_passed = False
            
        # 5. Doctor B attempts to create session for Patient A
        print("\nStep 4: Testing session creation scoping...")
        res_sess_b = client.post("/sessions/", json={"patient_id": patient_a_id}, headers=doc_b["headers"])
        print(f"  Doctor B POST /sessions/ (Excludes Patient A) | Expected: 404 | Actual: {res_sess_b.status_code} | {'PASS' if res_sess_b.status_code == 404 else 'FAIL'}")
        if res_sess_b.status_code != 404:
            all_passed = False
            
        # Doctor A creates session
        res_sess_a = client.post("/sessions/", json={"patient_id": patient_a_id}, headers=doc_a["headers"])
        session_id = res_sess_a.json()["id"]
        
        # 6. Doctor B attempts to view Doctor A's Session details
        print("\nStep 5: Testing single session retrieval scoping...")
        res_sess_get_b = client.get(f"/sessions/{session_id}", headers=doc_b["headers"])
        print(f"  Doctor B GET /sessions/SessionA_ID            | Expected: 404 | Actual: {res_sess_get_b.status_code} | {'PASS' if res_sess_get_b.status_code == 404 else 'FAIL'}")
        if res_sess_get_b.status_code != 404:
            all_passed = False
            
        # 7. Doctor B attempts to upload audio to Doctor A's Session
        print("\nStep 6: Testing audio upload scoping...")
        dummy_audio = b"fakeaudiobinarycontentdata"
        files = {"file": ("test.wav", dummy_audio, "audio/wav")}
        res_audio_b = client.post(
            "/upload-audio",
            data={"session_id": session_id},
            files=files,
            headers=doc_b["headers"]
        )
        print(f"  Doctor B POST /upload-audio (Excludes SessionA)| Expected: 404 | Actual: {res_audio_b.status_code} | {'PASS' if res_audio_b.status_code == 404 else 'FAIL'}")
        if res_audio_b.status_code != 404:
            all_passed = False

        # Doctor A uploads audio to generate transcript in test mode
        # Enable TEST_MODE temporarily
        import routers.audio
        routers.audio.TEST_MODE = True
        res_audio_a = client.post(
            "/upload-audio",
            data={"session_id": session_id},
            files=files,
            headers=doc_a["headers"]
        )
        routers.audio.TEST_MODE = False
        transcript_id = res_audio_a.json()["transcript_id"]
        
        # 8. Doctor B attempts to generate note for Doctor A's transcript
        print("\nStep 7: Testing note generation scoping...")
        res_note_b = client.post(
            "/generate-note",
            json={"transcript_id": transcript_id, "patient_name": "Patient Owned By A", "patient_age": 35},
            headers=doc_b["headers"]
        )
        print(f"  Doctor B POST /generate-note (Excludes Trans) | Expected: 404 | Actual: {res_note_b.status_code} | {'PASS' if res_note_b.status_code == 404 else 'FAIL'}")
        if res_note_b.status_code != 404:
            all_passed = False
            
        # 9. Doctor B attempts to query timeline or comparison
        print("\nStep 8: Testing timeline, insights, and comparison scoping...")
        res_timeline_b = client.get(f"/timeline/{patient_a_id}", headers=doc_b["headers"])
        print(f"  Doctor B GET /timeline/PatientA_ID            | Expected: 404 | Actual: {res_timeline_b.status_code} | {'PASS' if res_timeline_b.status_code == 404 else 'FAIL'}")
        if res_timeline_b.status_code != 404:
            all_passed = False
            
        res_compare_b = client.get(f"/compare/{patient_a_id}", headers=doc_b["headers"])
        print(f"  Doctor B GET /compare/PatientA_ID             | Expected: 404 | Actual: {res_compare_b.status_code} | {'PASS' if res_compare_b.status_code == 404 else 'FAIL'}")
        if res_compare_b.status_code != 404:
            all_passed = False
            
        res_insights_b = client.get(f"/patient-insights/{patient_a_id}", headers=doc_b["headers"])
        print(f"  Doctor B GET /patient-insights/PatientA_ID    | Expected: 404 | Actual: {res_insights_b.status_code} | {'PASS' if res_insights_b.status_code == 404 else 'FAIL'}")
        if res_insights_b.status_code != 404:
            all_passed = False

        res_overview_b = client.get(f"/patient-overview/{patient_a_id}", headers=doc_b["headers"])
        print(f"  Doctor B GET /patient-overview/PatientA_ID    | Expected: 404 | Actual: {res_overview_b.status_code} | {'PASS' if res_overview_b.status_code == 404 else 'FAIL'}")
        if res_overview_b.status_code != 404:
            all_passed = False
            
    finally:
        # Clean up database test records safely
        print("\nCleaning up test clinical records...")
        db = SessionLocal()
        try:
            # We delete Patient A and cascades
            p_rec = db.query(Patient).filter(Patient.id == patient_a_id).first()
            if p_rec:
                # Manually delete notes, transcripts, sessions first
                sessions_rec = db.query(SessionModel).filter(SessionModel.patient_id == patient_a_id).all()
                for s in sessions_rec:
                    db.query(Note).filter(Note.session_id == s.id).delete()
                    db.query(Transcript).filter(Transcript.session_id == s.id).delete()
                    db.delete(s)
                db.commit()  # Commit sessions deletion first
                
                db.delete(p_rec)
                db.commit()  # Commit patient deletion second
            print("  PASS: Test clinical records deleted.")
        except Exception as e:
            print(f"  FAIL: Cleanup of clinical records failed: {e}")
        db.close()
        
        cleanup_doctor(doc_a["email"])
        cleanup_doctor(doc_b["email"])
        print("  PASS: Test clinician user accounts deleted.")

    # 10. Database Rollback and Migration Validation Check
    print("\n--- DAY 35A DATABASE ROLLBACK & DATA PRESERVATION VALIDATION ---")
    
    db = SessionLocal()
    # Log current row counts
    count_p_before = db.query(Patient).count()
    count_s_before = db.query(SessionModel).count()
    count_n_before = db.query(Note).count()
    count_r_before = db.query(Report).count()
    count_e_before = db.query(Embedding).count()
    db.close()
    
    print(f"Row counts before rollback:")
    print(f"  Patients    : {count_p_before}")
    print(f"  Sessions    : {count_s_before}")
    print(f"  Notes       : {count_n_before}")
    print(f"  Reports     : {count_r_before}")
    print(f"  Embeddings  : {count_e_before}")
    
    # Run Rollback Script
    print("\nExecuting database rollback script...")
    import scripts.rollback_day35a_migration as rollback_module
    rollback_module.run_rollback()
    
    # Verify owner_id columns are deleted
    print("\nVerifying database schema reversion...")
    with engine.connect() as conn:
        columns_patient = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='patients' AND column_name='owner_id'"
        )).fetchall()
        passed_revert_p = len(columns_patient) == 0
        print(f"  owner_id removed from 'patients' table  : {'PASS' if passed_revert_p else 'FAIL'}")
        if not passed_revert_p:
            all_passed = False
            
        columns_embedding = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='embeddings' AND column_name='owner_id'"
        )).fetchall()
        passed_revert_e = len(columns_embedding) == 0
        print(f"  owner_id removed from 'embeddings' table: {'PASS' if passed_revert_e else 'FAIL'}")
        if not passed_revert_e:
            all_passed = False
            
    # Run Re-Migration Script
    print("\nRe-executing database migration script...")
    import scripts.apply_day35_migration as migration_module
    migration_module.run_migration()
    
    # Verify row counts match exactly (Data Preservation)
    print("\nVerifying data preservation after re-migration...")
    db = SessionLocal()
    count_p_after = db.query(Patient).count()
    count_s_after = db.query(SessionModel).count()
    count_n_after = db.query(Note).count()
    count_r_after = db.query(Report).count()
    count_e_after = db.query(Embedding).count()
    db.close()
    
    passed_preservation = (
        count_p_before == count_p_after and
        count_s_before == count_s_after and
        count_n_before == count_n_after and
        count_r_before == count_r_after and
        count_e_before == count_e_after
    )
    print(f"  All table row counts match exactly      : {'PASS' if passed_preservation else 'FAIL'}")
    if not passed_preservation:
        all_passed = False
        
    if all_passed:
        print("\nALL DAY 35A VERIFICATION MATRIX CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME VERIFICATION MATRIX CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
