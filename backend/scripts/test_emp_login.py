"""
Runtime test using FastAPI TestClient: login with EMP010000 and GET /api/profile.
This script performs read-only operations only (no PUT).
"""
import sys
import os
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

login_payload = {"identifier": "EMP010000", "password": "EMP010000"}
resp = client.post('/api/auth/login', json=login_payload)
print('login_status', resp.status_code)
if resp.status_code != 200:
    print('LOGIN_FAILED')
    print(resp.text)
    sys.exit(2)

# extract user but do not print token
json = resp.json()
user = json.get('user', {})
# Now call GET /profile with Authorization header
token = json.get('token')
headers = {'Authorization': 'Bearer ' + token}
profile_resp = client.get('/api/profile', headers=headers)
print('profile_status', profile_resp.status_code)
if profile_resp.status_code == 200:
    p = profile_resp.json()
    safe = {
        'userId': p.get('userId'),
        'empId': p.get('empId'),
        'role': p.get('role'),
        'department': p.get('department'),
        'avatar_present': bool(p.get('avatar'))
    }
    print('profile:', safe)
else:
    print('profile_body:', profile_resp.text)
    sys.exit(3)

# Do not perform PUT since it would write to DB
print('PUT_TEST: SKIPPED to avoid modifying production DB')
