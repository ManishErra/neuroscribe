import sys
import json
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal

def run_metadata_audit():
    print("=== FAISS METADATA MAPPING AUDIT ===")
    
    # 1. Locate and load vector_metadata.json
    backend_dir = Path(__file__).resolve().parent.parent
    metadata_file = backend_dir / "vector_metadata.json"
    
    if not metadata_file.is_file():
        print(f"Error: vector_metadata.json not found at {metadata_file}")
        sys.exit(1)
        
    with open(metadata_file, "r") as f:
        chunks = json.load(f)
        
    print(f"Loaded vector_metadata.json from: {metadata_file}")
    
    # 2. Query database for report -> patient -> owner_id mapping
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
        print(f"Loaded {len(mapping)} report-to-owner mappings from database.")
    except Exception as e:
        print(f"Database query failed: {e}")
        db.close()
        sys.exit(1)
    db.close()
    
    # 3. Analyze chunks
    total_chunks = len(chunks)
    chunks_with_id = 0
    chunks_missing_id = 0
    unique_report_ids = set()
    report_ids_in_db = set()
    report_ids_missing_db = set()
    resolved_chunks = 0
    unresolved_chunks = 0
    
    sample_unresolved = []
    sample_orphan_ids = []
    
    for idx, chunk in enumerate(chunks):
        r_id = chunk.get("report_id")
        
        # Fallback to report_source if report_id missing
        if not r_id:
            r_id = chunk.get("report_source")
            
        if r_id:
            chunks_with_id += 1
            r_id_str = str(r_id)
            unique_report_ids.add(r_id_str)
            
            if r_id_str in mapping:
                report_ids_in_db.add(r_id_str)
                resolved_chunks += 1
            else:
                report_ids_missing_db.add(r_id_str)
                unresolved_chunks += 1
                if len(sample_unresolved) < 3:
                    sample_unresolved.append(chunk)
                if r_id_str not in sample_orphan_ids:
                    sample_orphan_ids.append(r_id_str)
        else:
            chunks_missing_id += 1
            unresolved_chunks += 1
            if len(sample_unresolved) < 3:
                sample_unresolved.append(chunk)
                
    # 4. Display Results
    print(f"\n--- Audit Summary Metrics ---")
    print(f"Total metadata chunks processed: {total_chunks}")
    print(f"Chunks containing report_id    : {chunks_with_id}")
    print(f"Chunks missing report_id       : {chunks_missing_id}")
    print(f"Unique report_ids referenced   : {len(unique_report_ids)}")
    print(f"Report_ids existing in DB      : {len(report_ids_in_db)}")
    print(f"Report_ids missing from DB     : {len(report_ids_missing_db)}")
    print(f"Chunks successfully resolved   : {resolved_chunks}")
    print(f"Chunks unresolved              : {unresolved_chunks}")
    
    # Check classification
    all_mapped = (unresolved_chunks == 0)
    print(f"\nClassification: {'PASS' if all_mapped else 'FAIL'}")
    
    if sample_unresolved:
        print("\n--- Sample Unresolved Chunks ---")
        for i, c in enumerate(sample_unresolved):
            print(f"Sample {i+1}: {json.dumps(c)[:300]}...")
            
    if sample_orphan_ids:
        print("\n--- Sample Orphan Report IDs (Missing from DB) ---")
        for i, oid in enumerate(sample_orphan_ids[:5]):
            print(f"Orphan {i+1}: {oid}")
            
if __name__ == "__main__":
    run_metadata_audit()
