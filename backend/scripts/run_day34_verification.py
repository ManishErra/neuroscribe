import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User
from auth_utils import jwt, JWT_SECRET, JWT_ALGORITHM

client = TestClient(app)
fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

def get_or_create_test_user():
    db = SessionLocal()
    email = "test-verification-day34@neuroscribe.org"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password="dummyhashedpassword",
            name="Verification Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user

def cleanup_test_user():
    db = SessionLocal()
    email = "test-verification-day34@neuroscribe.org"
    user = db.query(User).filter(User.email == email).first()
    if user:
        db.delete(user)
        db.commit()
    db.close()

def generate_tokens(user_id: uuid.UUID, email: str):
    # Valid token
    valid_expire = datetime.now(timezone.utc) + timedelta(hours=1)
    valid_payload = {"sub": str(user_id), "email": email, "name": "Test User", "exp": int(valid_expire.timestamp())}
    valid_token = jwt.encode(valid_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Expired token
    expired_expire = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_payload = {"sub": str(user_id), "email": email, "name": "Test User", "exp": int(expired_expire.timestamp())}
    expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return valid_token, expired_token

def test_endpoint(method, url, payload, headers):
    if method == "GET":
        return client.get(url, headers=headers)
    elif method == "POST":
        return client.post(url, json=payload, headers=headers)
    return None

def run_verification():
    user = get_or_create_test_user()
    valid_token, expired_token = generate_tokens(user.id, user.email)
    
    print("\n--- Day 34 Route Protection Verification Run ---")
    
    endpoints = [
        ("GET", "/patients", {}, 200),
        ("GET", f"/patient-overview/{fake_uuid}", {}, 404),
        ("GET", f"/patient-insights/{fake_uuid}", {}, 404),
        ("GET", f"/sessions/patient/{fake_uuid}", {}, 200),
        ("POST", "/generate-note", {}, 422),
        ("GET", f"/reports/patient/{fake_uuid}", {}, 404),
        ("POST", "/ask/", {"question": "what is blood pressure?"}, 200),
        ("GET", f"/timeline/{fake_uuid}", {}, 404),
        ("GET", f"/compare/{fake_uuid}", {}, 404),
        ("POST", "/upload-audio", {}, 422),
        ("POST", "/embed/note", {}, 422),
    ]
    
    all_passed = True
    print("\n1. GATED CLINICAL ROUTERS VERIFICATION MATRIX")
    print(f"{'Endpoint':<50} | {'Condition':<15} | {'Exp Status':<10} | {'Act Status':<10} | {'Result':<5}")
    print("-" * 100)
    
    for method, url, payload, expected_valid_status in endpoints:
        for condition, token_val, expected_status in [
            ("No Token", None, 401),
            ("Invalid Token", "invalidtokenhere", 401),
            ("Expired Token", expired_token, 401),
            ("Valid Token", valid_token, expected_valid_status)
        ]:
            headers = {}
            if token_val:
                headers["Authorization"] = f"Bearer {token_val}"
                
            res = test_endpoint(method, url, payload, headers)
            status = res.status_code if res else 500
            
            passed = status == expected_status
            if not passed:
                all_passed = False
                
            res_str = "PASS" if passed else "FAIL"
            print(f"{method:<4} {url:<45} | {condition:<15} | {expected_status:<10} | {status:<10} | {res_str}")
            
    print("\n2. AUTHENTICATION BOUNDARY VERIFICATION")
    
    # Register (Public)
    email_reg = f"verify-register-{uuid.uuid4().hex[:6]}@neuroscribe.org"
    res_reg = client.post("/auth/register", json={"email": email_reg, "password": "Password@123", "name": "Verify Reg"})
    passed_reg = res_reg.status_code == 201
    print(f"POST /auth/register (Public)                 | Expected: 201 | Actual: {res_reg.status_code} | {'PASS' if passed_reg else 'FAIL'}")
    if not passed_reg:
        all_passed = False
        
    # Login (Public)
    res_login = client.post("/auth/login", json={"email": email_reg, "password": "Password@123"})
    passed_login = res_login.status_code == 200
    print(f"POST /auth/login (Public)                    | Expected: 200 | Actual: {res_login.status_code} | {'PASS' if passed_login else 'FAIL'}")
    if not passed_login:
        all_passed = False
        
    # clean registered user
    db = SessionLocal()
    created_u = db.query(User).filter(User.email == email_reg).first()
    if created_u:
        db.delete(created_u)
        db.commit()
    db.close()
        
    # GET /auth/me (Protected)
    res_me_anon = client.get("/auth/me")
    passed_me_anon = res_me_anon.status_code == 401
    print(f"GET /auth/me (No Token)                      | Expected: 401 | Actual: {res_me_anon.status_code} | {'PASS' if passed_me_anon else 'FAIL'}")
    if not passed_me_anon:
        all_passed = False
        
    res_me_valid = client.get("/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    passed_me_valid = res_me_valid.status_code == 200
    print(f"GET /auth/me (Valid Token)                   | Expected: 200 | Actual: {res_me_valid.status_code} | {'PASS' if passed_me_valid else 'FAIL'}")
    if not passed_me_valid:
        all_passed = False

    cleanup_test_user()
    
    if all_passed:
        print("\nALL VERIFICATION MATRIX CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME VERIFICATION MATRIX CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
