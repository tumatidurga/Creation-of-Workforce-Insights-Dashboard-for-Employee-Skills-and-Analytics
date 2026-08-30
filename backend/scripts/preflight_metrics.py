"""
Compute preflight metrics for migration in a read-only efficient manner.
Prints the requested metrics and a small safe sample.
"""
from backend.app.config import settings
from pymongo import MongoClient
import json

client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[settings.DATABASE_NAME]

# Totals
total_accounts = db.user_accounts.count_documents({})
accounts_with_userId = db.user_accounts.count_documents({"userId": {"$exists": True, "$nin": [None, ""]}})
accounts_missing_userId = total_accounts - accounts_with_userId
accounts_with_empId = db.user_accounts.count_documents({"empId": {"$exists": True, "$ne": None}})
accounts_without_empId = total_accounts - accounts_with_empId

# Roles
employee_accounts = db.user_accounts.count_documents({"role": "EMPLOYEE"})
hr_accounts = db.user_accounts.count_documents({"role": "HR_ADMIN"})

# Existing per-user profiles
existing_profiles = db.user_profiles.count_documents({"userId": {"$exists": True, "$nin": [None, ""]}})

# Profiles that would be created: accounts with userId and no corresponding user_profiles.userId
pipeline_missing_profiles = [
    {"$match": {"userId": {"$exists": True, "$nin": [None, ""]}}},
    {"$lookup": {"from": "user_profiles", "localField": "userId", "foreignField": "userId", "as": "profile"}},
    {"$match": {"profile": {"$size": 0}}},
    {"$count": "to_create"}
]
res = list(db.user_accounts.aggregate(pipeline_missing_profiles))
profiles_to_create = res[0]["to_create"] if res else 0

# Profiles skipped (invalid accounts)
profiles_skipped = accounts_missing_userId

# Employees matched and not matched among accounts with empId and no existing profile
pipeline_emp_matches = [
    {"$match": {"userId": {"$exists": True, "$nin": [None, ""]}, "empId": {"$exists": True, "$ne": None}}},
    {"$lookup": {"from": "user_profiles", "localField": "userId", "foreignField": "userId", "as": "profile"}},
    {"$match": {"profile": {"$size": 0}}},
    {"$project": {"empId": 1}},
]
emp_cursor = db.user_accounts.aggregate(pipeline_emp_matches)
emp_matches = 0
emp_not_matches = 0
invalid_avatar_count = 0
sample_accounts = []
count_checked = 0
for acct in emp_cursor:
    emp_id = acct.get('empId')
    emp = db.employees.find_one({'EmpID': emp_id}, {'_id': 0, 'Department': 1, 'EmployeeName': 1, 'avatar': 1})
    if emp:
        emp_matches += 1
        avatar_present = isinstance(emp.get('avatar'), str) and emp.get('avatar').strip() and emp.get('avatar').strip().lower().startswith(('http://', 'https://'))
        if not avatar_present and emp.get('avatar'):
            invalid_avatar_count += 1
        if len(sample_accounts) < 5:
            sample_accounts.append({
                'userId': acct.get('userId'),
                'empId': emp_id,
                'role': 'EMPLOYEE',
                'department': emp.get('Department'),
                'avatar_present': avatar_present
            })
    else:
        emp_not_matches += 1

# HR sample
sample_hr = None
hr_cursor = db.user_accounts.find({'role': 'HR_ADMIN'}, {'userId':1,'empId':1,'role':1}).limit(1)
for h in hr_cursor:
    sample_hr = {'userId': h.get('userId'), 'empId': h.get('empId'), 'role': h.get('role'), 'department': None, 'avatar_present': False}

# Duplicate counts
dup_userid_pipeline = [
    {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
    {"$match": {"_id": {"$ne": None, "$ne": ""}, "count": {"$gt": 1}}},
    {"$count": "dup_count"}
]
dup_userid_res = list(db.user_accounts.aggregate(dup_userid_pipeline))
duplicate_userid_groups = dup_userid_res[0]['dup_count'] if dup_userid_res else 0

dup_email_pipeline = [
    {"$group": {"_id": "$email", "count": {"$sum": 1}}},
    {"$match": {"_id": {"$ne": None, "$ne": ""}, "count": {"$gt": 1}}},
    {"$count": "dup_count"}
]
dup_email_res = list(db.user_accounts.aggregate(dup_email_pipeline))
duplicate_email_groups = dup_email_res[0]['dup_count'] if dup_email_res else 0

# CURRENT_USER count
current_user_count = db.user_profiles.count_documents({'userId':'CURRENT_USER'})

# Errors - none for read-only
errors = 0

# Print the exact requested values
print('Accounts scanned:', total_accounts)
print('Accounts with valid userId:', accounts_with_userId)
print('Accounts with missing userId:', accounts_missing_userId)
print('Accounts with empId:', accounts_with_empId)
print('Accounts without empId:', accounts_without_empId)
print('EMPLOYEE accounts:', employee_accounts)
print('HR_ADMIN accounts:', hr_accounts)
print('Existing per-user profiles:', existing_profiles)
print('Profiles that would be created:', profiles_to_create)
print('Profiles skipped:', profiles_skipped)
print('Employees matched:', emp_matches)
print('Employees not matched:', emp_not_matches)
print('Invalid avatar values:', invalid_avatar_count)
print('Duplicate userId groups:', duplicate_userid_groups)
print('Duplicate email groups:', duplicate_email_groups)
print('CURRENT_USER count:', current_user_count)
print('Errors:', errors)

# Safe samples
print('\nSample employee records (up to 5):')
print(json.dumps(sample_accounts, indent=2))
print('\nSample HR record (up to 1):')
print(json.dumps(sample_hr, indent=2))

client.close()
