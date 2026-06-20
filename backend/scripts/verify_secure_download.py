import sys
import json
import uuid
import os
import io
from pathlib import Path
import datetime

# Configure database for local SQLite verification
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "super-secret-key-for-testing-32c-minimum-length"
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
            import datetime as dt
            return dt.date.today()
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

from main import app
from database import engine, Base, SessionLocal
from models import User, Patient, Report
from auth_utils import hash_password, create_access_token
from routers.reports import resolve_uploaded_report_disk_path
from fastapi.testclient import TestClient

client = TestClient(app)

def run():
    print("--- Setting up Secure Download Verification ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create Owner (Doctor A)
    doc_a = User(
        id=uuid.uuid4(),
        email="owner_a@example.com",
        name="Owner A",
        hashed_password=hash_password("test"),
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    # Create Non-Owner (Doctor B)
    doc_b = User(
        id=uuid.uuid4(),
        email="non_owner_b@example.com",
        name="Non Owner B",
        hashed_password=hash_password("test"),
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(doc_a)
    db.add(doc_b)
    db.commit()

    token_a = create_access_token(doc_a.id, doc_a.email, doc_a.name)
    token_b = create_access_token(doc_b.id, doc_b.email, doc_b.name)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create patient under Doctor A
    patient = Patient(id=uuid.uuid4(), name="Patient A", age=30, gender="M", owner_id=doc_a.id)
    db.add(patient)
    db.commit()

    # Upload file as Doctor A
    pdf_content = b"%PDF-1.4 Fake PDF Data Verification Bytes"
    file_tuple = ("test_report.pdf", io.BytesIO(pdf_content), "application/pdf")
    upload_resp = client.post(
        "/reports/upload",
        data={"patient_id": str(patient.id)},
        files={"file": file_tuple},
        headers=headers_a
    )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    report_data = upload_resp.json()
    report_id = report_data["id"]
    file_path = report_data["file_path"] # e.g. uploads/reports/uuid_filename
    
    print(f"Uploaded File Path: {file_path}")

    # TEST A: Report owner receives HTTP 200 from download
    print("--- Test A: Report owner receives HTTP 200 ---")
    dl_resp_a = client.get(f"/reports/{report_id}/download", headers=headers_a)
    print(f"Owner Download Status: {dl_resp_a.status_code}")
    assert dl_resp_a.status_code == 200

    # TEST B: Downloaded file bytes match originally uploaded file
    print("--- Test B: Downloaded file bytes match originally uploaded file ---")
    downloaded_bytes = dl_resp_a.content
    print(f"Bytes Match: {downloaded_bytes == pdf_content}")
    assert downloaded_bytes == pdf_content

    # TEST C: Non-owner receives HTTP 404 from download
    print("--- Test C: Non-owner receives HTTP 404 ---")
    dl_resp_b = client.get(f"/reports/{report_id}/download", headers=headers_b)
    print(f"Non-Owner Download Status: {dl_resp_b.status_code}")
    assert dl_resp_b.status_code == 404

    # TEST D: Unauthenticated download returns 401
    print("--- Test D: Unauthenticated download returns 401 ---")
    dl_resp_unauth = client.get(f"/reports/{report_id}/download")
    print(f"Unauthenticated Download Status: {dl_resp_unauth.status_code}")
    assert dl_resp_unauth.status_code == 401

    # TEST E: Direct access returns 404
    print("--- Test E: Direct static access returns 404 ---")
    static_url = f"/{file_path}"
    static_resp = client.get(static_url)
    print(f"Static Access Status: {static_resp.status_code}")
    assert static_resp.status_code == 404

    # Cleanup
    disk_path = resolve_uploaded_report_disk_path(file_path)
    if os.path.exists(disk_path):
        os.remove(disk_path)
    db.delete(patient)
    db.delete(doc_a)
    db.delete(doc_b)
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        db.delete(report)
    db.commit()
    print("\nALL SECURE DOWNLOAD TESTS PASSED!")

if __name__ == "__main__":
    run()
