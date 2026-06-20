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

# Ensure tables are created locally
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def cleanup_user(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            db.delete(user)
            db.commit()
            print(f"Cleaned up test user: {email}")
    finally:
        db.close()

def run_tests():
    test_email = "test@example.com"
    
    print("\n--- Starting Day 36A Password Policy Verification Tests ---")
    
    try:
        # Case 1: Weak Password
        print("\nTest Case 1: Register with weak password (123456)")
        cleanup_user(test_email)
        payload = {"email": test_email, "password": "123456"}
        res = client.post("/auth/register", json=payload)
        print(f"Response status: {res.status_code}")
        assert res.status_code == 422, f"Expected 422, got {res.status_code}"
        print("PASS: Weak password rejected with 422")

        # Case 2: Missing Special Character
        print("\nTest Case 2: Register with missing special character (Password123)")
        cleanup_user(test_email)
        payload = {"email": test_email, "password": "Password123"}
        res = client.post("/auth/register", json=payload)
        print(f"Response status: {res.status_code}")
        assert res.status_code == 422, f"Expected 422, got {res.status_code}"
        print("PASS: Password without special character rejected with 422")

        # Case 3: Invalid Email
        print("\nTest Case 3: Register with invalid email (not-an-email)")
        payload = {"email": "not-an-email", "password": "Password@123"}
        res = client.post("/auth/register", json=payload)
        print(f"Response status: {res.status_code}")
        assert res.status_code == 422, f"Expected 422, got {res.status_code}"
        print("PASS: Malformed email rejected with 422")

        # Case 4: Valid Password
        print("\nTest Case 4: Register with valid password (Password@123)")
        cleanup_user(test_email)
        payload = {"email": test_email, "password": "Password@123"}
        res = client.post("/auth/register", json=payload)
        print(f"Response status: {res.status_code}")
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        print("PASS: Strong password and valid email accepted with 201")

        print("\nALL PASSWORD POLICY VERIFICATION TESTS PASSED SUCCESSFULLY!")
        
    finally:
        cleanup_user(test_email)

if __name__ == "__main__":
    run_tests()
