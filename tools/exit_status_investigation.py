from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone
from collections import Counter, defaultdict
import re

repo = Path(r'D:\infosys springboard internship docs\workforce-management-automation-system')
vals = {}
for line in (repo / '.env').read_text(encoding='utf-8', errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")
client = MongoClient(vals['MONGODB_URL'], serverSelectionTimeoutMS=10000)
db = client[vals['DATABASE_NAME']]

start = datetime.fromisoformat('2026-08-19T10:20:00+00:00')
end = datetime.fromisoformat('2026-08-19T10:51:00+00:00')

# get batch accounts
accounts = list(db.user_accounts.find({}, {'empId':1,'email':1,'createdAt':1}))

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
            return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        except Exception:
            try:
                return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            except Exception:
                return None

batch_accounts = [a for a in accounts if (lambda ca: ca and ca>=start and ca<=end)(parse_dt(a.get('createdAt')))]

# find employees for which EmploymentStatus normalized == 'exited'
empids = [a.get('empId') for a in batch_accounts if a.get('empId')]
empids_set = set(empids)

# fetch employee docs for these empids
employees = list(db.employees.find({'EmpID': {'$in': list(empids_set)}}, {'EmpID':1,'EmploymentStatus':1,'ExitDate':1,'Exit_Date':1,'exitDate':1,'updatedAt':1,'updated_at':1}))

# select those where normalized EmploymentStatus == 'exited'
exited_emp_docs = [e for e in employees if (str(e.get('EmploymentStatus') or '').strip().lower()=='exited')]

# ensure we consider only those whose accounts are in batch
exited_empids = set(e.get('EmpID') for e in exited_emp_docs)

# Build EmploymentStatus exact value counts
status_counter = Counter()
for e in exited_emp_docs:
    status_counter[e.get('EmploymentStatus')] += 1

# Now analyze ExitDate values and compare with account createdAt
# build map empId -> account createdAt (take account from batch)
acct_created = {}
for a in batch_accounts:
    eid = a.get('empId')
    if eid in exited_empids:
        acct_created[eid] = parse_dt(a.get('createdAt'))

# For each exited employee, get ExitDate value from employee doc
before = 0
same_date = 0
after = 0
missing = 0
unparseable = 0
exitdate_values_counter = Counter()
for e in exited_emp_docs:
    eid = e.get('EmpID')
    # find exit date candidates
    val = None
    for k in ['ExitDate','Exit_Date','exitDate']:
        if k in e and e.get(k):
            val = e.get(k); break
    if val is None:
        missing += 1
        exitdate_values_counter[None] += 1
        continue
    exitdate_values_counter[str(val)] += 1
    # try parse date
    parsed = None
    s = str(val)
    try:
        parsed = datetime.fromisoformat(s)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            parsed = datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except Exception:
            parsed = None
    if not parsed:
        unparseable += 1
        continue
    acct_dt = acct_created.get(eid)
    if not acct_dt:
        # no account createdAt found, count as unparseable? but better skip
        unparseable += 1
        continue
    # compare dates: compare date parts
    exit_date_only = parsed.date()
    acct_date_only = acct_dt.date()
    if exit_date_only < acct_date_only:
        before += 1
    elif exit_date_only == acct_date_only:
        same_date += 1
    elif exit_date_only > acct_date_only:
        after += 1

# Print results
print('TOTAL_EXITED_EMPLOYEES_IN_BATCH=', len(exited_emp_docs))
print('EMPLOYMENTSTATUS_DISTINCT_VALUES_COUNT=', len(status_counter))
for k,v in sorted(status_counter.items(), key=lambda x: (-x[1], str(x[0]))):
    print(repr(k), v)

print('\nEXITDATE_VALUES_DISTRIBUTION_SAMPLE_COUNT=', len(exitdate_values_counter))
for k,v in exitdate_values_counter.most_common():
    print(repr(k), v)

print('\nEXITDATE_COMPARISON_COUNTS:')
print('ExitDate_before_account_creation=', before)
print('ExitDate_same_date_as_account_creation=', same_date)
print('ExitDate_after_account_creation=', after)
print('ExitDate_missing=', missing)
print('ExitDate_unparseable=', unparseable)

client.close()
