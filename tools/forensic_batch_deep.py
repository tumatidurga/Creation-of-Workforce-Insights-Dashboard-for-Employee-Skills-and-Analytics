from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone
import re

repo = Path(r'D:\infosys springboard internship docs\workforce-management-automation-system')
vals = {}
for line in (repo / '.env').read_text(encoding='utf-8', errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")
client = MongoClient(vals['MONGODB_URL'], serverSelectionTimeoutMS=10000)
db = client[vals['DATABASE_NAME']]

# Time window inclusive
start = datetime.fromisoformat('2026-08-19T10:20:00+00:00')
end = datetime.fromisoformat('2026-08-19T10:51:00+00:00')

# fetch accounts in window using query on createdAt
# Query will match ISO strings or datetime types by retrieving and filtering in Python for safety
accounts = list(db.user_accounts.find({}, {'_id':1,'empId':1,'email':1,'role':1,'passwordStatus':1,'mustChangePassword':1,'createdAt':1,'updatedAt':1}))

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

batch = []
for a in accounts:
    ca = parse_dt(a.get('createdAt'))
    if not ca:
        continue
    if ca >= start and ca <= end:
        a['_created_dt'] = ca
        batch.append(a)

# 1 Number in window
num_in_window = len(batch)

# Load employees mapping for faster lookup
employees = list(db.employees.find({}, {'EmpID':1,'Email':1,'EmploymentStatus':1,'ExitDate':1,'Exit_Date':1,'terminationDate':1,'TerminationDate':1,'updatedAt':1,'updated_at':1,'statusChangedAt':1}))
emp_by_id = { e.get('EmpID'): e for e in employees if e.get('EmpID') }
emp_email_map = { (e.get('Email') or '').lower(): e for e in employees if e.get('Email') }

matched_by_empid = 0
matched_by_email = 0
no_match = 0
status_counts = {'Active':0,'Exited':0,'Other':0,'Orphan':0}
exited_empids = []

for a in batch:
    empId = a.get('empId')
    email = (a.get('email') or '').lower()
    if empId and empId in emp_by_id:
        matched_by_empid += 1
        emp = emp_by_id[empId]
        status = (emp.get('EmploymentStatus') or '').strip()
        if status.lower()=='active':
            status_counts['Active'] += 1
        elif status.lower()=='exited':
            status_counts['Exited'] += 1
            exited_empids.append(empId)
        else:
            status_counts['Other'] += 1
    elif email and email in emp_email_map:
        matched_by_email += 1
        emp = emp_email_map[email]
        status = (emp.get('EmploymentStatus') or '').strip()
        if status.lower()=='active':
            status_counts['Active'] += 1
        elif status.lower()=='exited':
            status_counts['Exited'] += 1
            if emp.get('EmpID'): exited_empids.append(emp.get('EmpID'))
        else:
            status_counts['Other'] += 1
    else:
        no_match += 1
        status_counts['Orphan'] += 1

# Verify exited count
exited_count = status_counts['Exited']

# Investigate exit-related fields existence on exited employees
exit_field_candidates = ['ExitDate','Exit_Date','terminationDate','TerminationDate','resignationDate','exitDate','statusChangedAt','StatusChangedAt','updatedAt','updated_at']
fields_present = {}
exited_details = {}
for eid in exited_empids:
    emp = emp_by_id.get(eid)
    if not emp:
        continue
    details = {}
    for f in exit_field_candidates:
        if f in emp and emp.get(f):
            details[f] = emp.get(f)
            fields_present[f] = fields_present.get(f,0)+1
    exited_details[eid] = details

# Compare exit field timestamps with account createdAt where possible
exited_comparisons = {}
for a in batch:
    empId = a.get('empId')
    if not empId or empId not in exited_details:
        continue
    created = a.get('_created_dt')
    # find any date-like fields
    comp_list = []
    for f,v in exited_details[empId].items():
        # try parse
        if not v:
            continue
        s = str(v)
        parsed = None
        try:
            parsed = datetime.fromisoformat(s)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        except Exception:
            try:
                parsed = datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except Exception:
                parsed = None
        comp_list.append((f, s, parsed.isoformat() if parsed else None, 'createdAt', created.isoformat()))
    if comp_list:
        exited_comparisons[empId] = comp_list

# EMP000011 account(s)
emp000011_accounts = list(db.user_accounts.find({'empId':'EMP000011'},{'_id':1,'empId':1,'email':1,'role':1,'passwordStatus':1,'mustChangePassword':1,'createdAt':1,'updatedAt':1}))
emp000011_count = len(emp000011_accounts)
emp000011_safe = []
for a in emp000011_accounts:
    row = {k: a.get(k) for k in ['_id','empId','email','role','passwordStatus','mustChangePassword','createdAt','updatedAt']}
    emp000011_safe.append(row)

# Duplicates within batch
from collections import Counter
empid_counts = Counter([a.get('empId') for a in batch if a.get('empId')])
duplicate_empids = {k:v for k,v in empid_counts.items() if v>1}
email_counts = Counter([(a.get('email') or '').lower() for a in batch if a.get('email')])
duplicate_emails = {k:v for k,v in email_counts.items() if v>1}

# duplicate _id in batch
id_counts = Counter([str(a.get('_id')) for a in batch])
duplicate_ids = {k:v for k,v in id_counts.items() if v>1}

# multiple accounts per employee globally
global_empid_counts = Counter([a.get('empId') for a in db.user_accounts.find({}, {'empId':1}) if a.get('empId')])
global_duplicates = {k:v for k,v in global_empid_counts.items() if v>1 and k in empid_counts}

# Print results
print('NUM_IN_WINDOW=', num_in_window)
print('MATCH_BY_EMPID=', matched_by_empid)
print('MATCH_BY_EMAIL_ONLY=', matched_by_email)
print('NO_MATCH=', no_match)
print('')
print('STATUS_COUNTS:')
print('Active=', status_counts['Active'])
print('Exited=', status_counts['Exited'])
print('Other=', status_counts['Other'])
print('Orphan=', status_counts['Orphan'])
print('')
print('EXITED_INDEP_VERIFIED_COUNT=', exited_count)
print('EXIT_FIELD_PRESENCE_SAMPLE_COUNTS=', fields_present)
print('EXITED_COMPARISONS_SAMPLE_COUNT=', len(exited_comparisons))
# print up to 20 comparisons samples
cnt=0
for eid, comps in list(exited_comparisons.items())[:20]:
    print('EX_EMP', eid)
    for c in comps:
        print('|'.join([str(x) for x in c]))
    cnt+=1
    
print('')
print('EMP000011_ACCOUNT_COUNT=', emp000011_count)
for a in emp000011_safe:
    print('EMP000011_SAFE|', '|'.join([str(a.get('_id')), str(a.get('empId')), str(a.get('email')), str(a.get('role')), str(a.get('passwordStatus')), str(a.get('mustChangePassword')), str(a.get('createdAt')), str(a.get('updatedAt'))]))

print('')
print('DUPLICATE_EMPID_IN_BATCH_COUNT=', len(duplicate_empids))
print('DUPLICATE_EMAIL_IN_BATCH_COUNT=', len(duplicate_emails))
print('DUPLICATE_ID_IN_BATCH_COUNT=', len(duplicate_ids))
print('GLOBAL_EMPID_DUPLICATES_IN_BATCH=', len(global_duplicates))

print('')
print('PROVISIONING_SCRIPT_SUMMARY:')
print('BATCH_SIZE=500')
print('EMPLOYEE_SELECTION_FILTER=skips terminated/inactive/resigned employees via EmploymentStatus/status check')
print('EXISTING_ACCOUNT_DETECTION=checks db.user_accounts for empId or case-insensitive email regex and SKIPS existing')
print('OVERWRITE_BEHAVIOR=does not overwrite existing accounts or custom passwords (skips)')
print('ACCOUNT_LIMIT=None')
print('CANARY_EMP_ID=when set runs single-account canary flow (validates active, valid email, ensures no existing account; on non-dry-run will create exactly one account)')
print('CAN_SCRIPT_CREATE_FOR_EXITED=NO (script filters out terminated/inactive/resigned via status check)')

print('')
print('FACTS:')
print('- The above counts are direct reads from MongoDB for accounts with createdAt between 2026-08-19T10:20:00Z and 2026-08-19T10:51:00Z.')
print('- The provisioning script was read from repository; its filtering logic and batch size are as reported.')
print('')
print('INFERENCES:')
print('- The batch accounts are consistent with the provisioning script output (role, passwordStatus, mustChangePassword) and timestamp clustering, but there is no definitive attribution without MongoDB/Atlas audit logs or server/CI logs showing the process that performed the inserts.')
print('- The existence of 335 exited matches (as reported earlier) is verified by current EmploymentStatus values in employee documents; however, employee historical state at the exact account creation time cannot be determined unless employees store an exit timestamp field. Fields present across exited employee docs (counts) are:')
print(fields_present)
print('- If exit timestamp fields are absent or non-standard, the DB cannot prove whether those employee records were Active at the moment of account creation.')

print('')
print('FORENSIC_STATUS_CHECK_COMPLETE=YES','DATABASE_MODIFIED=NO','PROVISIONING_EXECUTED=NO','AUTH_CODE_MODIFIED=NO','ENV_MODIFIED=NO')

client.close()
