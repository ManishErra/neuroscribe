import requests
import sys

BASE_URL = "http://localhost:8000"

def check():
    print("[*] Logging in as audit_doc_99@neuroscribe.com...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": "audit_doc_99@neuroscribe.com", "password": "Password123!@"})
    print("Login status:", res.status_code)
    if res.status_code != 200:
        print("[-] Login failed:", res.text)
        return
        
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("[*] Fetching patient directory...")
    res = requests.get(f"{BASE_URL}/patients/", headers=headers)
    print("Patients status:", res.status_code)
    patients = res.json()
    print(f"[+] Total Patients found: {len(patients)}")
    for p in patients:
        print(f"  - ID: {p['id']}, Name: {p['name']}, Age: {p['age']}, Gender: {p['gender']}")
        
    if patients:
        p_id = patients[0]["id"]
        print(f"[*] Listing sessions for patient {p_id}...")
        res = requests.get(f"{BASE_URL}/sessions/patient/{p_id}", headers=headers)
        print("Sessions:", res.status_code, res.json())
        
        print(f"[*] Listing reports for patient {p_id}...")
        res = requests.get(f"{BASE_URL}/reports/patient/{p_id}", headers=headers)
        print("Reports:", res.status_code, res.json())

if __name__ == "__main__":
    check()
