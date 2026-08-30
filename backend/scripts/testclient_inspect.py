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

r = client.get('/api/employees/EMP000002')
print('status', r.status_code)
try:
    print(r.json())
except Exception as e:
    print('no json:', e)
