import sys
import json
import shutil
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal

def run_faiss_metadata_migration():
    print("=== STARTING DAY 35B/PHASE 0 FAISS METADATA MIGRATION ===")
    
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
            SELECT r.id, r.patient_id, p.owner_id 
            FROM reports r 
            JOIN patients p ON r.patient_id = p.id
        """
        rows = db.execute(text(query)).fetchall()
        for r_id, patient_id, owner_id in rows:
            mapping[str(r_id)] = {
                "patient_id": str(patient_id),
                "owner_id": str(owner_id)
            }
        print(f"Loaded {len(mapping)} active report-to-patient mappings from database.")
    except Exception as e:
        db.close()
        raise RuntimeError(f"Database query failed during mapping fetch: {e}")
    finally:
        db.close()
        
    # STEP 5: Patch Chunks In-Memory (Orphaned Chunk Policy Enforcement)
    patched_chunks = []
    active_count = 0
    orphaned_count = 0
    orphaned_reports = set()
    
    for idx, chunk in enumerate(chunks):
        r_id = chunk.get("report_id") or chunk.get("report_source")
        if not r_id:
            raise RuntimeError(f"Defect found: Metadata chunk at index {idx} has no report identifier.")
            
        r_id_str = str(r_id)
        
        # Orphaned Chunk Policy
        if r_id_str not in mapping:
            chunk["migration_status"] = "orphaned"
            chunk["patient_id"] = "orphaned"
            chunk["owner_id"] = "orphaned"
            orphaned_count += 1
            orphaned_reports.add(r_id_str)
        else:
            # Active Chunk Mapping
            db_map = mapping[r_id_str]
            chunk["patient_id"] = db_map["patient_id"]
            chunk["owner_id"] = db_map["owner_id"]
            # Clean up migration_status if it was somehow present
            if "migration_status" in chunk:
                del chunk["migration_status"]
            active_count += 1
            
        patched_chunks.append(chunk)
        
    # STEP 6: Validate Chunk Counts Match Exactly
    patched_count = len(patched_chunks)
    if original_count != patched_count:
        raise RuntimeError(
            f"LOUD MIGRATION FAILURE: Patched count ({patched_count}) does not match "
            f"original count ({original_count}). Aborting replacement."
        )
        
    print(f"Validation successful: Patched chunk count matches original count ({patched_count}).")
    print(f"  - Active chunks successfully patched: {active_count}")
    print(f"  - Orphaned chunks logged and marked  : {orphaned_count}")
    print(f"  - Unique orphaned report IDs        : {list(orphaned_reports)}")
    
    # STEP 7: Atomic Write Replacement
    print(f"Writing to temporary file: {tmp_path}")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(patched_chunks, f, indent=2, ensure_ascii=False)
        
    # Atomically replace the target file using Path.replace() (equivalent to os.replace syscall)
    print(f"Replacing original file atomically: {metadata_path}")
    tmp_path.replace(metadata_path)
    
    print("=== DAY 35B/PHASE 0 FAISS METADATA MIGRATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        run_faiss_metadata_migration()
    except Exception as exc:
        print(f"Migration Failed with error: {exc}", file=sys.stderr)
        sys.exit(1)
