import asyncio
import os
import uuid
import glob
import traceback
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from database import engine
from main import app

async def run_diagnostic():
    print("--- DIAGNOSTIC SCRIPT INITIALIZED ---")
    conn = engine.connect()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            
            # --- Setup Auth ---
            uid = str(uuid.uuid4())[:8]
            email = f"diag_{uid}@example.com"
            await ac.post("/auth/register", json={"email": email, "password": "Smoke_P@ssw0rd123", "name": "Dr. Diag"})
            res_login = await ac.post("/auth/login", json={"email": email, "password": "Smoke_P@ssw0rd123"})
            token = res_login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # --- 1. OCR Pipeline Verification ---
            print("\n[Diagnostic 1] OCR Pipeline")
            pat_res = await ac.post("/patients/", json={"name": "Diag Pat", "dob": "1990-01-01", "gender": "Other", "age": 30}, headers=headers)
            patient_id = pat_res.json()["id"]

            from reportlab.pdfgen import canvas
            pdf_path = "diag_report.pdf"
            c = canvas.Canvas(pdf_path)
            c.drawString(100, 750, "Patient Diagnosis: Mild headaches.")
            c.drawString(100, 730, "Recommendation: Rest and hydration.")
            c.save()
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            print(f"Generated PDF Used: {pdf_path}")
            print(f"PDF Size: {len(pdf_bytes)} bytes")
            
            files = {"file": ("diag_report.pdf", pdf_bytes, "application/pdf")}
            data = {"patient_id": patient_id, "report_type": "MRI"}
            res_up = await ac.post("/reports/upload", data=data, files=files, headers=headers)
            report_id = res_up.json()["id"]
            
            await ac.post(f"/reports/{report_id}/ocr", headers=headers)
            print("Waiting for OCR background task...")
            await asyncio.sleep(6)
            
            row = conn.execute(text(f"SELECT ocr_status, ocr_error, LENGTH(ocr_text) FROM reports WHERE id = '{report_id}'")).fetchone()
            status, error, length = row
            print(f"Report ID: {report_id}")
            print(f"ocr_status: {status}")
            print(f"ocr_error: {error}")
            print(f"ocr_text length: {length}")
            
            db_emb = conn.execute(text(f"SELECT COUNT(*) FROM embeddings WHERE source_id = '{report_id}'")).fetchone()[0]
            print(f"Embedding count: {db_emb}")

            # --- 2. RAG Route Verification ---
            print("\n[Diagnostic 2] RAG Route Verification")
            res_ask = await ac.get(f"/ask?patient_id={patient_id}&query=test", headers=headers)
            print(f"Initial GET /ask status: {res_ask.status_code}")
            if res_ask.status_code == 307:
                print(f"Redirect Location: {res_ask.headers.get('location')}")
                
            async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac_follow:
                res_ask_follow = await ac_follow.get(f"/ask?patient_id={patient_id}&query=test", headers=headers)
                print(f"Followed GET /ask status: {res_ask_follow.status_code}")
                
            res_ask_slash = await ac.get(f"/ask/?patient_id={patient_id}&query=test", headers=headers)
            print(f"GET /ask/ status: {res_ask_slash.status_code}")

            # --- 3. Patient Delete Verification ---
            print("\n[Diagnostic 3] Patient Delete Verification")
            await ac.post("/sessions/", json={"patient_id": patient_id}, headers=headers)
            
            res_del = await ac.delete(f"/patients/{patient_id}", headers=headers)
            print(f"Delete HTTP Status: {res_del.status_code}")
            print(f"Delete Response Body: {res_del.text}")

            print("Direct DB Delete Attempt:")
            try:
                conn.execute(text(f"DELETE FROM patients WHERE id = '{patient_id}'"))
                conn.commit()
            except Exception as sql_e:
                conn.rollback()
                print(f"SQL Exception:\n{traceback.format_exc()}")

    except Exception as e:
        print(f"Global Error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    os.environ["APP_ENV"] = "production"
    asyncio.run(run_diagnostic())
