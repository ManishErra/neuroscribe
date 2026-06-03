import sys
import json
import shutil
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal

def run_faiss_metadata_migration():
    print("=== STARTING DAY 35B FAISS METADATA MIGRATION ===")
    
    backend_dir = Path(__file__).resolve().parent.parent
    metadata_path = backend_dir / "vector_metadata.json"
    backup_path = backend_dir / "vector_metadata.backup.json"
    tmp_path = backend_dir / "vector_metadata.json.tmp"
    
    # STEP 1: Verify source metadata file exists
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Source metadata file not found at: {metadata_path}")
        
    # STEP 2: Automatic Backup Creation
    print(f"Creating metadata backup: {backup_path}")
    shutil.copy2(metadata_path, backup_path)
    
    # STEP 3: Load existing metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    original_count = len(chunks)
    print(f"Loaded {original_count} original metadata chunks from: {metadata_path}")
    
    # STEP 4: Query Database Mappings
    db = SessionLocal()
    mapping = {}
    try:
        query = """
            SELECT r.id, p.owner_id 
            FROM reports r 
            JOIN patients p ON r.patient_id = p.id
        """
        rows = db.execute(text(query)).fetchall()
        for r_id, owner_id in rows:
            mapping[str(r_id)] = str(owner_id)
        print(f"Loaded {len(mapping)} active report-to-owner mappings from database.")
    except Exception as e:
        db.close()
        raise RuntimeError(f"Database query failed during mapping fetch: {e}")
    finally:
        db.close()
        
    # STEP 5: Patch Chunks In-Memory (Loud Failure Enforcement)
    patched_chunks = []
    for idx, chunk in enumerate(chunks):
        r_id = chunk.get("report_id") or chunk.get("report_source")
        if not r_id:
            raise RuntimeError(f"Defect found: Metadata chunk at index {idx} has no report identifier.")
            
        r_id_str = str(r_id)
        
        # Loud failure if database has no owner mapping for the report (silent fallback is disabled)
        if r_id_str not in mapping:
            raise RuntimeError(
                f"LOUD MIGRATION FAILURE: Database contains no ownership records for report_id '{r_id_str}' "
                f"at metadata index {idx}. Fallback is disabled."
            )
            
        # Patch chunk dictionary
        chunk["owner_id"] = mapping[r_id_str]
        patched_chunks.append(chunk)
        
    # STEP 6: Validate Chunk Counts Match Exactly
    patched_count = len(patched_chunks)
    if original_count != patched_count:
        raise RuntimeError(
            f"LOUD MIGRATION FAILURE: Patched count ({patched_count}) does not match "
            f"original count ({original_count}). Aborting replacement."
        )
    print(f"Validation successful: Patched chunk count matches original count ({patched_count}).")
    
    # STEP 7: Atomic Write Replacement
    print(f"Writing to temporary file: {tmp_path}")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(patched_chunks, f, indent=2, ensure_ascii=False)
        
    # Atomically replace the target file using Path.replace() (equivalent to os.replace syscall)
    print(f"Replacing original file atomically: {metadata_path}")
    tmp_path.replace(metadata_path)
    
    print("=== DAY 35B FAISS METADATA MIGRATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        run_faiss_metadata_migration()
    except Exception as exc:
        print(f"Migration Failed with error: {exc}", file=sys.stderr)
        sys.exit(1)
