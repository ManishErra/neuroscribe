import sys
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import engine

def run_rollback():
    print("--- Starting Day 35A Database Rollback ---")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Drop indexes
            print("Step 1: Dropping owner isolation indexes...")
            conn.execute(text("DROP INDEX IF EXISTS idx_patients_owner_id"))
            conn.execute(text("DROP INDEX IF EXISTS idx_embeddings_owner_id"))
            
            # 2. Drop owner_id constraint and column from embeddings
            print("Step 2: Reverting embeddings table schema...")
            conn.execute(text("ALTER TABLE embeddings DROP CONSTRAINT IF EXISTS embeddings_owner_id_fkey"))
            conn.execute(text("ALTER TABLE embeddings DROP COLUMN IF EXISTS owner_id"))
            
            # 3. Drop owner_id constraint and column from patients
            print("Step 3: Reverting patients table schema...")
            conn.execute(text("ALTER TABLE patients DROP CONSTRAINT IF EXISTS patients_owner_id_fkey"))
            conn.execute(text("ALTER TABLE patients DROP COLUMN IF EXISTS owner_id"))
            
            # 4. Clean up force_password_reset column from users
            print("Step 4: Reverting users table schema...")
            conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS force_password_reset"))
            
            # 5. Delete legacy owner user
            print("Step 5: Deleting legacy system owner user...")
            conn.execute(
                text("DELETE FROM users WHERE id = :id"),
                {"id": "d35e8400-e29b-41d4-a716-446655440000"}
            )
            
            trans.commit()
            print("\nDay 35A Database Rollback applied successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\nRollback failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_rollback()
