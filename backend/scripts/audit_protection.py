import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

endpoints_to_test = [
    ("GET", "/patients"),
    ("GET", f"/patient-overview/{fake_uuid}"),
    ("GET", f"/patient-insights/{fake_uuid}"),
    ("GET", f"/sessions/patient/{fake_uuid}"),
    ("POST", "/generate-note", {}),
    ("GET", f"/reports/patient/{fake_uuid}"),
    ("POST", "/ask/", {"question": "what is blood pressure?"}),
    ("GET", f"/timeline/{fake_uuid}"),
    ("GET", "/auth/me")
]

print("--- Running Final Backend Route Protection Audit ---")
for method, url, *payload in endpoints_to_test:
    headers = {}
    if method == "GET":
        res = client.get(url, headers=headers)
    elif method == "POST":
        json_data = payload[0] if payload else {}
        res = client.post(url, json=json_data, headers=headers)
        
    status = res.status_code
    is_protected = "No" if status in [200, 201, 404, 422, 405] else "Yes (Protected)"
    print(f"{method:<4} {url:<50} | Status: {status:<3} | Protected: {is_protected}")
