import sys
import json
import random
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
import faiss

def run_faiss_consistency_audit():
    print("=== STARTING FAISS & METADATA CONSISTENCY AUDIT ===")
    
    backend_dir = Path(__file__).resolve().parent.parent
    index_file = backend_dir / "vector.index"
    metadata_file = backend_dir / "vector_metadata.json"
    
    audit_passed = True
    
    # 1. Load FAISS index and get vector count
    if not index_file.is_file():
        print(f"  FAIL: FAISS index file not found at: {index_file}")
        sys.exit(1)
        
    index = faiss.read_index(str(index_file))
    faiss_vector_count = index.ntotal
    print(f"  FAISS vector count (vector.index)  : {faiss_vector_count}")
    
    # 2. Load Metadata and get record count
    if not metadata_file.is_file():
        print(f"  FAIL: Metadata file not found at: {metadata_file}")
        sys.exit(1)
        
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata_records = json.load(f)
    metadata_record_count = len(metadata_records)
    print(f"  Metadata record count (vector_metadata.json): {metadata_record_count}")
    
    # 3. Consistency check
    count_match = (faiss_vector_count == metadata_record_count)
    print(f"  Counts match (faiss == metadata)   : {'PASS' if count_match else 'FAIL'}")
    if not count_match:
        audit_passed = False
        
    # 4. Random sampling audit
    print("\n--- Random Sampling Check (10 Chunks) ---")
    random.seed(42)  # Seed for deterministic and reproducible sampling
    sampled_indices = random.sample(range(metadata_record_count), min(10, metadata_record_count))
    
    db = SessionLocal()
    try:
        # Load all existing report IDs and user IDs for fast lookup
        db_report_ids = {str(r[0]) for r in db.execute(text("SELECT id FROM reports")).fetchall()}
        db_user_ids = {str(u[0]) for u in db.execute(text("SELECT id FROM users")).fetchall()}
        print(f"  Loaded {len(db_report_ids)} reports and {len(db_user_ids)} users from DB for verification.")
    except Exception as e:
        print(f"  FAIL: Database fetch failed: {e}")
        db.close()
        sys.exit(1)
    db.close()
    
    sample_failures = 0
    for i, idx in enumerate(sampled_indices):
        chunk = metadata_records[idx]
        print(f"\n  [Sample #{i+1}] Metadata Index: {idx}")
        
        report_id = chunk.get("report_id") or chunk.get("report_source")
        owner_id = chunk.get("owner_id")
        
        print(f"    report_id : {report_id}")
        print(f"    owner_id  : {owner_id}")
        
        # Verify fields exist
        if not report_id:
            print("    FAIL: report_id missing in metadata chunk.")
            sample_failures += 1
            continue
        if not owner_id:
            print("    FAIL: owner_id missing in metadata chunk.")
            sample_failures += 1
            continue
            
        report_id_str = str(report_id)
        owner_id_str = str(owner_id)
        
        # Verify db references
        report_exists = report_id_str in db_report_ids
        owner_exists = owner_id_str in db_user_ids
        
        print(f"    Report exists in DB   : {'YES' if report_exists else 'NO'}")
        print(f"    Owner exists in users : {'YES' if owner_exists else 'NO'}")
        
        if not report_exists:
            print(f"    FAIL: report_id '{report_id_str}' does not exist in DB (dangling reference).")
            sample_failures += 1
        if not owner_exists:
            print(f"    FAIL: owner_id '{owner_id_str}' does not exist in users table (dangling reference).")
            sample_failures += 1
            
    print(f"\n  Sampling audit complete. Total sample check failures: {sample_failures}")
    if sample_failures > 0:
        audit_passed = False
        
    # 5. Final Classification
    print("\n--- Final Classification ---")
    if audit_passed:
        print("FINAL AUDIT RESULT: PASS")
        sys.exit(0)
    else:
        print("FINAL AUDIT RESULT: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    run_faiss_consistency_audit()
