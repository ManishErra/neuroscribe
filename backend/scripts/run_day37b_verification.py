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
        # Extract date part only (YYYY-MM-DD) from datetime string
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
from report_vector_store import search_similar_chunks

# Clean and recreate database tables for isolated verification run
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

async def run_verification():
    print("\n======================================================================")
    print("DAY 37B REMEDIATION VERIFICATION SCRIPT")
    print("======================================================================\n")

    transport = httpx.ASGITransport(app=app)
    ac = httpx.AsyncClient(transport=transport, base_url="http://localhost:8000")

    db = SessionLocal()

    # Create distinct clinician accounts for isolation checking
    doc_a_email = f"doca-{uuid.uuid4().hex[:6]}@neuroscribe.org"
    doc_b_email = f"docb-{uuid.uuid4().hex[:6]}@neuroscribe.org"
    password = "SecurePassword123!"

    print("Registering Doctor A and Doctor B...")
    # Doctor A
    res = await ac.post("/auth/register", json={"email": doc_a_email, "password": password, "name": "Doctor A"})
    assert res.status_code == 201, f"Failed to register Doc A: {res.text}"
    doc_a_id = res.json()["id"]

    res_login = await ac.post("/auth/login", json={"email": doc_a_email, "password": password})
    assert res_login.status_code == 200, f"Login Doc A failed: {res_login.text}"
    doc_a_token = res_login.json()["access_token"]
    doc_a_headers = {"Authorization": f"Bearer {doc_a_token}"}

    # Doctor B
    res = await ac.post("/auth/register", json={"email": doc_b_email, "password": password, "name": "Doctor B"})
    assert res.status_code == 201, f"Failed to register Doc B: {res.text}"
    doc_b_id = res.json()["id"]

    res_login = await ac.post("/auth/login", json={"email": doc_b_email, "password": password})
    assert res_login.status_code == 200, f"Login Doc B failed: {res_login.text}"
    doc_b_token = res_login.json()["access_token"]
    doc_b_headers = {"Authorization": f"Bearer {doc_b_token}"}

    print(f"Doc A ID: {doc_a_id} | Doc B ID: {doc_b_id}")

    # Create Patient C under Doctor A
    print("\nCreating Patient C under Doctor A...")
    res_pat = await ac.post(
        "/patients/",
        json={"name": "Patient C", "age": 45, "gender": "Female"},
        headers=doc_a_headers
    )
    assert res_pat.status_code == 200, f"Patient creation failed: {res_pat.text}"
    patient_c_id = res_pat.json()["id"]
    print(f"Patient C ID: {patient_c_id}")

    # Define validation status matrix
    matrix = {
        "A": "FAIL",  # PDF Upload
        "B": "FAIL",  # Image Upload
        "C": "FAIL",  # OCR Execution
        "D": "FAIL",  # OCR Concurrency
        "E": "FAIL",  # Open original document
        "F": "FAIL",  # Direct static URL access
        "G": "FAIL",  # Report deletion
        "H": "FAIL",  # Ownership isolation
        "I": "FAIL",  # Oversized upload rejection
    }

    report_pdf_id = None
    report_pdf_file_path = None
    report_img_id = None

    try:
        # ----------------------------------------------------
        # TEST I: Oversized upload rejection (>50MB)
        # ----------------------------------------------------
        print("\n--- Test I: Oversized upload rejection ---")
        large_content = b"x" * (51 * 1024 * 1024)  # 51 MB
        files = {"file": ("huge_report.pdf", large_content, "application/pdf")}
        start_time = time.time()
        res_large = await ac.post(
            "/reports/upload",
            data={"patient_id": patient_c_id},
            files=files,
            headers=doc_a_headers
        )
        end_time = time.time()
        duration = end_time - start_time
        print(f"Oversized upload request status: {res_large.status_code}")
        print(f"Response text: {res_large.text}")
        print(f"Upload duration: {duration:.2f} seconds")

        if res_large.status_code == 400 and "too large" in res_large.text:
            print("PASS: Oversized upload successfully rejected with 400.")
            matrix["I"] = "PASS"
        else:
            print("FAIL: Oversized upload not rejected or returned incorrect code.")

        # ----------------------------------------------------
        # TEST A: PDF upload
        # ----------------------------------------------------
        print("\n--- Test A: PDF upload ---")
        mock_pdf_content = b"%PDF-1.4 mock pdf data content"
        files = {"file": ("report_c.pdf", mock_pdf_content, "application/pdf")}
        res_pdf = await ac.post(
            "/reports/upload",
            data={"patient_id": patient_c_id},
            files=files,
            headers=doc_a_headers
        )
        print(f"PDF upload status: {res_pdf.status_code}")
        if res_pdf.status_code == 200:
            res_data = res_pdf.json()
            report_pdf_id = res_data["id"]
            report_pdf_file_path = res_data["file_path"]
            print(f"Uploaded Report ID: {report_pdf_id}")
            print(f"File Path: {report_pdf_file_path}")
            assert res_data["ocr_status"] == "pending"
            matrix["A"] = "PASS"
        else:
            print(f"FAIL: PDF upload failed: {res_pdf.text}")

        # ----------------------------------------------------
        # TEST B: Image upload
        # ----------------------------------------------------
        print("\n--- Test B: Image upload ---")
        mock_png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR mock image bytes"
        files = {"file": ("skin_lesion.png", mock_png_content, "image/png")}
        res_img = await ac.post(
            "/reports/upload",
            data={"patient_id": patient_c_id},
            files=files,
            headers=doc_a_headers
        )
        print(f"Image upload status: {res_img.status_code}")
        if res_img.status_code == 200:
            report_img_id = res_img.json()["id"]
            print(f"Uploaded Image Report ID: {report_img_id}")
            matrix["B"] = "PASS"
        else:
            print(f"FAIL: Image upload failed: {res_img.text}")

        # ----------------------------------------------------
        # TEST C & D: OCR Execution & Concurrency
        # ----------------------------------------------------
        print("\n--- Test C & D: OCR Execution & Concurrency ---")
        # Define a slow OCR mock in the reports router
        original_ocr = routers.reports.extract_report_text
        
        def slow_ocr(disk_path, mime_type):
            print("  [OCR Worker Thread] OCR started, sleeping 2.0s...")
            time.sleep(2.0)  # CPU-heavy / blocking work in threadpool
            print("  [OCR Worker Thread] OCR finished.")
            return "OCR RESULT: Patient C has hemoglobin level of 14.5 g/dL and glucose is 88 mg/dL."

        routers.reports.extract_report_text = slow_ocr

        print("Triggering slow OCR task as Doctor A...")
        ocr_task = asyncio.create_task(
            ac.post(f"/reports/{report_pdf_id}/ocr", headers=doc_a_headers)
        )

        # Wait a tiny bit for request thread to start
        await asyncio.sleep(0.2)

        # Fire concurrent requests while OCR is processing in background
        print("Sending concurrent request to check application responsiveness...")
        c_start = time.time()
        res_concurrent = await ac.get(f"/reports/patient/{patient_c_id}", headers=doc_a_headers)
        c_end = time.time()
        concurrent_duration = c_end - c_start

        print(f"Concurrent patient reports query finished in {concurrent_duration:.3f}s with status {res_concurrent.status_code}")
        assert res_concurrent.status_code == 200, "Concurrent request failed!"

        # Wait for OCR task to finish
        print("Waiting for OCR task completion...")
        res_ocr = await ocr_task
        print(f"OCR task finished with status: {res_ocr.status_code}")
        
        # Restore original OCR
        routers.reports.extract_report_text = original_ocr

        if res_ocr.status_code == 200:
            res_ocr_data = res_ocr.json()
            assert res_ocr_data["ocr_status"] == "ready"
            assert "14.5 g/dL" in res_ocr_data["text_preview"]
            print("PASS: OCR executed successfully, status updated to ready.")
            matrix["C"] = "PASS"
        else:
            print(f"FAIL: OCR failed: {res_ocr.text}")

        if concurrent_duration < 1.0:
            print(f"PASS: Concurrency test passed. FastAPI server responded in {concurrent_duration:.3f}s (well under 2.0s OCR sleep).")
            matrix["D"] = "PASS"
        else:
            print(f"FAIL: FastAPI event loop was blocked by the slow OCR task.")

        # ----------------------------------------------------
        # TEST E & F: Open original document / static access
        # ----------------------------------------------------
        print("\n--- Test E & F: Static serving access ---")
        # Access the relative static URL path
        static_url = f"/{report_pdf_file_path}"
        print(f"Attempting to fetch static file from: {static_url}")
        res_static = await ac.get(static_url)
        print(f"Static serving response status: {res_static.status_code}")
        if res_static.status_code == 200 and res_static.content == mock_pdf_content:
            print("PASS: Original PDF document retrieved from static server match.")
            matrix["E"] = "PASS"
            matrix["F"] = "PASS"
        else:
            print(f"FAIL: Static serve returned status {res_static.status_code}")

        # ----------------------------------------------------
        # TEST H: Ownership isolation
        # ----------------------------------------------------
        print("\n--- Test H: Ownership isolation ---")
        ownership_passed = True

        # Doctor B attempts to GET Doctor A's patient reports
        res_iso_list = await ac.get(f"/reports/patient/{patient_c_id}", headers=doc_b_headers)
        print(f"Doc B GET patient reports: {res_iso_list.status_code}")
        if res_iso_list.status_code != 404:
            print(f"  FAIL: Doc B could list/access Doc A's patient reports.")
            ownership_passed = False

        # Doctor B attempts to GET Doctor A's single report
        res_iso_get = await ac.get(f"/reports/{report_pdf_id}", headers=doc_b_headers)
        print(f"Doc B GET report details: {res_iso_get.status_code}")
        if res_iso_get.status_code != 404:
            print(f"  FAIL: Doc B could fetch details of Doc A's report.")
            ownership_passed = False

        # Doctor B attempts to run OCR on Doctor A's report
        res_iso_ocr = await ac.post(f"/reports/{report_pdf_id}/ocr", headers=doc_b_headers)
        print(f"Doc B OCR execution: {res_iso_ocr.status_code}")
        if res_iso_ocr.status_code != 404:
            print(f"  FAIL: Doc B could run OCR on Doc A's report.")
            ownership_passed = False

        # Doctor B attempts to DELETE Doctor A's report
        res_iso_del = await ac.delete(f"/reports/{report_pdf_id}", headers=doc_b_headers)
        print(f"Doc B DELETE report: {res_iso_del.status_code}")
        if res_iso_del.status_code != 404:
            print(f"  FAIL: Doc B could delete Doc A's report.")
            ownership_passed = False

        if ownership_passed:
            print("PASS: Strict patient-level ownership isolation verified successfully.")
            matrix["H"] = "PASS"

        # ----------------------------------------------------
        # TEST G: Report deletion
        # ----------------------------------------------------
        print("\n--- Test G: Report deletion ---")
        disk_path = Path(__file__).resolve().parent.parent / report_pdf_file_path
        print(f"Verifying file exists before deletion: {disk_path.is_file()}")
        assert disk_path.is_file(), "Report file was not saved on disk!"

        res_del = await ac.delete(f"/reports/{report_pdf_id}", headers=doc_a_headers)
        print(f"DELETE request status code: {res_del.status_code}")

        if res_del.status_code == 204:
            # Check SQL database record
            db_report = db.query(Report).filter(Report.id == report_pdf_id).first()
            file_exists = disk_path.is_file()
            print(f"DB Record after deletion: {db_report}")
            print(f"Disk file after deletion: {file_exists}")

            if db_report is None and not file_exists:
                print("PASS: Report record deleted from database and file removed from disk.")
                matrix["G"] = "PASS"
            else:
                print("FAIL: DB row or physical file was not cleaned up.")
        else:
            print(f"FAIL: DELETE endpoint returned incorrect code: {res_del.status_code}")

        # ----------------------------------------------------
        # Vector cleanup audit: check if vector chunks remain in FAISS index
        # ----------------------------------------------------
        print("\n--- Vector store cleanup audit ---")
        # Search for a keyword specific to the deleted report
        search_results = search_similar_chunks(
            query="hemoglobin 14.5",
            top_k=5,
            owner_id=doc_a_id
        )
        print(f"Search results for 'hemoglobin 14.5' under owner {doc_a_id}:")
        found_orphaned = False
        for hit in search_results:
            print(f"  Chunk hit: [Report ID: {hit['report_id']}] score={hit['similarity_score']} text='{hit['chunk_text']}'")
            if str(hit['report_id']) == str(report_pdf_id):
                found_orphaned = True

        if found_orphaned:
            print("AUDIT RESULT: YES, deleted report chunks remain as orphaned FAISS vectors.")
        else:
            print("AUDIT RESULT: NO, deleted report chunks were not found in search results.")

    finally:
        # Clean up database records
        print("\nCleaning up validation records from database...")
        db.query(Report).filter(Report.patient_id == patient_c_id).delete()
        db.query(Patient).filter(Patient.id == patient_c_id).delete()
        db.commit()

        # Clean up generated physical files (e.g. skin_lesion.png or report_c.pdf if they weren't deleted)
        if report_pdf_file_path:
            p = Path(__file__).resolve().parent.parent / report_pdf_file_path
            if p.is_file():
                try:
                    os.remove(p)
                    print(f"Cleaned up dangling report file: {p}")
                except OSError:
                    pass

        # Cleanup users
        db.query(User).filter(User.id.in_([doc_a_id, doc_b_id])).delete()
        db.commit()
        db.close()
        print("Cleanup completed.")

    # Remove verification SQLite database file after test
    try:
        os.remove("verification_test.db")
        print("Removed verification_test.db database file.")
    except OSError:
        pass

    # Print validation summary
    print("\n======================================================================")
    print("VERIFICATION RESULTS SUMMARY")
    print("======================================================================")
    for key, val in matrix.items():
        print(f"  Test {key}: {val}")
    print("======================================================================\n")

    return matrix

if __name__ == "__main__":
    asyncio.run(run_verification())
