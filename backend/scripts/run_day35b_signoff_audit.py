import sys
import json
import uuid
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User, Patient, Report
import report_vector_store

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

def run_signoff_audit():
    print("=== STARTING DAY 35B FINAL PERSISTENCE SIGN-OFF AUDIT ===")
    
    backend_dir = Path(__file__).resolve().parent.parent
    metadata_file = backend_dir / "vector_metadata.json"
    
    audit_passed = True
    
    # ----------------------------------------------------
    # 1. Metadata Reload Audit
    # ----------------------------------------------------
    print("\n--- 1. Metadata Reload Audit ---")
    
    # Check count on disk
    if not metadata_file.is_file():
        print(f"  FAIL: vector_metadata.json not found at {metadata_file}")
        sys.exit(1)
        
    with open(metadata_file, "r", encoding="utf-8") as f:
        disk_chunks = json.load(f)
    disk_count = len(disk_chunks)
    print(f"  Metadata chunks on disk  : {disk_count}")
    
    # Execute load_vector_store()
    report_vector_store.load_vector_store()
    mem_chunks = report_vector_store._chunk_metadata
    mem_count = len(mem_chunks)
    print(f"  Metadata chunks in memory: {mem_count}")
    
    # Verify disk_count == mem_count == 1152
    reload_ok = (disk_count == mem_count)
    print(f"  Counts match (disk == memory)         : {'PASS' if reload_ok else 'FAIL'}")
    if not reload_ok:
        audit_passed = False
        
    if mem_count != 1152:
        print(f"  WARNING: Chunk count is {mem_count}, expected 1152.")
        
    # Check owner_id presence
    chunks_with_owner = sum(1 for c in mem_chunks if c.get("owner_id"))
    chunks_missing_owner = mem_count - chunks_with_owner
    print(f"  Chunks with owner_id                  : {chunks_with_owner}")
    print(f"  Chunks missing owner_id               : {chunks_missing_owner}")
    
    owner_id_ok = (chunks_missing_owner == 0)
    print(f"  All chunks have owner_id (missing == 0): {'PASS' if owner_id_ok else 'FAIL'}")
    if not owner_id_ok:
        audit_passed = False
        
    # ----------------------------------------------------
    # 2. Backend Restart Audit (Simulated via clean reload)
    # ----------------------------------------------------
    print("\n--- 2. Backend Restart Audit ---")
    # Simulate a clean import by deleting from sys.modules and re-importing
    if "report_vector_store" in sys.modules:
        del sys.modules["report_vector_store"]
        
    import report_vector_store as reloaded_store
    reloaded_mem_chunks = reloaded_store._chunk_metadata
    reloaded_mem_count = len(reloaded_mem_chunks)
    print(f"  Re-loaded chunks in memory after restart: {reloaded_mem_count}")
    
    restart_count_ok = (reloaded_mem_count == mem_count)
    print(f"  Chunk counts unchanged after restart    : {'PASS' if restart_count_ok else 'FAIL'}")
    if not restart_count_ok:
        audit_passed = False
        
    reloaded_chunks_with_owner = sum(1 for c in reloaded_mem_chunks if c.get("owner_id"))
    reloaded_chunks_missing_owner = reloaded_mem_count - reloaded_chunks_with_owner
    print(f"  Re-loaded chunks with owner_id          : {reloaded_chunks_with_owner}")
    print(f"  Re-loaded chunks missing owner_id       : {reloaded_chunks_missing_owner}")
    
    restart_owner_ok = (reloaded_chunks_missing_owner == 0)
    print(f"  All chunks still contain owner_id       : {'PASS' if restart_owner_ok else 'FAIL'}")
    if not restart_owner_ok:
        audit_passed = False
        
    # ----------------------------------------------------
    # 3. Runtime Isolation Audit
    # ----------------------------------------------------
    print("\n--- 3. Runtime Isolation Audit ---")
    doc_a = create_doctor("doctor-a")
    doc_b = create_doctor("doctor-b")
    
    patient_c_id = None
    report_c_id = None
    
    try:
        # Create Patient C under Doctor A
        res_p = client.post(
            "/patients/",
            json={"name": "Audit Patient C", "age": 45, "gender": "Female"},
            headers=doc_a["headers"]
        )
        patient_c_id = res_p.json()["id"]
        
        # Mock OCR extraction
        import routers.reports
        original_ocr = routers.reports.extract_report_text
        routers.reports.extract_report_text = lambda path, mime: (
            "Lab results for Audit Patient C. Hemoglobin is 14.1 g/dL. Glucose level is 92 mg/dL."
        )
        
        # Upload Report C as Doctor A
        pdf_content = b"%PDF-1.4 mock audit pdf"
        files = {"file": ("audit_report.pdf", pdf_content, "application/pdf")}
        res_upload = client.post(
            "/reports/upload",
            data={"patient_id": patient_c_id},
            files=files,
            headers=doc_a["headers"]
        )
        report_c_id = res_upload.json()["id"]
        
        # Run OCR
        client.post(f"/reports/{report_c_id}/ocr", headers=doc_a["headers"])
        
        # Restore OCR extraction
        routers.reports.extract_report_text = original_ocr
        
        # Doctor A queries the content
        print("  Querying as Doctor A...")
        res_search_a = client.post(
            "/ask/",
            json={"question": "What is the Hemoglobin level of Audit Patient C?", "top_k": 5},
            headers=doc_a["headers"]
        )
        
        doc_a_answer = res_search_a.json().get("answer")
        doc_a_chunks = res_search_a.json().get("chunks_used", [])
        
        print(f"    Doctor A answer     : {doc_a_answer}")
        print(f"    Doctor A chunks_used : {doc_a_chunks}")
        
        doc_a_search_ok = len(doc_a_chunks) > 0 and "14.1" in str(doc_a_answer)
        print(f"    Doctor A retrieval succeeds           : {'PASS' if doc_a_search_ok else 'FAIL'}")
        if not doc_a_search_ok:
            audit_passed = False
            
        # Doctor B queries the identical content
        print("  Querying identical content as Doctor B...")
        res_search_b = client.post(
            "/ask/",
            json={"question": "What is the Hemoglobin level of Audit Patient C?", "top_k": 5},
            headers=doc_b["headers"]
        )
        
        doc_b_answer = res_search_b.json().get("answer")
        doc_b_chunks = res_search_b.json().get("chunks_used", [])
        
        print(f"    Doctor B answer     : {doc_b_answer}")
        print(f"    Doctor B chunks_used : {doc_b_chunks}")
        
        doc_b_search_ok = (
            "No relevant medical context found." in str(doc_b_answer) and
            len(doc_b_chunks) == 0
        )
        print(f"    Doctor B retrieval isolated (empty)   : {'PASS' if doc_b_search_ok else 'FAIL'}")
        if not doc_b_search_ok:
            audit_passed = False
            
    finally:
        # Cleanup
        db = SessionLocal()
        try:
            if patient_c_id:
                db.query(Report).filter(Report.patient_id == patient_c_id).delete()
                db.query(Patient).filter(Patient.id == patient_c_id).delete()
                db.commit()
        except Exception as e:
            print(f"  Error during DB cleanup: {e}")
        db.close()
        
        cleanup_doctor(doc_a["email"])
        cleanup_doctor(doc_b["email"])
        
    # ----------------------------------------------------
    # 4. Final Verification
    # ----------------------------------------------------
    print("\n--- 4. Final Classification ---")
    if audit_passed:
        print("FINAL CLASSIFICATION: PASS")
        sys.exit(0)
    else:
        print("FINAL CLASSIFICATION: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    run_signoff_audit()
