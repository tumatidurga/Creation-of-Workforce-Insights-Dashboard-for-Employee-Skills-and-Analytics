"""
Enhanced dry-run of migrate_user_profiles.py: analyze which profiles would be created without writing to DB.
DO NOT MODIFY DB.
"""
import sys
import itertools
import json
from datetime import datetime
from backend.app.config import settings
from pymongo import MongoClient

url = settings.MONGODB_URL
if not url:
    print('MONGO_READ_FAILED: No MONGODB_URL configured')
    sys.exit(2)

client = MongoClient(url, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[settings.DATABASE_NAME]

# Basic counts
total_accounts = db.user_accounts.count_documents({})
accounts_with_userId = db.user_accounts.count_documents({"userId": {"$exists": True, "$nin": [None, ""]}})
accounts_with_empId = db.user_accounts.count_documents({"empId": {"$exists": True, "$ne": None}})
accounts_without_empId = total_accounts - accounts_with_empId

# Duplicate userId groups
dup_userid_pipeline = [
    {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
    {"$match": {"_id": {"$ne": None, "$ne": ""}, "count": {"$gt": 1}}},
    {"$count": "dup_count"}
]
dup_userid_res = list(db.user_accounts.aggregate(dup_userid_pipeline))
duplicate_userid_count = dup_userid_res[0]['dup_count'] if dup_userid_res else 0

# Duplicate emails
dup_email_pipeline = [
    {"$group": {"_id": "$email", "count": {"$sum": 1}}},
    {"$match": {"_id": {"$ne": None, "$ne": ""}, "count": {"$gt": 1}}},
    {"$count": "dup_count"}
]
dup_email_res = list(db.user_accounts.aggregate(dup_email_pipeline))
duplicate_email_count = dup_email_res[0]['dup_count'] if dup_email_res else 0

# CURRENT_USER count in profiles
current_user_profiles = db.user_profiles.count_documents({"userId": "CURRENT_USER"})

# Existing per-user profiles
existing_profiles = db.user_profiles.count_documents({"userId": {"$exists": True, "$nin": [None, ""]}})

# Accounts that would produce profiles: accounts with userId and without existing profile
# We'll iterate accounts with a projection limited to safe fields
projection = {"userId": 1, "empId": 1, "role": 1}
accounts_cursor = db.user_accounts.find({}, projection)

scanned = 0
would_create = 0
already_existing = 0
employees_matched = 0
employee_mismatches = 0
hr_profiles = 0
invalid_accounts = 0
errors = 0
invalid_avatar_count = 0

# Collect small samples
sample_accounts = []
sample_hr = None

for acct in accounts_cursor:
    scanned += 1
    try:
        user_id = acct.get('userId')
        if not user_id:
            invalid_accounts += 1
            continue
        # check existing profile
        if db.user_profiles.find_one({'userId': user_id}, {'_id': 0}):
            already_existing += 1
            continue
        # would create
        would_create += 1
        emp_id = acct.get('empId')
        if emp_id:
            emp = db.employees.find_one({'EmpID': emp_id}, {'_id': 0, 'Department': 1, 'EmployeeName': 1, 'avatar': 1})
            if emp:
                employees_matched += 1
                avatar_present = bool(isinstance(emp.get('avatar'), str) and emp.get('avatar').strip() and emp.get('avatar').strip().lower().startswith(('http://', 'https://')))
                if not avatar_present and emp.get('avatar'):
                    invalid_avatar_count += 1
                if len(sample_accounts) < 5:
                    sample_accounts.append({
                        'userId': user_id,
                        'empId': emp_id,
                        'role': acct.get('role'),
                        'department': emp.get('Department'),
                        'avatar_present': avatar_present,
                    })
            else:
                employee_mismatches += 1
                if len(sample_accounts) < 5:
                    sample_accounts.append({
                        'userId': user_id,
                        'empId': emp_id,
                        'role': acct.get('role'),
                        'department': None,
                        'avatar_present': False,
                    })
        else:
            hr_profiles += 1
            if not sample_hr and acct.get('role') == 'HR_ADMIN':
                sample_hr = {'userId': user_id, 'empId': None, 'role': acct.get('role'), 'department': None, 'avatar_present': False}
    except Exception:
        errors += 1

print('Migration dry-run summary')
print('Timestamp:', datetime.utcnow().isoformat())
print('Total user_accounts:', total_accounts)
print('Accounts with userId:', accounts_with_userId)
print('Accounts with empId:', accounts_with_empId)
print('Accounts without empId:', accounts_without_empId)
print('Duplicate userId groups:', duplicate_userid_count)
print('Duplicate email groups:', duplicate_email_count)
print('Existing per-user profiles:', existing_profiles)
print('Accounts scanned (iteration):', scanned)
print('Profiles that would be created:', would_create)
print('Employees matched:', employees_matched)
print('Employee mismatches (empId present but no employee):', employee_mismatches)
print('HR_ADMIN accounts (would create profiles):', hr_profiles)
print('Invalid accounts (missing userId):', invalid_accounts)
print('Accounts with invalid avatar values on employee records:', invalid_avatar_count)
print('CURRENT_USER profiles count:', current_user_profiles)
print('Errors during dry-run:', errors)

print('\nSample planned profile records (up to 5):')
print(json.dumps(sample_accounts, indent=2))
if sample_hr:
    print('\nSample HR planned profile:')
    print(json.dumps(sample_hr, indent=2))

# close client
client.close()
