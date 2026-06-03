import sys
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal

def run_integrity_audit():
    db = SessionLocal()
    print("=== DAY 35A DATABASE INTEGRITY AUDIT SCRIPTS ===")
    
    try:
        # 1. PostgreSQL schema inspection
        print("\n--- 1. Schema Inspection ---")
        
        schema_checks = [
            ("patients", "owner_id"),
            ("embeddings", "owner_id"),
            ("users", "force_password_reset")
        ]
        
        for table, col in schema_checks:
            query = f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
            print(f"Executing: {query}")
            res = db.execute(text(query)).fetchone()
            if res:
                print(f"  Result: Column '{res[0]}' exists on '{table}' | Type: {res[1]} | Nullable: {res[2]} -> PASS")
            else:
                print(f"  Result: Column '{col}' NOT FOUND on '{table}' -> FAIL")

        # 2. PostgreSQL index inspection
        print("\n--- 2. Index Inspection ---")
        
        index_checks = [
            ("patients", "idx_patients_owner_id"),
            ("embeddings", "idx_embeddings_owner_id")
        ]
        
        for table, index in index_checks:
            query = f"SELECT indexname, indexdef FROM pg_indexes WHERE tablename='{table}' AND indexname='{index}'"
            print(f"Executing: {query}")
            res = db.execute(text(query)).fetchone()
            if res:
                print(f"  Result: Index '{res[0]}' exists on '{table}' | Definition: {res[1]} -> PASS")
            else:
                print(f"  Result: Index '{index}' NOT FOUND on '{table}' -> FAIL")

        # 3. Ownership backfill verification
        print("\n--- 3. Ownership Backfill Verification ---")
        
        null_p_query = "SELECT COUNT(*) FROM patients WHERE owner_id IS NULL"
        print(f"Executing: {null_p_query}")
        null_p_count = db.execute(text(null_p_query)).scalar()
        print(f"  Patients with NULL owner_id: {null_p_count} -> {'PASS' if null_p_count == 0 else 'FAIL'}")

        null_e_query = "SELECT COUNT(*) FROM embeddings WHERE owner_id IS NULL"
        print(f"Executing: {null_e_query}")
        null_e_count = db.execute(text(null_e_query)).scalar()
        print(f"  Embeddings with NULL owner_id: {null_e_count} -> {'PASS' if null_e_count == 0 else 'FAIL'}")

        dist_p_query = "SELECT owner_id, COUNT(*) FROM patients GROUP BY owner_id"
        print(f"Executing: {dist_p_query}")
        dist_p = db.execute(text(dist_p_query)).fetchall()
        print("  Distribution of owner_id across patients:")
        for row in dist_p:
            print(f"    owner_id: {row[0]} | Count: {row[1]}")

        dist_e_query = "SELECT owner_id, COUNT(*) FROM embeddings GROUP BY owner_id"
        print(f"Executing: {dist_e_query}")
        dist_e = db.execute(text(dist_e_query)).fetchall()
        print("  Distribution of owner_id across embeddings:")
        for row in dist_e:
            print(f"    owner_id: {row[0]} | Count: {row[1]}")

        # 4. Legacy owner verification
        print("\n--- 4. Legacy Owner Verification ---")
        legacy_id = "d35e8400-e29b-41d4-a716-446655440000"
        legacy_query = f"SELECT id, email, name, force_password_reset FROM users WHERE id = '{legacy_id}'"
        print(f"Executing: {legacy_query}")
        legacy_user = db.execute(text(legacy_query)).fetchone()
        if legacy_user:
            print(f"  Legacy user exists -> PASS")
            print(f"    ID: {legacy_user[0]}")
            print(f"    Email: {legacy_user[1]}")
            print(f"    Name: {legacy_user[2]}")
            print(f"    force_password_reset: {legacy_user[3]} -> {'PASS' if legacy_user[3] else 'FAIL'}")
        else:
            print(f"  Legacy user with ID {legacy_id} NOT FOUND -> FAIL")

        # 5. Orphan verification
        print("\n--- 5. Orphan Verification ---")
        
        orphan_t_query = "SELECT COUNT(*) FROM transcripts WHERE session_id IS NULL"
        print(f"Executing: {orphan_t_query}")
        orphan_t_count = db.execute(text(orphan_t_query)).scalar()
        print(f"  Transcripts where session_id IS NULL: {orphan_t_count}")
        
        orphan_n_query = "SELECT COUNT(*) FROM notes WHERE session_id IS NULL"
        print(f"Executing: {orphan_n_query}")
        orphan_n_count = db.execute(text(orphan_n_query)).scalar()
        print(f"  Notes where session_id IS NULL: {orphan_n_count}")
        
        print(f"  Confirmation: Do these records still exist? "
              f"{'YES (still exist after Day 35A)' if (orphan_t_count > 0 or orphan_n_count > 0) else 'NO (deleted)'}")

    except Exception as e:
        print(f"Audit failed with exception: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_integrity_audit()
