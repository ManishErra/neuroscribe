import secrets
import sys
import time
import uuid
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import engine
from auth_utils import hash_password

def run_migration():
    print("--- Starting Day 35A Database Migration ---")
    
    # 1. Generate secure legacy owner password
    legacy_owner_id = "d35e8400-e29b-41d4-a716-446655440000"
    raw_password = secrets.token_urlsafe(32)
    hashed_password = hash_password(raw_password)
    
    print(f"Generated secure Legacy Owner UUID: {legacy_owner_id}")
    print(f"Generated secure Legacy Owner email: legacy-owner@neuroscribe.org")
    print("Legacy owner password generated and stored securely.")
    
    # Write credentials securely to a local file (not committed to git)
    creds_file = Path(__file__).resolve().parent.parent.parent / ".env.migration"
    with open(creds_file, "w") as f:
        f.write(f"# Day 35A Migration Legacy Owner Credentials\n")
        f.write(f"LEGACY_OWNER_ID={legacy_owner_id}\n")
        f.write(f"LEGACY_OWNER_EMAIL=legacy-owner@neuroscribe.org\n")
        f.write(f"LEGACY_OWNER_PASSWORD={raw_password}\n")
    print(f"Credentials written locally to: {creds_file}")

    with engine.connect() as conn:
        start_time = time.time()
        trans = conn.begin()
        try:
            # 2. Database Orphan Cleanup Strategy
            print("\nStep 1: Cleaning up orphaned database records...")
            res_t = conn.execute(text("DELETE FROM transcripts WHERE session_id IS NULL OR session_id NOT IN (SELECT id FROM sessions)"))
            print(f"Deleted {res_t.rowcount} orphaned transcripts.")
            
            res_n = conn.execute(text("DELETE FROM notes WHERE session_id IS NULL OR session_id NOT IN (SELECT id FROM sessions)"))
            print(f"Deleted {res_n.rowcount} orphaned notes.")
            
            # Add force_password_reset column to users if not present
            print("\nStep 2: Altering users table (force_password_reset)...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS force_password_reset BOOLEAN NOT NULL DEFAULT FALSE"))
            
            # 3. Create legacy owner user with force_password_reset = True
            print("\nStep 3: Inserting Legacy Owner User...")
            conn.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, name, created_at, force_password_reset)
                    VALUES (:id, :email, :hashed, :name, NOW(), TRUE)
                    ON CONFLICT (email) DO NOTHING
                """),
                {
                    "id": legacy_owner_id,
                    "email": "legacy-owner@neuroscribe.org",
                    "hashed": hashed_password,
                    "name": "Legacy System Owner"
                }
            )
            
            # 4. Add owner_id to patients table and backfill
            print("\nStep 4: Migrating patients table (owner_id column)...")
            conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(id) ON DELETE CASCADE"))
            conn.execute(
                text("UPDATE patients SET owner_id = :legacy_id WHERE owner_id IS NULL"),
                {"legacy_id": legacy_owner_id}
            )
            conn.execute(text("ALTER TABLE patients ALTER COLUMN owner_id SET NOT NULL"))
            
            # 5. Add owner_id to embeddings table and backfill
            print("\nStep 5: Migrating embeddings table (owner_id column)...")
            conn.execute(text("ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(id) ON DELETE CASCADE"))
            
            # Note source backfill
            conn.execute(text("""
                UPDATE embeddings e
                SET owner_id = p.owner_id
                FROM notes n
                JOIN sessions s ON n.session_id = s.id
                JOIN patients p ON s.patient_id = p.id
                WHERE e.source_type = 'note' AND e.source_id = n.id AND e.owner_id IS NULL
            """))
            
            # Report source backfill
            conn.execute(text("""
                UPDATE embeddings e
                SET owner_id = p.owner_id
                FROM reports r
                JOIN patients p ON r.patient_id = p.id
                WHERE e.source_type = 'report' AND e.source_id = r.id AND e.owner_id IS NULL
            """))
            
            # Set leftover embeddings to legacy owner
            conn.execute(
                text("UPDATE embeddings SET owner_id = :legacy_id WHERE owner_id IS NULL"),
                {"legacy_id": legacy_owner_id}
            )
            conn.execute(text("ALTER TABLE embeddings ALTER COLUMN owner_id SET NOT NULL"))
            
            # 6. Create indexes for owner scoping queries
            print("\nStep 6: Creating indexes for owner isolation queries...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_owner_id ON patients(owner_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_embeddings_owner_id ON embeddings(owner_id)"))
            
            trans.commit()
            duration_ms = (time.time() - start_time) * 1000
            print(f"\nTransaction committed successfully in {duration_ms:.2f} ms.")
            print("\nDay 35A Database Migration applied successfully!")
            
        except Exception as e:
            trans.rollback()
            duration_ms = (time.time() - start_time) * 1000
            print(f"\nMigration failed and was rolled back after {duration_ms:.2f} ms: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
