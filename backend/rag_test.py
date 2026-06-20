import requests, time

BASE_URL = 'http://localhost:8000'
LOGIN_DATA = {'username': 'doctor@neuroscribe.com', 'password': 'Password123!'}

print('1. Authenticating...')
resp = requests.post(f'{BASE_URL}/auth/token', data=LOGIN_DATA)
token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

print('2. Creating Patient A & B...')
p_a_resp = requests.post(f'{BASE_URL}/patients/', json={'name': 'Patient A', 'age': 45, 'gender': 'male'}, headers=headers)
p_b_resp = requests.post(f'{BASE_URL}/patients/', json={'name': 'Patient B', 'age': 30, 'gender': 'female'}, headers=headers)

p_a = p_a_resp.json()
p_b = p_b_resp.json()

print(f"Patient A Creation Resp: {p_a}")
print(f"Patient B Creation Resp: {p_b}")

if 'id' not in p_a or 'id' not in p_b:
    print('Failed to create patients. Exiting.')
    exit(1)

print('3. Uploading Reports...')
with open('patient_a_report.pdf', 'rb') as f_a:
    r_a = requests.post(f'{BASE_URL}/reports/upload', data={'patient_id': p_a['id']}, files={'file': f_a}, headers=headers).json()

with open('patient_b_report.pdf', 'rb') as f_b:
    r_b = requests.post(f'{BASE_URL}/reports/upload', data={'patient_id': p_b['id']}, files={'file': f_b}, headers=headers).json()

print(f"Upload A: {r_a}")
print(f"Upload B: {r_b}")

print('Waiting 15s for OCR processing...')
time.sleep(15)

print('4. Testing RAG Isolation...')
ans_a = requests.get(f'{BASE_URL}/search/ask', params={'patient_id': p_a['id'], 'query': 'What is the diagnosis?'}, headers=headers).json()
ans_b = requests.get(f'{BASE_URL}/search/ask', params={'patient_id': p_b['id'], 'query': 'What is the diagnosis?'}, headers=headers).json()

print('\n--- RAG ISOLATION RESULTS ---')
print(f"Patient A Answer: {ans_a}")
print(f"Patient B Answer: {ans_b}")
