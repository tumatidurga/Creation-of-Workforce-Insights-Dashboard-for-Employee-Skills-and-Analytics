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

# time window per instruction: >= start and < end
start = datetime.fromisoformat('2026-08-19T10:20:00+00:00')
end = datetime.fromisoformat('2026-08-19T10:51:00+00:00')

# helper parse
from datetime import datetime as _dt

def parse_dt(v):
    if not v:
        return None
    if isinstance(v, _dt):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    s = str(v)
    try:
        dt = _dt.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        try:
            return _dt.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        except Exception:
            try:
                return _dt.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            except Exception:
                return None

# read-only counts
total_user_accounts = db.user_accounts.count_documents({})
total_employees = db.employees.count_documents({})

# load employees mapping
employees = list(db.employees.find({}, {'EmpID':1,'Email':1,'EmploymentStatus':1,'ExitDate':1,'Exit_Date':1}))
emp_by_id = { e.get('EmpID'): e for e in employees if e.get('EmpID') }
emp_email_map = { (e.get('Email') or '').lower(): e for e in employees if e.get('Email') }

# fetch all accounts and filter batch by createdAt range (>=start and <end)
accounts = list(db.user_accounts.find({}, {'_id':1,'empId':1,'email':1,'role':1,'passwordStatus':1,'mustChangePassword':1,'createdAt':1,'updatedAt':1}))

batch = []
for a in accounts:
    ca = parse_dt(a.get('createdAt'))
    if not ca:
        continue
    if ca >= start and ca < end:
        a['_created_dt'] = ca
        batch.append(a)

batch_size = len(batch)

# matching
matched_by_empid = 0
matched_by_email_only = 0
no_match = 0
status_counts = {'Active':0,'Exited':0,'Other':0,'Orphan':0}
empids_in_batch = []
for a in batch:
    empId = a.get('empId')
    email = (a.get('email') or '').lower()
    if empId and empId in emp_by_id:
        matched_by_empid += 1
        empids_in_batch.append(empId)
        status = (emp_by_id[empId].get('EmploymentStatus') or '')
        if status.strip().lower()=='active':
            status_counts['Active'] += 1
        elif status.strip().lower()=='exited':
            status_counts['Exited'] += 1
        else:
            status_counts['Other'] += 1
    elif email and email in emp_email_map:
        matched_by_email_only += 1
        status = (emp_email_map[email].get('EmploymentStatus') or '')
        if status.strip().lower()=='active':
            status_counts['Active'] += 1
        elif status.strip().lower()=='exited':
            status_counts['Exited'] += 1
        else:
            status_counts['Other'] += 1
    else:
        no_match += 1
        status_counts['Orphan'] += 1

# duplicates in batch
from collections import Counter
empid_counts = Counter([a.get('empId') for a in batch if a.get('empId')])
duplicate_empids = sum(1 for v in empid_counts.values() if v>1)
email_counts = Counter([(a.get('email') or '').lower() for a in batch if a.get('email')])
duplicate_emails = sum(1 for v in email_counts.values() if v>1)
id_counts = Counter([str(a.get('_id')) for a in batch])
duplicate_ids = sum(1 for v in id_counts.values() if v>1)

# EMP000011 doc
emp011_docs = list(db.user_accounts.find({'empId':'EMP000011'},{'_id':1,'empId':1,'email':1,'role':1,'passwordStatus':1,'mustChangePassword':1,'createdAt':1,'updatedAt':1}))
emp011_count = len(emp011_docs)
emp011_safe = []
for d in emp011_docs:
    row = {k: d.get(k) for k in ['_id','empId','email','role','passwordStatus','mustChangePassword','createdAt','updatedAt']}
    emp011_safe.append(row)

# exited employee evidence: employees in batch with EmploymentStatus exactly 'Exited'
exited_empids = [eid for eid in empids_in_batch if eid in emp_by_id and (emp_by_id[eid].get('EmploymentStatus')=='Exited')]
exited_empids = sorted(set(exited_empids))
exited_count = len(exited_empids)
# verify exitdate presence and earlier than account createdAt
exitdate_missing = 0
exitdate_unparseable = 0
exitdate_before = 0
exitdate_same_day = 0
exitdate_after = 0
for eid in exited_empids:
    emp = emp_by_id.get(eid)
    exit_val = emp.get('ExitDate') or emp.get('Exit_Date')
    if not exit_val:
        exitdate_missing +=1
        continue
    # normalize exit date parse
    parsed_exit = None
    try:
        parsed_exit = _dt.fromisoformat(str(exit_val))
        if parsed_exit.tzinfo is None:
            parsed_exit = parsed_exit.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            parsed_exit = _dt.strptime(str(exit_val),'%Y-%m-%d').replace(tzinfo=timezone.utc)
        except Exception:
            parsed_exit = None
    if not parsed_exit:
        exitdate_unparseable +=1
        continue
    # find account createdAt for this emp in batch
    acct = next((a for a in batch if a.get('empId')==eid), None)
    if not acct:
        continue
    acct_dt = acct.get('_created_dt')
    if parsed_exit.date() < acct_dt.date():
        exitdate_before +=1
    elif parsed_exit.date() == acct_dt.date():
        exitdate_same_day +=1
    elif parsed_exit.date() > acct_dt.date():
        exitdate_after +=1

# Compose verification results
print('VERIFICATION_RESULTS')
print('TOTAL_EMPLOYEES=', total_employees)
print('TOTAL_USER_ACCOUNTS=', total_user_accounts)
print('SUSPICIOUS_BATCH_CRITERIA=createdAt >= 2026-08-19T10:20:00Z and createdAt < 2026-08-19T10:51:00Z')
print('BATCH_SIZE=', batch_size)
print('BATCH_MATCHED_BY_EMPID=', matched_by_empid)
print('BATCH_MATCHED_BY_EMAIL_ONLY=', matched_by_email_only)
print('BATCH_NO_EMPLOYEE_MATCH=', no_match)
print('BATCH_STATUS_COUNTS_ACTIVE=', status_counts['Active'])
print('BATCH_STATUS_COUNTS_EXITED=', status_counts['Exited'])
print('BATCH_STATUS_COUNTS_OTHER=', status_counts['Other'])
print('BATCH_STATUS_COUNTS_ORPHAN=', status_counts['Orphan'])
print('DUPLICATE_EMPID_IN_BATCH=', duplicate_empids)
print('DUPLICATE_EMAIL_IN_BATCH=', duplicate_emails)
print('DUPLICATE_ID_IN_BATCH=', duplicate_ids)
print('EMP000011_ACCOUNT_COUNT=', emp011_count)
for r in emp011_safe:
    print('EMP000011_SAFE|', '|'.join([str(r.get('_id')), str(r.get('empId')), str(r.get('email')), str(r.get('role')), str(r.get('passwordStatus')), str(r.get('mustChangePassword')), str(r.get('createdAt')), str(r.get('updatedAt'))]))
print('')
print('EXITED_EMPLOYEES_IN_BATCH_COUNT=', exited_count)
print('EXITED_EXITDATE_VALUES_PRESENT=', exited_count - exitdate_missing - exitdate_unparseable)
print('EXITED_EXITDATE_MISSING=', exitdate_missing)
print('EXITED_EXITDATE_UNPARSEABLE=', exitdate_unparseable)
print('EXITED_EXITDATE_BEFORE_ACCOUNT=', exitdate_before)
print('EXITED_EXITDATE_SAME_DAY=', exitdate_same_day)
print('EXITED_EXITDATE_AFTER_ACCOUNT=', exitdate_after)

# provisioning script facts (read code)
print('PROVISIONING_SCRIPT_EVIDENCE')
print('SCRIPT_PATH=backend/scripts/provision_employee_accounts.py')
print('BATCH_SIZE=500')
print('EXISTING_ACCOUNTS_SKIPPED=YES')
print('ACCOUNT_LIMIT=None')
print('CANARY_ACTIVE_ONLY_CHECK=_is_active_employee requires status=="active"')
print('MASS_FILTER_EXCLUDES=terminated,inactive,resigned (lowercased)')
print('MASS_FILTER_DOES_NOT_EXCLUDE=Exited (not in exclusion list)')

print('\nATTRIBUTION_STATUS')
print('Attribution is NOT PROVEN from the current repository/database evidence.')
print('Atlas audit logs or server/CI/host logs are required to identify authenticated DB user, client IP, application name, driver, and exact INSERT operations.')

# Atlas admin request template
print('\nATLAS_ADMIN_REQUEST')
print('Please query MongoDB Atlas audit logs for INSERT operations on workforce_db.user_accounts for the time window 2026-08-19T10:20:00Z through 2026-08-19T10:51:00Z. Return only safe metadata: timestamp, authenticated principal, client IP, application name, driver/client info, namespace, operation type, insert/insertMany command info, and any session/correlation ids.')
print('Cluster: workforcecluster.c9wibir.mongodb.net')
print('Database: workforce_db')
print('Collection: user_accounts')
print('Time window: 2026-08-19T10:20:00Z -> 2026-08-19T10:51:00Z')
print('Fields requested: timestamp, authenticated user/principal, client IP, application name, driver/client, namespace, operation type, command text, session/correlation id (if available).')
print('\nSAFE_NEXT_ACTION: Do not run mass provisioning until Atlas/server audit evidence has been reviewed and the cause of the 3,001-account batch has been established. Do not delete or modify the 3,001 accounts or run provisioning scripts.')

print('\nFINAL_STATUS')
print('EVIDENCE_PRESERVATION_COMPLETE=YES')
print('DATABASE_MODIFIED=NO')
print('PROVISIONING_EXECUTED=NO')
print('CODE_MODIFIED=NO')
print('ENV_MODIFIED=NO')
print('ATTRIBUTION_PROVEN=NO')

client.close()
