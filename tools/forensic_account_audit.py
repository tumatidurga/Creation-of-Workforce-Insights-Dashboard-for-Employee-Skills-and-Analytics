from pathlib import Path
from pymongo import MongoClient
from datetime import datetime
from collections import Counter, defaultdict
import sys

repo = Path(r'D:\infosys springboard internship docs\workforce-management-automation-system')
vals = {}
for line in (repo / '.env').read_text(encoding='utf-8', errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")

client = MongoClient(vals['MONGODB_URL'], serverSelectionTimeoutMS=10000)
db = client[vals['DATABASE_NAME']]

employees = list(db.employees.find({}, {'EmpID':1, 'Email':1, 'EmploymentStatus':1}))
accounts = list(db.user_accounts.find({}, {'_id':1, 'empId':1, 'email':1, 'role':1, 'passwordStatus':1, 'mustChangePassword':1, 'createdAt':1, 'updatedAt':1}))

empid_set = set()
email_map = {}
empid_to_status = {}
for e in employees:
    eid = e.get('EmpID')
    if eid:
        empid_set.add(eid)
        empid_to_status[eid] = e.get('EmploymentStatus')
    email = e.get('Email')
    if email:
        email_map[email.lower()] = (e.get('EmploymentStatus'), e.get('EmpID'))

matched_by_empid = []
matched_by_email = []
orphan = []
accounts_active = 0
accounts_exited = 0

# duplicate detection
empid_counter = Counter()
email_counter = Counter()

# creation grouping
by_date = Counter()
by_date_hour = Counter()
created_times = []

# provisioning-like heuristic
prov_like = []

null_pw_accounts = []

for a in accounts:
    empId = a.get('empId')
    email = a.get('email')
    lower_email = email.lower() if isinstance(email, str) else None
    matched = False
    if empId and empId in empid_set:
        matched_by_empid.append(a)
        matched = True
        status = empid_to_status.get(empId)
        if status and status.lower() == 'active':
            accounts_active += 1
        if status and status.lower() == 'exited':
            accounts_exited += 1
    elif lower_email and lower_email in email_map:
        matched_by_email.append(a)
        matched = True
        status,_eid = email_map[lower_email]
        if status and status.lower() == 'active':
            accounts_active += 1
        if status and status.lower() == 'exited':
            accounts_exited += 1
    else:
        orphan.append(a)

    if empId:
        empid_counter[empId] += 1
    if lower_email:
        email_counter[lower_email] += 1

    ca = a.get('createdAt')
    if ca:
        if isinstance(ca, str):
            try:
                dt = datetime.fromisoformat(ca)
            except:
                try:
                    dt = datetime.strptime(ca, '%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    dt = None
        elif isinstance(ca, datetime):
            dt = ca
        else:
            dt = None
        if dt:
            created_times.append(dt)
            by_date[dt.date().isoformat()] += 1
            by_date_hour[f"{dt.date().isoformat()}T{dt.hour:02d}"] += 1

    # provisioning-like heuristic: role EMPLOYEE, passwordStatus default, mustChangePassword False
    if a.get('role') == 'EMPLOYEE' and a.get('passwordStatus') == 'default' and a.get('mustChangePassword') in (False, 'false', 'False'):
        prov_like.append(a)

    if a.get('passwordStatus') is None and a.get('mustChangePassword') is None:
        null_pw_accounts.append(a)

# Active employees without accounts
active_empids = set(e.get('EmpID') for e in employees if e.get('EmploymentStatus') and e.get('EmploymentStatus').lower()=='active' and e.get('EmpID'))
accounts_empids = set(a.get('empId') for a in accounts if a.get('empId'))
# also consider matching by email
accounts_emails = set((a.get('email') or '').lower() for a in accounts if a.get('email'))

active_with_account = set()
for e in employees:
    if e.get('EmploymentStatus') and e.get('EmploymentStatus').lower()=='active':
        eid = e.get('EmpID')
        email = (e.get('Email') or '').lower()
        if (eid and eid in accounts_empids) or (email and email in accounts_emails):
            active_with_account.add(eid)

active_without_account = len([e for e in employees if e.get('EmploymentStatus') and e.get('EmploymentStatus').lower()=='active' and not ((e.get('EmpID') and e.get('EmpID') in accounts_empids) or ((e.get('Email') or '').lower() in accounts_emails))])

# duplicates
duplicate_empids = {k:v for k,v in empid_counter.items() if v>1}
duplicate_emails = {k:v for k,v in email_counter.items() if v>1}

# creation earliest/latest overall
earliest = min(created_times).isoformat() if created_times else None
latest = max(created_times).isoformat() if created_times else None

# provision-like stats
prov_count = len(prov_like)
prov_roles = Counter(a.get('role') for a in prov_like)
prov_pwstatus = Counter(a.get('passwordStatus') for a in prov_like)
prov_mustchg = Counter(a.get('mustChangePassword') for a in prov_like)
prov_times = []
for a in prov_like:
    ca = a.get('createdAt')
    if isinstance(ca, datetime): prov_times.append(ca)
    else:
        try:
            prov_times.append(datetime.fromisoformat(str(ca)))
        except:
            pass
prov_earliest = min(prov_times).isoformat() if prov_times else None
prov_latest = max(prov_times).isoformat() if prov_times else None

# accounts belonging to exited employees
exited_accounts_count = 0
for a in accounts:
    eid = a.get('empId')
    if eid and eid in empid_to_status and empid_to_status[eid] and empid_to_status[eid].lower()=='exited':
        exited_accounts_count += 1

# Print concise forensic report
print('USER_ACCOUNTS_TOTAL=', len(accounts))
print('MATCHED_BY_EMPID=', len(matched_by_empid))
print('MATCHED_BY_EMAIL_ONLY=', len(matched_by_email))
print('ORPHAN_ACCOUNTS=', len(orphan))
print('ACCOUNTS_FOR_ACTIVE_EMPLOYEES=', accounts_active)
print('ACCOUNTS_FOR_EXITED_EMPLOYEES=', accounts_exited)
print('ACTIVE_EMPLOYEES_WITHOUT_ACCOUNT=', active_without_account)
print('DUPLICATE_ACCOUNT_EMPID_COUNT=', sum(1 for v in empid_counter.values() if v>1))
print('DUPLICATE_ACCOUNT_EMAIL_COUNT=', sum(1 for v in email_counter.values() if v>1))
print('EARLIEST_ACCOUNT_CREATED_AT=', earliest)
print('LATEST_ACCOUNT_CREATED_AT=', latest)
print('PROVISION_LIKE_ACCOUNTS_COUNT=', prov_count)
print('PROVISION_LIKE_ROLES=', dict(prov_roles))
print('PROVISION_LIKE_PASSWORDSTATUS=', dict(prov_pwstatus))
print('PROVISION_LIKE_MUSTCHANGEPASSWORD=', dict(prov_mustchg))
print('PROVISION_LIKE_EARLIEST=', prov_earliest)
print('PROVISION_LIKE_LATEST=', prov_latest)
print('ACCOUNTS_BELONGING_TO_EXITED_EMPLOYEES=', exited_accounts_count)
print('\nCREATION_BY_DATE_TOP=')
for k,v in sorted(by_date.items()):
    print(k, v)
print('\nCREATION_BY_DATE_HOUR_TOP=')
for k,v in sorted(by_date_hour.items()):
    print(k, v)

print('\nNULL_PASSWORDSTATUS_ACCOUNTS_COUNT=', len(null_pw_accounts))
if null_pw_accounts:
    print('NULL_PASSWORDSTATUS_SAFE_METADATA:')
    for a in null_pw_accounts:
        print('|'.join([str(a.get('_id')), str(a.get('empId')), str(a.get('email')), str(a.get('role')), str(a.get('passwordStatus')), str(a.get('mustChangePassword')), str(a.get('createdAt')), str(a.get('updatedAt'))]))

if duplicate_empids:
    print('\nDUPLICATE_EMPID_ENTRIES_SAMPLE=')
    for k,v in list(duplicate_empids.items())[:20]:
        print(k, v)
if duplicate_emails:
    print('\nDUPLICATE_EMAIL_ENTRIES_SAMPLE=')
    for k,v in list(duplicate_emails.items())[:20]:
        print(k, v)

# orphan sample count limit
print('\nORPHAN_SAMPLE_COUNT=', min(50, len(orphan)))
for a in orphan[:50]:
    print('|'.join([str(a.get('_id')), str(a.get('empId')), str(a.get('email')), str(a.get('role')), str(a.get('passwordStatus')), str(a.get('mustChangePassword')), str(a.get('createdAt')), str(a.get('updatedAt'))]))

# exit
sys.exit(0)
