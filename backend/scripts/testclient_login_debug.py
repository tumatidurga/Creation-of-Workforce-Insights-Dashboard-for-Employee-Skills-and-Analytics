import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from backend.app.main import app
except Exception:
    from app.main import app

from fastapi.testclient import TestClient
client = TestClient(app)

payload = {'identifier': 'EMP000002', 'password': 'EMP000002'}
print('Posting:', payload)
r = client.post('/api/auth/login', json=payload)
print('status', r.status_code)
print('body:', r.text)
