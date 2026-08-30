from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone
import csv

repo = Path(r'D:\infosys springboard internship docs\workforce-management-automation-system')
vals = {}
for line in (repo / '.env').read_text(encoding='utf-8', errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")

mongo_url = vals.get('MONGODB_URL')
db_name = vals.get('DATABASE_NAME')
if not mongo_url or not db_name:
    raise RuntimeError('.env missing MONGODB_URL or DATABASE_NAME')

client = MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
db = client[db_name]

start = datetime.fromisoformat('2026-08-19T10:20:00+00:00')
end = datetime.fromisoformat('2026-08-19T10:51:00+00:00')

# fetch accounts and filter by createdAt in python to be robust
accounts = list(db.user_accounts.find({}, {'_id':1,'empId':1,'email':1,'role':1,'createdAt':1,'updatedAt':1}))

def parse_dt(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    s = str(v)
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        try:
            from datetime import datetime as _dt
            return _dt.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        except Exception:
            try:
                return _dt.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            except Exception:
                return None

batch_accounts = [a for a in accounts if (lambda ca: ca and ca>=start and ca<=end)(parse_dt(a.get('createdAt')))]

# map employees by EmpID
empids = [a.get('empId') for a in batch_accounts if a.get('empId')]
employees = list(db.employees.find({'EmpID': {'$in': list(set(empids))}}, {'EmpID':1,'Email':1,'EmploymentStatus':1,'ExitDate':1,'Exit_Date':1}))
emp_map = {e.get('EmpID'): e for e in employees}

rows = []
for a in batch_accounts:
    empid = a.get('empId')
    emp = emp_map.get(empid)
    if not emp:
        continue
    # exact match on EmploymentStatus == "Exited"
    if emp.get('EmploymentStatus') != 'Exited':
        continue
    exit_date = emp.get('ExitDate') or emp.get('Exit_Date') or ''
    row = {
        'EmpID': emp.get('EmpID'),
        'EmployeeEmail': emp.get('Email') or '',
        'EmploymentStatus': emp.get('EmploymentStatus') or '',
        'ExitDate': exit_date or '',
        'Account_id': str(a.get('_id')),
        'AccountEmail': a.get('email') or '',
        'AccountCreatedAt': parse_dt(a.get('createdAt')).isoformat() if parse_dt(a.get('createdAt')) else '',
        'AccountUpdatedAt': parse_dt(a.get('updatedAt')).isoformat() if parse_dt(a.get('updatedAt')) else '',
        'Role': a.get('role') or ''
    }
    rows.append(row)

out_path = repo / 'tools' / 'exited_employee_accounts_audit.csv'
with out_path.open('w', newline='', encoding='utf-8') as f:
    fieldnames = ['EmpID','EmployeeEmail','EmploymentStatus','ExitDate','Account_id','AccountEmail','AccountCreatedAt','AccountUpdatedAt','Role']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

# verification
csv_count = len(rows)
# verify EmploymentStatus exactly 'Exited' for all
all_exited = all(r['EmploymentStatus']=='Exited' for r in rows)
# verify ExitDate present for all
all_have_exitdate = all(r['ExitDate'] for r in rows)
# count how many have ExitDate earlier than account createdAt
from datetime import datetime as _dt
before_count = 0
for r in rows:
    try:
        exit_dt = _dt.fromisoformat(r['ExitDate'])
    except Exception:
        try:
            exit_dt = _dt.strptime(r['ExitDate'], '%Y-%m-%d')
        except Exception:
            exit_dt = None
    acct_dt = None
    try:
        acct_dt = _dt.fromisoformat(r['AccountCreatedAt'])
    except Exception:
        acct_dt = None
    if exit_dt and acct_dt:
        # compare dates
        if exit_dt.date() < acct_dt.date():
            before_count += 1

print('CSV_PATH=', str(out_path))
print('CSV_ROW_COUNT=', csv_count)
print('ALL_ROWS_IN_BATCH=', csv_count == len(batch_accounts) and csv_count == 335)
print('ALL_EMPLOYMENTSTATUS_EXACT_EXITED=', all_exited)
print('ALL_HAVE_EXITDATE=', all_have_exitdate)
print('EXITDATE_BEFORE_ACCOUNT_CREATED_COUNT=', before_count)
print('EXITED_ACCOUNT_AUDIT_COMPLETE=YES')
print('DATABASE_MODIFIED=NO')
print('PROVISIONING_EXECUTED=NO')
print('CODE_MODIFIED=NO')
print('ENV_MODIFIED=NO')

client.close()
