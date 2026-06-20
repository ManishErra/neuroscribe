import sys
import json
import uuid
import time
import os
import asyncio
import datetime
from pathlib import Path
from sqlalchemy import text

# Configure database for local SQLite verification
os.environ["DATABASE_URL"] = "sqlite:///./verification_test.db"

# Register CITEXT compiler fallback for SQLite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import CITEXT

@compiles(CITEXT, "sqlite")
def compile_citext_sqlite(element, compiler, **kw):
    return "TEXT"

# Monkeypatch SQLite's DATE result processor to support timestamp strings
from sqlalchemy.dialects.sqlite import DATE

def patched_sqlite_date_result_processor(self, dialect, coltype):
    def process(value):
        if value is None:
            return None
        if isinstance(value, datetime.date):
            return value
        date_str = str(value).split(" ")[0]
        try:
            return datetime.date.fromisoformat(date_str)
        except ValueError:
            return datetime.date.today()
    return process

DATE.result_processor = patched_sqlite_date_result_processor

# Monkeypatch SQLAlchemy's UUID bind parameter processor under SQLite
from sqlalchemy.sql.sqltypes import UUID
original_uuid_bind_processor = UUID.bind_processor

def patched_uuid_bind_processor(self, dialect):
    proc = original_uuid_bind_processor(self, dialect)
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    value = uuid.UUID(value)
                except ValueError:
                    pass
            if proc:
                return proc(value)
            return value
        return process
    return proc

UUID.bind_processor = patched_uuid_bind_processor

sys.path.append(str(Path(__file__).resolve().parent.parent))

import httpx
from main import app
from database import engine, Base, SessionLocal
from models import User, Patient, Report
import routers.reports
import report_vector_store
from report_vector_store import search_similar_chunks, load_vector_store

# Initialize clean database schema for isolated verification
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

async def run_verification():
    print("======================================================================")
    print("PHASE 0 RAG ISOLATION VERIFICATION RUNNER")
    print("======================================================================\n")

    transport = httpx.ASGITransport(app=app)
    ac = httpx.AsyncClient(transport=transport, base_url="http://localhost:8000")

    db = SessionLocal()
    
    # Define validation status matrix
    matrix = {
        "1. Active Chunks Validation": "FAIL",
        "2. Orphaned Chunks Excluded": "FAIL",
        "3. Patient-level Isolation": "FAIL",
        "4. Cross-user Clinician Isolation": "FAIL",
        "5. Existing Retrieval Functionality": "FAIL",
        "6. Ingestion Metadata Tagging": "FAIL"
    }

    metadata_path = Path(__file__).resolve().parent.parent / "vector_metadata.json"
    
    # ----------------------------------------------------
    # VERIFICATION 1 & 2: Static Metadata Verification
    # ----------------------------------------------------
    print("--- 1. Verification of Static Metadata ---")
    if not metadata_path.is_file():
        print(f"  FAIL: Metadata file {metadata_path} not found.")
        sys.exit(1)
        
    with open(metadata_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    print(f"Loaded {len(chunks)} chunks from {metadata_path.name}.")
    
    active_valid = True
    orphaned_found = False
    orphaned_valid = True
    orphaned_report_id = "633dc096-2180-49c6-9e43-482f75c38c9a"
    
    active_count = 0
    
    for idx, c in enumerate(chunks):
        r_id = c.get("report_id") or c.get("report_source")
        patient_id = c.get("patient_id")
        owner_id = c.get("owner_id")
        status = c.get("migration_status")
        
        if status == "orphaned":
            orphaned_found = True
            if r_id != orphaned_report_id or patient_id != "orphaned" or owner_id != "orphaned":
                orphaned_valid = False
                print(f"  FAIL: Orphaned chunk index {idx} has invalid attributes: r_id={r_id}, pat_id={patient_id}, owner_id={owner_id}")
        else:
            active_count += 1
            if not r_id or not patient_id or not owner_id or patient_id == "orphaned" or owner_id == "orphaned":
                active_valid = False
                print(f"  FAIL: Active chunk index {idx} has invalid attributes: r_id={r_id}, pat_id={patient_id}, owner_id={owner_id}")

    print(f"  Processed {active_count} active chunks and {1 if orphaned_found else 0} orphaned chunks.")
    
    if active_count == 1152 and active_valid:
        print("  PASS: All 1152 active chunks have valid report_id, patient_id, and owner_id.")
        matrix["1. Active Chunks Validation"] = "PASS"
    else:
        print(f"  FAIL: Active chunks validation failed. Active count={active_count}, Valid={active_valid}")
        
    if orphaned_found and orphaned_valid:
        print("  PASS: Orphaned chunk correctly identified, tagged, and preserved.")
        matrix["2. Orphaned Chunks Excluded"] = "PASS"
    else:
        print(f"  FAIL: Orphaned chunk validation failed. Found={orphaned_found}, Valid={orphaned_valid}")

    # Re-trigger vector store load to verify it handles the newly migrated metadata successfully
    print("\n--- Reloading Vector Store in Memory ---")
    load_vector_store()
    print(f"Loaded store. total chunks in index metadata: {len(report_vector_store._chunk_metadata)}")
    
    # ----------------------------------------------------
    # REGISTER TEST DOCTORS AND PATIENTS
    # ----------------------------------------------------
    print("\n--- Registering Test Accounts ---")
    doc_a_email = f"doca-{uuid.uuid4().hex[:6]}@neuroscribe.org"
    doc_b_email = f"docb-{uuid.uuid4().hex[:6]}@neuroscribe.org"
    password = "SecurePassword123!"

    patient_a_id = None
    patient_b_id = None
    patient_a2_id = None
    doc_a_id = None
    doc_b_id = None
    report_a_id = None

    try:
        # Doctor A
        res = await ac.post("/auth/register", json={"email": doc_a_email, "password": password, "name": "Doctor A"})
        assert res.status_code == 201
        doc_a_id = res.json()["id"]
        res_login = await ac.post("/auth/login", json={"email": doc_a_email, "password": password})
        doc_a_token = res_login.json()["access_token"]
        doc_a_headers = {"Authorization": f"Bearer {doc_a_token}"}

        # Doctor B
        res = await ac.post("/auth/register", json={"email": doc_b_email, "password": password, "name": "Doctor B"})
        assert res.status_code == 201
        doc_b_id = res.json()["id"]
        res_login = await ac.post("/auth/login", json={"email": doc_b_email, "password": password})
        doc_b_token = res_login.json()["access_token"]
        doc_b_headers = {"Authorization": f"Bearer {doc_b_token}"}

        # Create Patient A under Doctor A, and Patient B under Doctor B
        res_pat_a = await ac.post("/patients/", json={"name": "Patient A", "age": 30, "gender": "Male"}, headers=doc_a_headers)
        patient_a_id = res_pat_a.json()["id"]

        res_pat_b = await ac.post("/patients/", json={"name": "Patient B", "age": 35, "gender": "Female"}, headers=doc_b_headers)
        patient_b_id = res_pat_b.json()["id"]

        print(f"Doctor A ID: {doc_a_id} | Patient A ID: {patient_a_id}")
        print(f"Doctor B ID: {doc_b_id} | Patient B ID: {patient_b_id}")

        # Create a second patient under Doctor A (Patient A2) to verify patient isolation
        res_pat_a2 = await ac.post("/patients/", json={"name": "Patient A2", "age": 40, "gender": "Male"}, headers=doc_a_headers)
        patient_a2_id = res_pat_a2.json()["id"]
        print(f"Patient A2 ID (also owned by Doc A): {patient_a2_id}")

        # ----------------------------------------------------
        # TEST: OCR Ingestion & Chunk Metadata Tagging
        # ----------------------------------------------------
        print("\n--- 3. Testing OCR Ingestion Tagging ---")
        mock_ocr_result = "Clinical report text: Hemoglobin is 14.2 g/dL. Blood Glucose is 98 mg/dL. WBC count is 6500 cells/ul."
        
        # Mock OCR extraction
        original_ocr = routers.reports.extract_report_text
        routers.reports.extract_report_text = lambda path, mime: mock_ocr_result

        # Upload and run OCR for Patient A
        files = {"file": ("report_a.pdf", b"%PDF-1.4 mock pdf data", "application/pdf")}
        res_upload = await ac.post("/reports/upload", data={"patient_id": patient_a_id}, files=files, headers=doc_a_headers)
        assert res_upload.status_code == 200
        report_a_id = res_upload.json()["id"]
        
        res_ocr = await ac.post(f"/reports/{report_a_id}/ocr", headers=doc_a_headers)
        assert res_ocr.status_code == 200
        
        # Restore original OCR
        routers.reports.extract_report_text = original_ocr
        
        # Reload store and verify newly added chunk metadata
        load_vector_store()
        new_chunks = [c for c in report_vector_store._chunk_metadata if str(c.get("report_id")) == str(report_a_id)]
        print(f"Ingested {len(new_chunks)} chunks for Report A.")
        
        new_chunks_valid = len(new_chunks) > 0
        for c in new_chunks:
            if str(c.get("patient_id")) != str(patient_a_id) or str(c.get("owner_id")) != str(doc_a_id):
                new_chunks_valid = False
                print(f"  FAIL: Ingested chunk has incorrect tags: patient={c.get('patient_id')}, owner={c.get('owner_id')}")

        if new_chunks_valid:
            print("  PASS: Newly ingested chunks correctly tagged with both patient_id and owner_id.")
            matrix["6. Ingestion Metadata Tagging"] = "PASS"
        else:
            print("  FAIL: Newly ingested chunks tagging failed.")

        # ----------------------------------------------------
        # TEST: Patient-level Isolation
        # ----------------------------------------------------
        print("\n--- 4. Testing Patient-level Isolation ---")
        # Query Doctor A asking about Patient A's hemoglobin
        res_ask_a = await ac.post(
            "/ask/",
            json={"patient_id": patient_a_id, "question": "What is the hemoglobin level?", "top_k": 5},
            headers=doc_a_headers
        )
        print(f"Doctor A query Patient A hemoglobin status: {res_ask_a.status_code}")
        print(f"Doctor A query Patient A hemoglobin chunks count: {len(res_ask_a.json().get('chunks_used', []))}")
        
        # Query Doctor A asking about Patient A2 (who has NO reports uploaded)
        res_ask_a2 = await ac.post(
            "/ask/",
            json={"patient_id": patient_a2_id, "question": "What is the hemoglobin level?", "top_k": 5},
            headers=doc_a_headers
        )
        print(f"Doctor A query Patient A2 status: {res_ask_a2.status_code}")
        chunks_a2 = res_ask_a2.json().get("chunks_used", [])
        print(f"Doctor A query Patient A2 chunks count: {len(chunks_a2)}")
        
        # Patient-level isolation is verified if query for Patient A2 returns 0 chunks, 
        # despite both patients being owned by Doctor A.
        if res_ask_a.status_code == 200 and len(res_ask_a.json().get("chunks_used", [])) > 0 and len(chunks_a2) == 0:
            print("  PASS: Patient-level isolation validated. Chunks are strictly partitioned by patient_id.")
            matrix["3. Patient-level Isolation"] = "PASS"
        else:
            print("  FAIL: Patient-level isolation failed.")

        # ----------------------------------------------------
        # TEST: Cross-user Clinician Isolation
        # ----------------------------------------------------
        print("\n--- 5. Testing Cross-user Clinician Isolation ---")
        
        # Doctor B attempts to query Patient A's data passing Patient A's ID
        res_ask_b_leak = await ac.post(
            "/ask/",
            json={"patient_id": patient_a_id, "question": "What is the hemoglobin level?", "top_k": 5},
            headers=doc_b_headers
        )
        print(f"Doctor B querying Patient A's ID status: {res_ask_b_leak.status_code} (Expected: 404)")
        print(f"Doctor B querying Patient A's ID response: {res_ask_b_leak.text}")
        
        if res_ask_b_leak.status_code == 404 and "access denied" in res_ask_b_leak.text:
            print("  PASS: Cross-user clinician isolation validated. Clinicians cannot access other clinicians' patient IDs.")
            matrix["4. Cross-user Clinician Isolation"] = "PASS"
        else:
            print("  FAIL: Cross-user clinician isolation failed.")

        # ----------------------------------------------------
        # TEST: Orphaned Chunk Exclusion
        # ----------------------------------------------------
        print("\n--- 6. Testing Orphaned Chunk Exclusion ---")
        # Run a raw search query using search_similar_chunks for query "Patient C" (which is in the orphaned chunk)
        # under Doctor A's context, and verify that the orphaned chunk is never returned
        results = search_similar_chunks(
            query="hemoglobin level of Patient C",
            top_k=10,
            owner_id=doc_a_id,
            patient_id=patient_a_id
        )
        print(f"Query returned {len(results)} chunks.")
        orphaned_leaked = False
        for r in results:
            if str(r.get("report_id")) == orphaned_report_id or r.get("migration_status") == "orphaned":
                orphaned_leaked = True
                print(f"  FAIL: Orphaned chunk leaked in search: {r}")

        if not orphaned_leaked:
            # Double check the verification matrix check
            # Confirm that the orphaned chunk cannot be searched under any user
            all_results = search_similar_chunks(
                query="Patient C has hemoglobin level of 14.5",
                top_k=100
            )
            global_leaked = False
            for r in all_results:
                if str(r.get("report_id")) == orphaned_report_id or r.get("migration_status") == "orphaned":
                    global_leaked = True
                    
            if not global_leaked:
                print("  PASS: Orphaned chunks are successfully excluded from all retrievals.")
                matrix["2. Orphaned Chunks Excluded"] = "PASS"
            else:
                print("  FAIL: Orphaned chunks leaked in global search.")
                matrix["2. Orphaned Chunks Excluded"] = "FAIL"
        else:
            print("  FAIL: Orphaned chunks leaked in scoped search.")
            matrix["2. Orphaned Chunks Excluded"] = "FAIL"

        # ----------------------------------------------------
        # TEST: Existing Retrieval Functionality
        # ----------------------------------------------------
        print("\n--- 7. Testing Existing Retrieval Functionality ---")
        # Verify that we can retrieve Patient A's hemoglobin query properly
        res_ask_final = await ac.post(
            "/ask/",
            json={"patient_id": patient_a_id, "question": "What is the hemoglobin level?", "top_k": 5},
            headers=doc_a_headers
        )
        answer = res_ask_final.json().get("answer")
        chunks_used = res_ask_final.json().get("chunks_used", [])
        print(f"Patient A hemoglobin answer: {answer}")
        print(f"Patient A hemoglobin chunks used: {len(chunks_used)}")
        
        if res_ask_final.status_code == 200 and len(chunks_used) > 0:
            print("  PASS: Existing retrieval functionality remains intact.")
            matrix["5. Existing Retrieval Functionality"] = "PASS"
        else:
            print("  FAIL: Existing retrieval functionality is broken.")

    finally:
        # Clean up database records
        print("\nCleaning up test records...")
        if report_a_id:
            try:
                from report_vector_store import remove_vectors_for_report
                removed = remove_vectors_for_report(str(report_a_id))
                print(f"Cleaned up test vectors for report {report_a_id}: deleted {removed} vectors")
            except Exception as e:
                print(f"Failed to clean up test vectors: {e}")

        if doc_a_id or doc_b_id:
            db.query(Report).filter(Report.patient_id.in_([patient_a_id, patient_b_id, patient_a2_id])).delete()
            db.query(Patient).filter(Patient.id.in_([patient_a_id, patient_b_id, patient_a2_id])).delete()
            db.query(User).filter(User.id.in_([doc_a_id, doc_b_id])).delete()
            db.commit()
            print("  PASS: Database verification records removed.")
        db.close()
        
        try:
            os.remove("verification_test.db")
            print("Cleaned up verification_test.db file.")
        except OSError:
            pass

    # Print summary
    print("\n======================================================================")
    print("VERIFICATION RESULTS SUMMARY")
    print("======================================================================")
    all_passed = True
    for key, val in matrix.items():
        print(f"  {key}: {val}")
        if val != "PASS":
            all_passed = False
    print("======================================================================\n")
    
    if all_passed:
        print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SOME VERIFICATION CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_verification())
