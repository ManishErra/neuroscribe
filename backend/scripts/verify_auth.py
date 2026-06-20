import sys
import os
from pathlib import Path

# Override DATABASE_URL for local sqlite testing
os.environ["DATABASE_URL"] = "sqlite:///./verification_test.db"

# Register CITEXT compiler fallback for SQLite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import CITEXT

@compiles(CITEXT, "sqlite")
def compile_citext_sqlite(element, compiler, **kw):
    return "TEXT"

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine, Base
from models import User
from auth_utils import jwt, JWT_SECRET, JWT_ALGORITHM
from datetime import datetime, timedelta, timezone

# Ensure tables are created locally
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def cleanup_user(email: str):
    db = SessionLocal()
    try:
        # Delete test user if exists
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            db.delete(user)
            db.commit()
            print(f"Cleaned up test user: {email}")
    finally:
        db.close()

def run_tests():
    test_email = "verify-doctor@neuroscribe.org"
    test_password = "Password@123"
    test_name = "Dr. Verification"
    
    # 0. Clean up any leftover test user
    cleanup_user(test_email)
    
    print("\n--- Starting Day 33 Auth Verification Tests ---")
    
    try:
        # Test Case 1: Register user
        print("\nTest Case 1: Register new user")
        payload = {"email": test_email, "password": test_password, "name": test_name}
        res = client.post("/auth/register", json=payload)
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["email"] == test_email.lower(), f"Expected normalized email, got {data['email']}"
        assert data["name"] == test_name
        assert "id" in data
        print("PASS: Register new user succeeded")

        # Test Case 2: Register duplicate email (case-insensitive check)
        print("\nTest Case 2: Register duplicate user (casing differences)")
        duplicate_payload = {
            "email": "  VERIFY-doctor@NEUROSCRIBE.org  ", 
            "password": "DifferentPassword@123", 
            "name": "Another Name"
        }
        res = client.post("/auth/register", json=duplicate_payload)
        assert res.status_code == 409, f"Expected 409, got {res.status_code}: {res.text}"
        print("PASS: Duplicate registration rejected with 409")

        # Test Case 3: Login with correct credentials
        print("\nTest Case 3: Login with correct credentials")
        login_payload = {"email": test_email, "password": test_password}
        res = client.post("/auth/login", json=login_payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        token_data = res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        token = token_data["access_token"]
        print("PASS: Login succeeded, token returned")

        # Test Case 4: Login with mixed-case and padded email
        print("\nTest Case 4: Login with mixed-case and whitespace in email")
        padded_login_payload = {"email": "  Verify-Doctor@NeuroScribe.Org  ", "password": test_password}
        res = client.post("/auth/login", json=padded_login_payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("PASS: Case-insensitive and trimmed email login succeeded")

        # Test Case 5: Login with incorrect password
        print("\nTest Case 5: Login with incorrect password")
        bad_login_payload = {"email": test_email, "password": "wrongpassword"}
        res = client.post("/auth/login", json=bad_login_payload)
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        print("PASS: Invalid password login rejected with 401")

        # Test Case 6: Call /auth/me with valid token
        print("\nTest Case 6: Get current user (/auth/me) with valid token")
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/auth/me", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        user_data = res.json()
        assert user_data["email"] == test_email.lower()
        assert user_data["name"] == test_name
        print("PASS: Fetch current user succeeded")

        # Test Case 7: Call /auth/me with invalid token
        print("\nTest Case 7: Call /auth/me with invalid token")
        headers = {"Authorization": "Bearer invalidtokenhere"}
        res = client.get("/auth/me", headers=headers)
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        print("PASS: Invalid token rejected with 401")

        # Test Case 8: Call /auth/me with expired token
        print("\nTest Case 8: Call /auth/me with expired token")
        # Manually forge an expired token
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_email).first()
        db.close()
        
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "exp": int(expired_time.timestamp())
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        res = client.get("/auth/me", headers=headers)
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        print("PASS: Expired token rejected with 401")

        print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

    finally:
        # Clean up database
        cleanup_user(test_email)

if __name__ == "__main__":
    run_tests()
