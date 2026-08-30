from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import re

repo = Path(r'D:\infosys springboard internship docs\workforce-management-automation-system')
vals = {}
for line in (repo / '.env').read_text(encoding='utf-8', errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")
client = MongoClient(vals['MONGODB_URL'], serverSelectionTimeoutMS=10000)
db = client[vals['DATABASE_NAME']]

# load employees mapping
employees = list(db.employees.find({}, {'EmpID':1, 'Email':1, 'EmploymentStatus':1}))
empid_set = set(e.get('EmpID') for e in employees if e.get('EmpID'))
email_map = { (e.get('Email') or '').lower(): (e.get('EmploymentStatus') or '') for e in employees if e.get('Email') }
active_empids = set(e.get('EmpID') for e in employees if (e.get('EmploymentStatus') or '').strip().lower()=='active' and e.get('EmpID'))

# time window
start = datetime.fromisoformat('2026-08-19T10:20:00+00:00')
end = datetime.fromisoformat('2026-08-19T10:51:00+00:00')

# fetch all accounts and filter in python
accounts = list(db.user_accounts.find({}, {'_id':1,'empId':1,'email':1,'role':1,'passwordStatus':1,'mustChangePassword':1,'createdAt':1,'updatedAt':1}))

batch_accounts = []

def parse_dt(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    s = str(v)
    try:
        # handle ISO with offset
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # try common Z format
        try:
            return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        except Exception:
            try:
                return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            except Exception:
                return None

for a in accounts:
    ca = parse_dt(a.get('createdAt'))
    if not ca:
        continue
    if ca >= start and ca < end:
        a['_parsed_createdAt'] = ca
        batch_accounts.append(a)

# 1
num_in_window = len(batch_accounts)

# 2 matches
matched_by_empid = 0
matched_by_email = 0
no_employee_match = 0

# 3 employee status counts
status_counts = {'Active':0,'Exited':0,'Other':0,'Orphan':0}

# sets for empid lists
empids_in_batch = []

for a in batch_accounts:
    empId = a.get('empId')
    email = (a.get('email') or '').lower()
    matched = False
    if empId and empId in empid_set:
        matched_by_empid += 1
        matched = True
        empids_in_batch.append(empId)
        status = next((e.get('EmploymentStatus') for e in employees if e.get('EmpID')==empId), '')
        if status and status.strip().lower()=='active':
            status_counts['Active'] += 1
        elif status and status.strip().lower()=='exited':
            status_counts['Exited'] += 1
        else:
            status_counts['Other'] += 1
    elif email and email in email_map:
        matched_by_email += 1
        matched = True
        status = email_map[email]
        if status and status.strip().lower()=='active':
            status_counts['Active'] += 1
        elif status and status.strip().lower()=='exited':
            status_counts['Exited'] += 1
        else:
            status_counts['Other'] += 1
    else:
        no_employee_match += 1
        status_counts['Orphan'] += 1

# 4 EmpID range and lists
# consider only accounts that have empId present
empid_nums = []
empid_strings = []
for a in batch_accounts:
    e = a.get('empId')
    if e:
        # extract trailing digits
        m = re.search(r'([0-9]+)$', str(e))
        if m:
            num = int(m.group(1))
            empid_nums.append(num)
            empid_strings.append((num, str(e)))
        else:
            # fallback: skip
            pass

unique_empids = sorted(set([s for (_,s) in empid_strings]), key=lambda x: int(re.search(r'([0-9]+)$', x).group(1)) if re.search(r'([0-9]+)$', x) else float('inf'))
unique_count = len(unique_empids)
smallest_empid = unique_empids[0] if unique_empids else None
largest_empid = unique_empids[-1] if unique_empids else None
first_20 = unique_empids[:20]
last_20 = unique_empids[-20:]

# sequential test
if empid_nums:
    minv = min(empid_nums)
    maxv = max(empid_nums)
    sequential = (maxv - minv + 1 == len(set(empid_nums)))
else:
    sequential = False

# 5 Compare with active employees
active_with_accounts_from_batch = 0
for eid in active_empids:
    # check if this active empid has an account in batch
    if eid in set(empids_in_batch):
        active_with_accounts_from_batch += 1
    else:
        # also check email-based matches: get employee email and see if any batch account uses that email
        emp_email = next((e.get('Email') for e in employees if e.get('EmpID')==eid), None)
        if emp_email and any((a.get('email') or '').lower()==(emp_email or '').lower() for a in batch_accounts):
            active_with_accounts_from_batch += 1

active_total = len(active_empids)
active_without_accounts_from_batch = active_total - active_with_accounts_from_batch

# 6 group by 5-minute intervals
interval_counts = {}
# create bins starting from start to end in 5-minute increments
cur = start
while cur < end:
    interval_counts[cur.isoformat()] = 0
    cur += timedelta(minutes=5)

for a in batch_accounts:
    ca = a['_parsed_createdAt']
    # floor to 5-min
    minute = (ca.minute // 5) * 5
    flo = ca.replace(minute=minute, second=0, microsecond=0)
    flo = flo.replace(tzinfo=timezone.utc)
    key = flo.isoformat()
    if key not in interval_counts:
        # if outside due to timezone parsing differences, assign appropriately
        # normalize to nearest lower 5-min within window
        # compute flo via arithmetic
        delta = ca - start
        bins = int(delta.total_seconds() // (5*60))
        flo2 = start + timedelta(minutes=5*bins)
        key = flo2.isoformat()
        if key not in interval_counts:
            # skip
            continue
    interval_counts[key] += 1

# 7 Provisioning script behavior summary
batch_size = 500
active_only_filtering = True
existing_account_skip = True
account_limit = None
canary_behavior = (
    "If CANARY_EMP_ID is set, script runs a single-account canary flow: it validates the EmpID exists, email is valid, employee is active, checks no existing account by empId or email, and on DRY_RUN reports WOULD_CREATE; on real run it creates exactly one account for that EmpID and returns."
)

# Print results exactly as requested
print('NUMBER_IN_WINDOW=', num_in_window)
print('MATCH_BY_EMPID=', matched_by_empid)
print('MATCH_BY_EMAIL=', matched_by_email)
print('NO_EMPLOYEE_MATCH=', no_employee_match)
print('')
print('EMPLOYEE_STATUS_COUNTS:')
print('Active=', status_counts['Active'])
print('Exited=', status_counts['Exited'])
print('Other=', status_counts['Other'])
print('Orphan=', status_counts['Orphan'])
print('')
print('EMPID_RANGE:')
print('SMALLEST_EMPID=', smallest_empid)
print('LARGEST_EMPID=', largest_empid)
print('FIRST_20_EMPIDS=', ','.join(first_20))
print('LAST_20_EMPIDS=', ','.join(last_20))
print('UNIQUE_EMPID_COUNT=', unique_count)
print('EMPIDS_SEQUENTIAL=', 'YES' if sequential else 'NO')
print('')
print('COMPARE_WITH_ACTIVE:')
print('ACTIVE_EMPLOYEES_WITH_ACCOUNTS_IN_BATCH=', active_with_accounts_from_batch)
print('ACTIVE_EMPLOYEES_WITHOUT_ACCOUNTS_IN_BATCH=', active_without_accounts_from_batch)
print('')
print('CREATION_5MIN_INTERVALS:')
for k in sorted(interval_counts.keys()):
    print(k, interval_counts[k])
print('')
print('PROVISIONING_SCRIPT_BEHAVIOR:')
print('BATCH_SIZE=', batch_size)
print('ACTIVE_ONLY_FILTERING=', 'YES' if active_only_filtering else 'NO')
print('EXISTING_ACCOUNT_SKIP=', 'YES' if existing_account_skip else 'NO')
print('ACCOUNT_LIMIT=', account_limit)
print('CANARY_EMP_ID_BEHAVIOR=', canary_behavior)
print('')
print('FORENSIC_QUERY_COMPLETE=YES')
print('DATABASE_MODIFIED=NO')
print('PROVISIONING_EXECUTED=NO')

client.close()
