import sys
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal

def run_remediation():
    print("=== STARTING RELEASE REMEDIATION DATA PURGE ===")
    
    db = SessionLocal()
    try:
        # 1. Identify temporary doctors
        doctors = db.execute(text(
            "SELECT id, email FROM users WHERE email LIKE 'doctor-a-%' OR email LIKE 'doctor-b-%'"
        )).fetchall()
        
        doctor_ids = [str(d[0]) for d in doctors]
        doctor_emails = [d[1] for d in doctors]
        print(f"  Identified {len(doctor_ids)} temporary doctor accounts to delete:")
        for email in doctor_emails:
            print(f"    - {email}")
            
        # 2. Identify temporary patients
        patients = db.execute(text(
            "SELECT id, name FROM patients WHERE name IN ('Patient Owned By A', 'Patient C', 'Audit Patient C') OR owner_id::text IN :doc_ids"
        ), {"doc_ids": tuple(doctor_ids) if doctor_ids else ("",)}).fetchall()
        
        patient_ids = [str(p[0]) for p in patients]
        patient_names = [p[1] for p in patients]
        print(f"  Identified {len(patient_ids)} temporary patients to delete:")
        for name in patient_names:
            print(f"    - {name}")
            
        # 3. Identify and delete sessions, transcripts, notes
        session_count = 0
        transcript_count = 0
        note_count = 0
        report_count = 0
        embedding_count = 0
        
        if patient_ids:
            # Sessions
            sessions = db.execute(text(
                "SELECT id FROM sessions WHERE patient_id::text IN :pat_ids"
            ), {"pat_ids": tuple(patient_ids)}).fetchall()
            session_ids = [str(s[0]) for s in sessions]
            session_count = len(session_ids)
            
            if session_ids:
                # Delete notes & transcripts
                res_notes = db.execute(text(
                    "DELETE FROM notes WHERE session_id::text IN :sess_ids"
                ), {"sess_ids": tuple(session_ids)})
                note_count = res_notes.rowcount
                
                res_transcripts = db.execute(text(
                    "DELETE FROM transcripts WHERE session_id::text IN :sess_ids"
                ), {"sess_ids": tuple(session_ids)})
                transcript_count = res_transcripts.rowcount
                
                # Delete sessions
                db.execute(text(
                    "DELETE FROM sessions WHERE id::text IN :sess_ids"
                ), {"sess_ids": tuple(session_ids)})
                
            # Delete reports & embeddings
            res_reports = db.execute(text(
                "DELETE FROM reports WHERE patient_id::text IN :pat_ids"
            ), {"pat_ids": tuple(patient_ids)})
            report_count = res_reports.rowcount
            
            # Since embeddings are tied to notes, let's delete them by owner_id or patient notes
            if doctor_ids:
                res_embeddings = db.execute(text(
                    "DELETE FROM embeddings WHERE owner_id::text IN :doc_ids"
                ), {"doc_ids": tuple(doctor_ids)})
                embedding_count = res_embeddings.rowcount
                
            # Delete patients
            db.execute(text(
                "DELETE FROM patients WHERE id::text IN :pat_ids"
            ), {"pat_ids": tuple(patient_ids)})
            
        # Delete doctors
        if doctor_ids:
            db.execute(text(
                "DELETE FROM users WHERE id::text IN :doc_ids"
            ), {"doc_ids": tuple(doctor_ids)})
            
        db.commit()
        
        print("\n--- Purge Results Summary ---")
        print(f"  Users deleted       : {len(doctor_ids)}")
        print(f"  Patients deleted     : {len(patient_ids)}")
        print(f"  Sessions deleted     : {session_count}")
        print(f"  Transcripts deleted  : {transcript_count}")
        print(f"  Notes deleted        : {note_count}")
        print(f"  Reports deleted      : {report_count}")
        print(f"  Embeddings deleted   : {embedding_count}")
        print("  Database cleanup completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"  FAIL: Database remediation failed: {e}")
        db.close()
        sys.exit(1)
    db.close()

if __name__ == "__main__":
    run_remediation()
