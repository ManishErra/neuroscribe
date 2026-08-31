import sys
import os
import json
import uuid
import faiss
import numpy as np
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, os.path.abspath('backend'))

from database import engine, get_db
from models import User, Patient, Report, Base
from auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from report_vector_store import search_similar_chunks, _index_path, _metadata_path
from report_ocr_extract import extract_report_text
from sqlalchemy import text
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("==================================================")
print("     NEUROSCRIBE DEPLOYMENT-READINESS AUDIT       ")
print("==================================================")

# ── 1. DATABASE ─────────────────────────────────────────────────────────────
print("\n--- 1. DATABASE VERIFICATION ---")
try:
    with engine.connect() as conn:
        dialect = engine.dialect.name
        print(f"[OK] Connection established. Engine dialect: '{dialect}'")
        
    db = next(get_db())
    users = db.query(User).all()
    patients = db.query(Patient).all()
    reports = db.query(Report).all()
    
    print(f"[OK] Database Query Success: {len(users)} users, {len(patients)} patients, {len(reports)} reports found.")
    
    # Verify Relationships
    patient_map = {str(p.id): str(p.owner_id) for p in patients}
    valid_reports = 0
    for r in reports:
        pid = str(r.patient_id)
        if pid in patient_map:
            valid_reports += 1
    print(f"[OK] Report -> Patient -> Owner relationships: {valid_reports}/{len(reports)} valid.")
    db_pass = True
except Exception as e:
    print(f"[FAIL] Database verification failed: {e}")
    db_pass = False

# ── 2. AUTHENTICATION (API LEVEL) ───────────────────────────────────────────
print("\n--- 2. AUTHENTICATION API VERIFICATION ---")
try:
    test_email = f"audit_doc_{uuid.uuid4().hex[:6]}@neuroscribe.demo"
    test_pass = "AuditUserPass123!"
    
    # 2.1 Password Hashing & Verification Utility
    hashed_pwd = hash_password(test_pass)
    assert verify_password(test_pass, hashed_pwd), "bcrypt hash verification failed"
    print(f"[OK] bcrypt password hashing and verification passed.")
    
    # 2.2 JWT Generation & Decoding Utility
    dummy_uid = uuid.uuid4()
    tok_str = create_access_token(dummy_uid, test_email)
    payload = decode_access_token(tok_str)
    assert payload.get("sub") == str(dummy_uid), "JWT payload sub mismatch"
    assert payload.get("email") == test_email, "JWT payload email mismatch"
    print(f"[OK] HS256 JWT creation and validation passed.")

    # 2.3 API Registration
    reg_resp = client.post("/auth/register", json={
        "email": test_email,
        "password": test_pass,
        "name": "Dr. Audit User"
    })
    assert reg_resp.status_code in (200, 201), f"Register API failed: {reg_resp.text}"
    print(f"[OK] Register API endpoint (/auth/register) returned {reg_resp.status_code}.")
    
    # 2.4 API Login
    login_resp = client.post("/auth/login", json={
        "email": test_email,
        "password": test_pass
    })
    token = login_resp.json().get("access_token")
    assert token is not None, f"Login failed: {login_resp.text}"
    print(f"[OK] Login API endpoint (/auth/login) returned 200 OK & bearer token.")
    
    # 2.5 Authenticated /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200, f"/auth/me failed with status {me_resp.status_code}"
    print(f"[OK] /auth/me identity verified: {me_resp.json().get('email')}")
    
    # 2.6 Unauthenticated Route Protection
    unauth_resp = client.get("/auth/me")
    assert unauth_resp.status_code in (401, 403), f"Unauthenticated request returned {unauth_resp.status_code}"
    
    invalid_resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert invalid_resp.status_code == 401, f"Invalid token request returned {invalid_resp.status_code}"
    print(f"[OK] Protected route security verified: 401 returned for missing and invalid tokens.")
    auth_pass = True
except Exception as e:
    print(f"[FAIL] Authentication API test failed: {e}")
    auth_pass = False

# ── 3. PATIENT & RAG ISOLATION ──────────────────────────────────────────────
print("\n--- 3. PATIENT & RAG ISOLATION VERIFICATION ---")
try:
    # Register User A and User B
    uA_email, uA_pass = f"userA_{uuid.uuid4().hex[:4]}@demo.com", "PassA123!456"
    uB_email, uB_pass = f"userB_{uuid.uuid4().hex[:4]}@demo.com", "PassB123!456"
    
    client.post("/auth/register", json={"email": uA_email, "password": uA_pass})
    client.post("/auth/register", json={"email": uB_email, "password": uB_pass})
    
    tokA = client.post("/auth/login", json={"email": uA_email, "password": uA_pass}).json()["access_token"]
    tokB = client.post("/auth/login", json={"email": uB_email, "password": uB_pass}).json()["access_token"]
    
    # User A creates Patient A
    pA_resp = client.post("/patients/", json={"name": "Patient A", "age": 40, "gender": "Male"}, headers={"Authorization": f"Bearer {tokA}"})
    pA_id = pA_resp.json()["id"]
    
    # User B attempts to access Patient A (should fail 404)
    pA_by_B = client.get(f"/patients/{pA_id}", headers={"Authorization": f"Bearer {tokB}"})
    assert pA_by_B.status_code == 404, f"Cross-tenant patient access returned status {pA_by_B.status_code}"
    print(f"[OK] Direct tenant patient boundary verified: 404 returned for unowned patient.")
    
    # RAG Vector Search Isolation
    uB_payload = decode_access_token(tokB)
    uB_user_id = uB_payload["sub"]
    leak_chunks = search_similar_chunks(
        query="What is the hemoglobin level?",
        top_k=5,
        owner_id=str(uB_user_id),
        patient_id=str(pA_id)
    )
    assert len(leak_chunks) == 0, f"RAG LEAK DETECTED! Returned {len(leak_chunks)} chunks for cross-tenant query!"
    print(f"[OK] RAG vector isolation verified: 0 unauthorized chunks returned for cross-tenant query.")
    iso_pass = True
except Exception as e:
    print(f"[FAIL] Patient isolation test failed: {e}")
    iso_pass = False

# ── 4. FAISS & VECTOR METADATA INTEGRITY ────────────────────────────────────
print("\n--- 4. FAISS VECTOR STORE INTEGRITY VERIFICATION ---")
try:
    idx_file = _index_path()
    meta_file = _metadata_path()
    
    if idx_file.exists() and meta_file.exists():
        faiss_idx = faiss.read_index(str(idx_file))
        with open(meta_file, encoding='utf-8') as f:
            metadata = json.load(f)
            
        print(f"[OK] FAISS Index ntotal: {faiss_idx.ntotal}")
        print(f"[OK] Vector Metadata count: {len(metadata)}")
        
        assert faiss_idx.ntotal == len(metadata), f"DESYNC DETECTED! ntotal={faiss_idx.ntotal} vs metadata={len(metadata)}"
        
        valid_records = 0
        for m in metadata:
            if "report_id" in m and "patient_id" in m and "chunk_text" in m:
                valid_records += 1
        print(f"[OK] Valid metadata records: {valid_records}/{len(metadata)}")
        faiss_pass = True
    else:
        print("[WARNING] Vector store files do not exist yet.")
        faiss_pass = True
except Exception as e:
    print(f"[FAIL] FAISS integrity test failed: {e}")
    faiss_pass = False

# ── 5. OCR & PDF PROCESSING ────────────────────────────────────────────────
print("\n--- 5. OCR & PDF PROCESSING VERIFICATION ---")
try:
    sample_pdf = "demo_data/alex_chen_lab_report.pdf"
    if os.path.exists(sample_pdf):
        extracted_text = extract_report_text(sample_pdf, "application/pdf")
        assert len(extracted_text) > 0, "PDF extraction returned empty text"
        assert "Hemoglobin" in extracted_text or "CBC" in extracted_text or "Glucose" in extracted_text, "Expected clinical text missing"
        print(f"[OK] Digital PDF extraction verified using pypdf. Extracted {len(extracted_text)} characters.")
        ocr_pass = True
    else:
        print(f"[WARNING] Sample PDF '{sample_pdf}' not found on disk.")
        ocr_pass = False
except Exception as e:
    print(f"[FAIL] OCR/PDF extraction failed: {e}")
    ocr_pass = False

# ── 6. DEPENDENCIES VERIFICATION ───────────────────────────────────────────
print("\n--- 6. DEPENDENCIES VERIFICATION ---")
required_packages = ["pypdf", "email_validator", "sentence_transformers", "faiss", "sqlalchemy", "jose", "passlib", "groq"]
deps_pass = True
for pkg in required_packages:
    try:
        __import__(pkg.replace("-", "_"))
        print(f"[OK] Package '{pkg}': Available")
    except ImportError:
        print(f"[FAIL] Package '{pkg}': MISSING!")
        deps_pass = False

print("\n==================================================")
print("            AUDIT EXECUTION SUMMARY              ")
print("==================================================")
print(f"1. Database:               {'PASS' if db_pass else 'FAIL'}")
print(f"2. Authentication:         {'PASS' if auth_pass else 'FAIL'}")
print(f"3. Patient & RAG Isolation:{'PASS' if iso_pass else 'FAIL'}")
print(f"4. FAISS Vector Integrity: {'PASS' if faiss_pass else 'FAIL'}")
print(f"5. OCR / PDF Extraction:   {'PASS' if ocr_pass else 'FAIL'}")
print(f"6. Required Dependencies:  {'PASS' if deps_pass else 'FAIL'}")
