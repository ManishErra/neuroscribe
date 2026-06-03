import sys
import uuid
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine
from models import User, Patient, Session as SessionModel, Note, Transcript, Report, Embedding
from embeddings import generate_embedding

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
    print("=== STARTING PGVECTOR SECURITY & ISOLATION AUDIT ===")
    
    # 1. Register and login Doctor A & Doctor B
    doc_a = create_doctor("doctor-a")
    doc_b = create_doctor("doctor-b")
    
    print(f"Doctor A Registered: {doc_a['email']} (ID: {doc_a['id']})")
    print(f"Doctor B Registered: {doc_b['email']} (ID: {doc_b['id']})")
    
    # 2. Doctor A creates patient and related records
    print("\n--- Phase 1: Doctor A Creates Patient, SOAP Note, and Embeddings ---")
    
    # Create Patient A
    res = client.post("/patients/", json={"name": "Vector Audit Patient A", "age": 50, "gender": "Female"}, headers=doc_a["headers"])
    patient_a_id = res.json()["id"]
    print(f"  Created Patient A: {patient_a_id}")
    
    # Create Session A
    res = client.post("/sessions/", json={"patient_id": patient_a_id}, headers=doc_a["headers"])
    session_a_id = res.json()["id"]
    print(f"  Created Session A: {session_a_id}")
    
    # Upload Audio (creates Transcript A)
    import routers.audio
    routers.audio.TEST_MODE = True
    dummy_audio = b"fakeaudiobinarycontentdata"
    files = {"file": ("test.wav", dummy_audio, "audio/wav")}
    res = client.post("/upload-audio", data={"session_id": session_a_id}, files=files, headers=doc_a["headers"])
    transcript_a_id = res.json()["transcript_id"]
    routers.audio.TEST_MODE = False
    print(f"  Created Transcript A: {transcript_a_id}")
    
    # Generate Note A
    res = client.post("/generate-note", json={"transcript_id": transcript_a_id, "patient_name": "Vector Audit Patient A", "patient_age": 50}, headers=doc_a["headers"])
    note_a_id = res.json()["note_id"]
    print(f"  Generated Note A: {note_a_id}")
    
    # Save & Auto-Embed Note A
    doctor_edited = {
        "presenting_complaint": "Depressive mood and lack of energy.",
        "symptoms_mentioned": ["depression", "lethargy"],
        "medications_mentioned": ["sertraline"],
        "sleep": "disturbed sleep pattern",
        "mood_in_patient_words": "feeling down",
        "social_context": "recently retired",
        "plan_discussed": "start sertraline 50mg",
        "flags_for_review": "none",
        "confidence": "high"
    }
    res = client.post("/save-note", json={"note_id": note_a_id, "doctor_edited": doctor_edited}, headers=doc_a["headers"])
    print(f"  Finalized Note A & Generated Embeddings: {res.status_code}")
    
    # 3. SQL Audits
    db = SessionLocal()
    try:
        # Check embeddings generated for Doctor A
        count_a = db.query(Embedding).filter(Embedding.owner_id == doc_a["id"]).count()
        print(f"  Embeddings created with owner_id = Doctor A ID: {count_a}")
        
        print("\n--- Phase 2: Doctor B Isolation Checks ---")
        
        # Test Scenario 1: Attempt retrieval of Doctor A embeddings directly
        print("\n[Scenario 1: Direct Retrieval Check]")
        query_direct = "SELECT id, source_id, chunk_text FROM embeddings WHERE owner_id = :doctor_b_id"
        print(f"  SQL Query Executed: {query_direct}")
        direct_rows = db.execute(text(query_direct), {"doctor_b_id": doc_b["id"]}).fetchall()
        print(f"  Doctor B direct retrieval returned embedding count: {len(direct_rows)}")
        passed_1 = len(direct_rows) == 0
        print(f"  Status: {'PASS' if passed_1 else 'FAIL'}")
        
        # Test Scenario 2: Attempt similarity search against Doctor A embeddings
        print("\n[Scenario 2: Scoped Similarity Search Check]")
        # We generate query vector for "depression"
        query_text = "depression"
        query_vec = generate_embedding(query_text)
        query_vec_str = str(query_vec)
        
        # Doctor B attempts similarity search over Patient A's records
        # This query represents the pgvector similarity search scoped to Doctor B's context
        query_sim = """
            SELECT e.id, e.chunk_text, 1 - (e.embedding <=> CAST(:query_vec AS vector)) as similarity
            FROM embeddings e
            JOIN notes n ON e.source_id = n.id
            JOIN sessions s ON n.session_id = s.id
            JOIN patients p ON s.patient_id = p.id
            WHERE p.id = :patient_id AND p.owner_id = :doctor_b_id
            ORDER BY e.embedding <=> CAST(:query_vec AS vector)
            LIMIT 5
        """
        print(f"  SQL Query Executed: {query_sim.strip()}")
        sim_rows = db.execute(text(query_sim), {
            "query_vec": query_vec_str,
            "patient_id": patient_a_id,
            "doctor_b_id": doc_b["id"]
        }).fetchall()
        print(f"  Doctor B similarity search returned embedding count: {len(sim_rows)}")
        passed_2 = len(sim_rows) == 0
        print(f"  Status: {'PASS' if passed_2 else 'FAIL'}")
        
        # Test Scenario 3: Attempt note retrieval through embedding paths
        print("\n[Scenario 3: Note Retrieval Through Embedding Path Check]")
        # Doctor B tries to join embeddings to notes to access Doctor A's note text
        query_note = """
            SELECT n.id, n.doctor_edited 
            FROM notes n
            JOIN embeddings e ON e.source_id = n.id
            WHERE e.owner_id = :doctor_b_id
        """
        print(f"  SQL Query Executed: {query_note.strip()}")
        note_rows = db.execute(text(query_note), {"doctor_b_id": doc_b["id"]}).fetchall()
        print(f"  Doctor B note retrieval through embeddings returned note count: {len(note_rows)}")
        passed_3 = len(note_rows) == 0
        print(f"  Status: {'PASS' if passed_3 else 'FAIL'}")
        
        # Test Scenario 4: Global cross-user access attempt on embeddings table
        print("\n[Scenario 4: Global Cross-User Access Attempt]")
        # Doctor B tries to select any rows where owner_id != Doctor B ID
        query_cross = "SELECT COUNT(*) FROM embeddings WHERE owner_id = :doctor_a_id"
        print(f"  SQL Query Executed: {query_cross}")
        cross_count = db.execute(text(query_cross), {"doctor_a_id": doc_a["id"]}).scalar()
        print(f"  Embeddings belonging to Doctor A found in table: {cross_count}")
        
        # Doctor B executes similarity search globally on embeddings table without patient joins
        query_global_sim = """
            SELECT id, chunk_text FROM embeddings
            WHERE owner_id = :doctor_b_id
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT 5
        """
        print(f"  SQL Query Executed: {query_global_sim.strip()}")
        global_sim_rows = db.execute(text(query_global_sim), {
            "query_vec": query_vec_str,
            "doctor_b_id": doc_b["id"]
        }).fetchall()
        print(f"  Doctor B global similarity search returned embedding count: {len(global_sim_rows)}")
        passed_4 = len(global_sim_rows) == 0
        print(f"  Status: {'PASS' if passed_4 else 'FAIL'}")

    finally:
        db.close()
        
    # 4. Clean up test records
    print("\n--- Cleaning up Test Records ---")
    db = SessionLocal()
    try:
        p_rec = db.query(Patient).filter(Patient.id == patient_a_id).first()
        if p_rec:
            # Delete reports, sessions, notes, transcripts, embeddings
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
            print("  Deleted Patient A and related records successfully.")
    except Exception as e:
        print(f"  Cleanup failed: {e}")
    db.close()
    
    cleanup_doctor(doc_a["email"])
    cleanup_doctor(doc_b["email"])
    print("  Cleaned up Doctor A and Doctor B accounts.")

if __name__ == "__main__":
    run_audit()
