import os
import secrets
import sys
from fastapi.testclient import TestClient

# Environment overrides for this process only
os.environ['MONGODB_URL'] = os.environ.get('MONGODB_URL', 'mongodb://127.0.0.1:27017')
os.environ['DATABASE_NAME'] = os.environ.get('DATABASE_NAME', 'workforce_db_test')
# Ensure a non-empty AUTH_BOOTSTRAP_PASSWORD so login endpoint doesn't reject
os.environ['AUTH_BOOTSTRAP_PASSWORD'] = os.environ.get('AUTH_BOOTSTRAP_PASSWORD', 'bootstrap-test-password')

# We will set EMPLOYEE_TEST_PASSWORD to the EmpID value for the test employee(s)

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.app.main import app
from backend.app.config import settings
from backend.app.database import connect_to_mongo, get_database

import asyncio
# Safety check: ensure settings.DATABASE_NAME endswith _test to avoid accidental production runs
if not getattr(settings, 'DATABASE_NAME', '').endswith('_test'):
    print('ERROR: application settings DATABASE_NAME is not a test database:', settings.DATABASE_NAME)
    sys.exit(2)

# Ensure the app's DB connection is established for endpoints
try:
    asyncio.run(connect_to_mongo())
except Exception as e:
    print('WARNING: connect_to_mongo failed:', e)

client = TestClient(app)

# Discover employees directly from DB to avoid requiring auth for this script
from pymongo import MongoClient
mongo = MongoClient(os.environ['MONGODB_URL'], serverSelectionTimeoutMS=5000)
db = mongo[os.environ['DATABASE_NAME']]

employees = list(db.employees.find({}, {'_id':0}))
if not employees:
    print('NO_EMPLOYEES')
    sys.exit(4)

# Choose two employees: one for keep-default, one for change-password
emp1 = employees[0]
emp2 = employees[1] if len(employees) > 1 else employees[0]

emp1_id = emp1.get('EmpID') or emp1.get('empId')
emp1_email = emp1.get('Email') or emp1.get('email')
emp2_id = emp2.get('EmpID') or emp2.get('empId')
emp2_email = emp2.get('Email') or emp2.get('email')

# Set test passwords in env for compatibility with existing tests
os.environ['EMPLOYEE_TEST_PASSWORD'] = emp1_id

results = {}

# Helper to login and return token and user
def login(identifier, password):
    r = client.post('/api/auth/login', json={'identifier': identifier, 'password': password})
    return r

# 5. Verify default-password login for emp2
r_login = login(emp2_id, emp2_id)
results['emp2_login_status'] = r_login.status_code
if r_login.status_code == 200:
    token = r_login.json().get('token')
    user = r_login.json().get('user')
    results['emp2_user_role'] = user.get('role')
    results['emp2_passwordStatus'] = user.get('passwordStatus')
    results['emp2_mustChangePassword'] = user.get('mustChangePassword')
else:
    results['emp2_error'] = r_login.text

# 6. Test email login for emp2
r_login_email = login(emp2_email, emp2_id)
results['emp2_email_login_status'] = r_login_email.status_code

# 7. Keep default: simulate by accepting keep default (front-end does no API call). Verify subsequent login still works
r_keep = login(emp2_id, emp2_id)
results['emp2_keep_default_login_status'] = r_keep.status_code

# 8. Change password for emp1 (use emp1)
# login emp1 with default
r1 = login(emp1_id, emp1_id)
results['emp1_initial_login'] = r1.status_code
if r1.status_code != 200:
    print('ERROR: emp1 initial login failed')
    print(r1.text)
    sys.exit(5)

token1 = r1.json()['token']
headers = {'Authorization': f'Bearer {token1}'}

# Attempt password change: current = emp1_id, new = random secure
new_pw = secrets.token_urlsafe(16)
change_payload = {'currentPassword': emp1_id, 'newPassword': new_pw, 'confirmPassword': new_pw}
rc = client.post('/api/auth/change-password', json=change_payload, headers=headers)
results['emp1_change_status'] = rc.status_code

# Verify login with new password works
r_new = login(emp1_id, new_pw)
results['emp1_login_with_new'] = r_new.status_code
# Verify old password fails
r_old = login(emp1_id, emp1_id)
results['emp1_login_with_old'] = r_old.status_code

# 10. Reprovisioning safety: run provisioning script again (non-dry-run) and ensure no overwrite
os.environ['PROVISION_DRY_RUN'] = 'false'
import subprocess, sys
proc = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'provision_employee_accounts.py')], env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
prov_out = proc.stdout + '\n' + proc.stderr
results['provision_rerun_output'] = prov_out

# After reprovision, check emp1 account passwordStatus
r_me = None
if r_new.status_code == 200:
    token_new = r_new.json().get('token')
    r_me = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token_new}'})
    if r_me.status_code == 200:
        results['emp1_passwordStatus_after_reprovision'] = r_me.json().get('passwordStatus')

# Print concise, non-sensitive results
print('EMP1_ID=', emp1_id)
print('EMP2_ID=', emp2_id)
print('EMP1_EMAIL=', emp1_email)
print('EMP2_EMAIL=', emp2_email)
print('EMP2_default_login_status=', results.get('emp2_login_status'))
print('EMP2_email_login_status=', results.get('emp2_email_login_status'))
print('EMP2_passwordStatus=', results.get('emp2_passwordStatus'))
print('EMP2_mustChangePassword=', results.get('emp2_mustChangePassword'))
print('EMP1_change_status=', results.get('emp1_change_status'))
print('EMP1_login_with_new=', results.get('emp1_login_with_new'))
print('EMP1_login_with_old=', results.get('emp1_login_with_old'))
print('PROVISION_RERUN_STATUS=', 'OK' if 'STATUS=SUCCESS' in prov_out else 'FAIL')
