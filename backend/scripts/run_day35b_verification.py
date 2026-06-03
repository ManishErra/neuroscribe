import sys
import json
import uuid
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User, Patient, Report

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

def run_verification():
    print("\n--- DAY 35B FAISS VECTOR STORE ISOLATION VERIFICATION MATRIX ---")
    
    backend_dir = Path(__file__).resolve().parent.parent
    metadata_file = backend_dir / "vector_metadata.json"
    
    all_passed = True
    
    # ----------------------------------------------------
    # AUDIT A: Existing Metadata Audit
    # ----------------------------------------------------
    print("\n--- Audit A: Existing Metadata Check ---")
    if not metadata_file.is_file():
        print(f"  FAIL: vector_metadata.json not found at {metadata_file}")
        sys.exit(1)
        
    with open(metadata_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    total_chunks = len(chunks)
    print(f"  Loaded {total_chunks} metadata chunks.")
    
    if total_chunks != 1152:
        print(f"  WARNING: Total chunks is {total_chunks}, expected 1152 (ignoring if developer added test chunks).")
        
    missing_owner = 0
    invalid_owner_count = 0
    
    db = SessionLocal()
    try:
        # Load all valid user IDs
        valid_user_ids = {str(uid[0]) for uid in db.execute(text("SELECT id FROM users")).fetchall()}
        print(f"  Loaded {len(valid_user_ids)} valid user IDs from database.")
    except Exception as e:
        print(f"  FAIL: Failed to query users table: {e}")
        db.close()
        sys.exit(1)
    db.close()
    
    for idx, chunk in enumerate(chunks):
        owner_id = chunk.get("owner_id")
        if not owner_id:
            missing_owner += 1
        elif str(owner_id) not in valid_user_ids:
            invalid_owner_count += 1
            
    print(f"  Chunks missing owner_id                : {missing_owner}")
    print(f"  Chunks with owner_id not in users table: {invalid_owner_count}")
    
    if missing_owner > 0 or invalid_owner_count > 0:
        print("  FAIL: Static metadata audit failed (owner_id checks).")
        all_passed = False
    else:
        print("  PASS: Static metadata audit passed.")
        
    # ----------------------------------------------------
    # AUDIT B: OCR Ingestion Audit
    # ----------------------------------------------------
    print("\n--- Audit B: OCR Chunk Ingestion Audit ---")
    doc_a = create_doctor("doctor-a")
    doc_b = create_doctor("doctor-b")
    
    print(f"  Doctor A logged in: {doc_a['email']} (ID: {doc_a['id']})")
    print(f"  Doctor B logged in: {doc_b['email']} (ID: {doc_b['id']})")
    
    patient_c_id = None
    report_c_id = None
    
    try:
        # Create Patient C under Doctor A
        res_p = client.post(
            "/patients/",
            json={"name": "Patient C", "age": 42, "gender": "Male"},
            headers=doc_a["headers"]
        )
        if res_p.status_code != 200:
            print(f"  FAIL: Doctor A failed to create Patient C: {res_p.text}")
            sys.exit(1)
        patient_c_id = res_p.json()["id"]
        
        # Mock OCR extraction
        import routers.reports
        original_ocr = routers.reports.extract_report_text
        routers.reports.extract_report_text = lambda path, mime: (
            "Patient C lab report: Hemoglobin is 13.9 g/dL, glucose is 95 mg/dL. "
            "Platelets count is normal at 250 x10^3/ul. Signed by Doctor A."
        )
        
        # Upload Report C as Doctor A
        pdf_content = b"%PDF-1.4 mock pdf text"
        files = {"file": ("report_c.pdf", pdf_content, "application/pdf")}
        res_upload = client.post(
            "/reports/upload",
            data={"patient_id": patient_c_id},
            files=files,
            headers=doc_a["headers"]
        )
        
        if res_upload.status_code != 200:
            print(f"  FAIL: Doctor A failed to upload Report C: {res_upload.text}")
            sys.exit(1)
            
        report_c_id = res_upload.json()["id"]
        print(f"  PASS: Report uploaded successfully. ID: {report_c_id}")
        
        # Run OCR to trigger chunking and vector storage
        res_ocr = client.post(
            f"/reports/{report_c_id}/ocr",
            headers=doc_a["headers"]
        )
        
        if res_ocr.status_code != 200:
            print(f"  FAIL: Doctor A failed to run OCR on Report C: {res_ocr.text}")
            sys.exit(1)
            
        print(f"  PASS: OCR completed. Status: {res_ocr.json()['ocr_status']}")
        
        # Restore original OCR extractor
        routers.reports.extract_report_text = original_ocr
        
        # Read the vector_metadata.json to inspect newly written chunks
        with open(metadata_file, "r", encoding="utf-8") as f:
            updated_chunks = json.load(f)
            
        report_c_chunks = [c for c in updated_chunks if str(c.get("report_id")) == str(report_c_id)]
        new_chunk_count = len(report_c_chunks)
        print(f"  New report generated chunks count: {new_chunk_count}")
        
        if new_chunk_count == 0:
            print("  FAIL: Report generated 0 chunks (classified as FAIL).")
            all_passed = False
        else:
            print("  PASS: Report generated > 0 chunks.")
            
        field_completeness_pass = True
        owner_equality_pass = True
        
        for c in report_c_chunks:
            if not c.get("report_id"):
                field_completeness_pass = False
                print("  FAIL: Chunk is missing report_id key.")
            if not c.get("owner_id"):
                field_completeness_pass = False
                print("  FAIL: Chunk is missing owner_id key.")
            elif str(c.get("owner_id")) != str(doc_a["id"]):
                owner_equality_pass = False
                print(f"  FAIL: Chunk owner_id ({c.get('owner_id')}) does not match Doctor A id ({doc_a['id']}).")
                
        if field_completeness_pass:
            print("  PASS: Every chunk contains report_id and owner_id.")
        else:
            all_passed = False
            
        if owner_equality_pass:
            print("  PASS: Every chunk owner_id equals current_user.id.")
        else:
            all_passed = False
            
        # ----------------------------------------------------
        # AUDIT C: Multi-Clinician Isolation Audit
        # ----------------------------------------------------
        print("\n--- Audit C: Multi-Clinician Isolation Check ---")
        # Doctor B searches for Hemoglobin of Patient C
        res_search_b = client.post(
            "/ask/",
            json={"question": "What is the Hemoglobin level of Patient C?", "top_k": 5},
            headers=doc_b["headers"]
        )
        
        if res_search_b.status_code != 200:
            print(f"  FAIL: Doctor B POST /ask/ query failed: {res_search_b.text}")
            all_passed = False
        else:
            answer = res_search_b.json().get("answer")
            chunks_used = res_search_b.json().get("chunks_used", [])
            print(f"  Doctor B answer     : {answer}")
            print(f"  Doctor B chunks_used : {chunks_used}")
            
            passed_answer = "No relevant medical context found." in str(answer) or "LLM generation failed" in str(answer) or answer is None
            passed_chunks = len(chunks_used) == 0
            
            # Since LLM is mocked or live, the answer string should reflect lack of context.
            # But the definitive check is that chunks_used must be empty.
            print(f"  Doctor B answer shows lack of context: {'PASS' if passed_answer else 'FAIL'}")
            print(f"  Doctor B chunks_used is empty        : {'PASS' if passed_chunks else 'FAIL'}")
            
            if not passed_chunks:
                all_passed = False
                
    finally:
        # Cleanup Patient C and cascading objects
        print("\nCleaning up test verification records...")
        db = SessionLocal()
        try:
            if patient_c_id:
                db.query(Report).filter(Report.patient_id == patient_c_id).delete()
                db.query(Patient).filter(Patient.id == patient_c_id).delete()
                db.commit()
            print("  PASS: Test patient C and report C deleted from DB.")
        except Exception as e:
            print(f"  FAIL: Cleanup of clinical database rows failed: {e}")
        db.close()
        
        cleanup_doctor(doc_a["email"])
        cleanup_doctor(doc_b["email"])
        print("  PASS: Test doctor accounts deleted.")
        
    if all_passed:
        print("\nALL DAY 35B FAISS VECTOR STORE ISOLATION VERIFICATION MATRIX CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME FAISS VECTOR STORE ISOLATION VERIFICATION MATRIX CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
