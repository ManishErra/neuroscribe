import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
from sqlalchemy import text

def run_db_audit():
    db = SessionLocal()
    print("--- Running Day 35 Database Migration Audit ---")
    try:
        # 1. Count rows in all tables
        tables = ["patients", "sessions", "transcripts", "notes", "reports", "embeddings", "users"]
        row_counts = {}
        for table in tables:
            res = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            row_counts[table] = res
            print(f"Table {table:<12} | Rows: {res}")
            
        # 2. Check for orphaned records
        print("\n--- Checking for Orphaned Records ---")
        
        # Sessions without patients
        orphan_sessions = db.execute(text(
            "SELECT COUNT(*) FROM sessions s LEFT JOIN patients p ON s.patient_id = p.id WHERE p.id IS NULL"
        )).scalar()
        print(f"Orphaned Sessions (no patient)   : {orphan_sessions}")
        
        # Transcripts without sessions
        orphan_transcripts = db.execute(text(
            "SELECT COUNT(*) FROM transcripts t LEFT JOIN sessions s ON t.session_id = s.id WHERE s.id IS NULL"
        )).scalar()
        print(f"Orphaned Transcripts (no session) : {orphan_transcripts}")
        
        # Notes without sessions
        orphan_notes = db.execute(text(
            "SELECT COUNT(*) FROM notes n LEFT JOIN sessions s ON n.session_id = s.id WHERE s.id IS NULL"
        )).scalar()
        print(f"Orphaned Notes (no session)       : {orphan_notes}")
        
        # Reports without patients
        orphan_reports = db.execute(text(
            "SELECT COUNT(*) FROM reports r LEFT JOIN patients p ON r.patient_id = p.id WHERE p.id IS NULL"
        )).scalar()
        print(f"Orphaned Reports (no patient)     : {orphan_reports}")
        
        # Embeddings without source
        # Since source can be notes or other types, we can check for notes
        orphan_embeddings_notes = db.execute(text(
            "SELECT COUNT(*) FROM embeddings e LEFT JOIN notes n ON e.source_id = n.id WHERE e.source_type = 'note' AND n.id IS NULL"
        )).scalar()
        print(f"Orphaned Embeddings (no note)     : {orphan_embeddings_notes}")

        # 3. List existing user accounts
        print("\n--- Existing User Accounts ---")
        users = db.execute(text("SELECT id, email, name, created_at FROM users")).fetchall()
        if not users:
            print("No users registered in the database.")
        for u in users:
            print(f"ID: {u[0]} | Email: {u[1]:<30} | Name: {u[2]:<15} | Created At: {u[3]}")
            
    except Exception as e:
        print(f"Database query failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_db_audit()
