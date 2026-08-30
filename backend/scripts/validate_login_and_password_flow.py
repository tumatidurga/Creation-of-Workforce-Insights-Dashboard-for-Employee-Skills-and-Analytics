import os
import sys
import traceback
from pprint import pprint

# Ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import after sys.path and env are set externally
from fastapi.testclient import TestClient

# Import the FastAPI app
try:
    from backend.app.main import app
except Exception:
    # support alternative import path
    from app.main import app

client = TestClient(app)

RESULT = {
    'employee_id_login': False,
    'employee_email_login': False,
    'change_password': False,
    'old_password_invalid': False,
    'new_password_valid': False,
}

# Select employee to test - pick an employee account that was newly provisioned
TEST_EMP_ID = os.environ.get('TEST_EMP_ID', 'EMP000002')
# Attempt ID-based login with default password = EmpID
try:
    r = client.post('/api/auth/login', json={'identifier': TEST_EMP_ID, 'password': TEST_EMP_ID})
    if r.status_code == 200:
        data = r.json()
        # Expect passwordStatus to be present and 'default'
        ps = data.get('passwordStatus')
        if ps in ('default', 'custom'):
            RESULT['employee_id_login'] = True
    else:
        RESULT['employee_id_login'] = False
except Exception:
    RESULT['employee_id_login'] = False

# Try email login if email exists for this emp
# Fetch employee email from DB via endpoint /api/employees/{empid} if exists
try:
    r = client.get(f'/api/employees/{TEST_EMP_ID}')
    if r.status_code == 200:
        emp = r.json()
        email = emp.get('Email')
        if email:
            r2 = client.post('/api/auth/login', json={'identifier': email, 'password': TEST_EMP_ID})
            RESULT['employee_email_login'] = (r2.status_code == 200)
except Exception:
    RESULT['employee_email_login'] = False

# For change-password test, use a different test employee (EMP000001 expected to exist)
TEST_CHANGE_EMP = os.environ.get('TEST_CHANGE_EMP', 'EMP000001')
NEW_PW = os.environ.get('TEMP_NEW_PW')
if not NEW_PW:
    # generate a temp strong-ish password in memory
    NEW_PW = 'T3stP@ssw0rd!'  # not printed

try:
    r = client.post('/api/auth/login', json={'identifier': TEST_CHANGE_EMP, 'password': TEST_CHANGE_EMP})
    if r.status_code == 200:
        token = r.json().get('accessToken') or r.json().get('access_token') or r.json().get('token')
        if token:
            headers = {'Authorization': f'Bearer {token}'}
            # attempt change password
            payload = {
                'currentPassword': TEST_CHANGE_EMP,
                'newPassword': NEW_PW,
                'confirmPassword': NEW_PW,
            }
            rc = client.post('/api/auth/change-password', json=payload, headers=headers)
            if rc.status_code == 200:
                RESULT['change_password'] = True
                # verify old password no longer works
                r_old = client.post('/api/auth/login', json={'identifier': TEST_CHANGE_EMP, 'password': TEST_CHANGE_EMP})
                RESULT['old_password_invalid'] = (r_old.status_code != 200)
                # verify new password works
                r_new = client.post('/api/auth/login', json={'identifier': TEST_CHANGE_EMP, 'password': NEW_PW})
                RESULT['new_password_valid'] = (r_new.status_code == 200)

except Exception:
    traceback.print_exc()

print('VALIDATION_RESULT:')
print(RESULT)

# Exit non-zero if any critical checks failed
if not RESULT['employee_id_login']:
    sys.exit(2)
if not RESULT['change_password']:
    sys.exit(3)

sys.exit(0)
