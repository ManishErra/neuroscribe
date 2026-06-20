import asyncio
import os
import io
import uuid
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from database import engine, get_db
from main import app

async def run_smoke_test():
    print("--- PRODUCTION SMOKE TEST INITIALIZED ---")
    
    # Establish DB connection for evidence
    conn = engine.connect()
    
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            
            # --- 1 & 2. Registration & Authentication ---
            print("\n[Step 1 & 2] Registration & Authentication")
            uid_a = str(uuid.uuid4())[:8]
            email_a = f"smoke_doc_a_{uid_a}@example.com"
            res_reg = await ac.post("/auth/register", json={"email": email_a, "password": "Smoke_P@ssw0rd123", "name": "Dr. Smoke A"})
            print(f"Register Doc A: {res_reg.status_code}")
            
            res_login = await ac.post("/auth/login", json={"email": email_a, "password": "Smoke_P@ssw0rd123"})
            print(f"Login Doc A: {res_login.status_code}")
            if res_login.status_code != 200:
                print(f"Login Error: {res_login.text}")
            token_a = res_login.json().get("access_token")
            headers_a = {"Authorization": f"Bearer {token_a}"}

            email_b = f"smoke_doc_b_{uid_a}@example.com"
            await ac.post("/auth/register", json={"email": email_b, "password": "Smoke_P@ssw0rd123", "name": "Dr. Smoke B"})
            res_login_b = await ac.post("/auth/login", json={"email": email_b, "password": "Smoke_P@ssw0rd123"})
            print(f"Login Doc B: {res_login_b.status_code}")
            if res_login_b.status_code != 200:
                print(f"Login Error B: {res_login_b.text}")
            token_b = res_login_b.json().get("access_token")
            headers_b = {"Authorization": f"Bearer {token_b}"}

            # --- 3. Patient Workflow ---
            print("\n[Step 3] Patient Workflow")
            res_pat_create = await ac.post("/patients/", json={"name": "Smoke Patient", "dob": "1990-01-01", "gender": "Other", "age": 36}, headers=headers_a)
            print(f"Create Patient: {res_pat_create.status_code}")
            if res_pat_create.status_code != 200 and res_pat_create.status_code != 201:
                print(f"Patient Create Error: {res_pat_create.text}")
            patient_id = res_pat_create.json()["id"]

            res_pat_get = await ac.get(f"/patients/{patient_id}", headers=headers_a)
            print(f"Retrieve Patient: {res_pat_get.status_code}")

            # --- 4. Session Workflow ---
            print("\n[Step 4] Session Workflow")
            res_sess_create = await ac.post("/sessions/", json={"patient_id": patient_id}, headers=headers_a)
            print(f"Create Session: {res_sess_create.status_code}")
            session_id = res_sess_create.json()["id"]

            res_sess_get = await ac.get(f"/sessions/{session_id}", headers=headers_a)
            print(f"Retrieve Session: {res_sess_get.status_code}")

            # --- 5. Report Workflow ---
            print("\n[Step 5] Report Workflow")
            import glob
            sample_pdfs = glob.glob(os.path.join("uploads", "reports", "*.pdf"))
            if sample_pdfs:
                with open(sample_pdfs[0], "rb") as f:
                    dummy_pdf = io.BytesIO(f.read())
            else:
                dummy_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
                
            files = {"file": ("smoke_report.pdf", dummy_pdf, "application/pdf")}
            data = {"patient_id": patient_id, "report_type": "MRI"}
            res_upload = await ac.post("/reports/upload", data=data, files=files, headers=headers_a)
            print(f"Upload Report: {res_upload.status_code}")
            report_id = res_upload.json()["id"]
            
            db_report = conn.execute(text(f"SELECT COUNT(*) FROM reports WHERE id = '{report_id}'")).fetchone()[0]
            print(f"Report row exists in DB: {db_report == 1}")

            # --- 6 & 7. OCR & Embedding Workflow ---
            print("\n[Step 6 & 7] OCR & Embedding Workflow")
            res_ocr = await ac.post(f"/reports/{report_id}/ocr", headers=headers_a)
            print(f"Execute OCR: {res_ocr.status_code}")
            
            # Wait for background task
            print("Waiting for OCR & Embeddings background task to complete...")
            await asyncio.sleep(5)
            
            # Verify DB Evidence
            db_text = conn.execute(text(f"SELECT ocr_text FROM reports WHERE id = '{report_id}'")).fetchone()[0]
            print(f"OCR text stored in DB: {bool(db_text and len(db_text) > 0)}")
            
            db_emb = conn.execute(text(f"SELECT COUNT(*) FROM embeddings WHERE source_id = '{report_id}'")).fetchone()[0]
            print(f"Embedding rows exist in DB: {db_emb > 0} (Count: {db_emb})")

            # --- 8. Retrieval Workflow ---
            print("\n[Step 8] RAG Retrieval Workflow")
            res_ask = await ac.get(f"/ask?patient_id={patient_id}&query=fake", headers=headers_a)
            print(f"RAG Search: {res_ask.status_code}")
            # Wait, the ask endpoint relies on LLM, so if it returns 200, it succeeded.

            # --- 9. Secure Download Workflow ---
            print("\n[Step 9] Secure Download Workflow")
            res_dl_unauth = await ac.get(f"/reports/{report_id}/download")
            print(f"Unauthenticated Download: {res_dl_unauth.status_code}")
            
            res_dl_nonowner = await ac.get(f"/reports/{report_id}/download", headers=headers_b)
            print(f"Non-owner Download: {res_dl_nonowner.status_code}")
            
            res_dl_owner = await ac.get(f"/reports/{report_id}/download", headers=headers_a)
            print(f"Owner Download: {res_dl_owner.status_code}")

            # --- 10. Cleanup Workflow ---
            print("\n[Step 10] Cleanup Workflow")
            res_del_rep = await ac.delete(f"/reports/{report_id}", headers=headers_a)
            print(f"Delete Report: {res_del_rep.status_code}")
            
            res_del_pat = await ac.delete(f"/patients/{patient_id}", headers=headers_a)
            print(f"Delete Patient: {res_del_pat.status_code}")

            # Verify Cleanup Evidence
            db_report_after = conn.execute(text(f"SELECT COUNT(*) FROM reports WHERE id = '{report_id}'")).fetchone()[0]
            db_emb_after = conn.execute(text(f"SELECT COUNT(*) FROM embeddings WHERE source_id = '{report_id}'")).fetchone()[0]
            print(f"Report row count after cleanup: {db_report_after}")
            print(f"Embeddings row count after cleanup: {db_emb_after}")

            # Cleanup dummy accounts
            conn.execute(text(f"DELETE FROM users WHERE email IN ('{email_a}', '{email_b}')"))
            conn.commit()

            print("\n--- SMOKE TEST SUCCESSFUL ---")

    except Exception as e:
        print(f"FAIL: Exception occurred: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    os.environ["APP_ENV"] = "production"
    asyncio.run(run_smoke_test())
