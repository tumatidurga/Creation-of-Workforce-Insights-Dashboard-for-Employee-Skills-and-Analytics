"""
Read-only queries for HR account and EMP010000 verification.
Prints JSON-safe lines for each result.
"""
from backend.app.config import settings
from pymongo import MongoClient
import json

client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[settings.DATABASE_NAME]

# Query for Priya Sharma
hr = db.user_accounts.find_one({'email': 'priya.sharma@enterprise.com'}, {'_id': 0, 'userId':1, 'empId':1, 'role':1, 'name':1, 'email':1, 'status':1})
print('HR_ACCOUNT:')
print(json.dumps(hr, indent=2))

# Check whether per-user profile exists for hr-admin
hr_profile_exists = bool(db.user_profiles.find_one({'userId': 'hr-admin'}, {'_id':0}))
print('HR_PROFILE_EXISTS:', hr_profile_exists)

# EMP010000 user account and profile info
acct = db.user_accounts.find_one({'userId': 'EMP010000'}, {'_id':0, 'userId':1, 'empId':1, 'role':1})
profile = db.user_profiles.find_one({'userId': 'EMP010000'}, {'_id':0, 'userId':1, 'empId':1, 'role':1, 'department':1, 'avatar':1})

print('EMP010000_ACCOUNT:')
print(json.dumps(acct, indent=2))
print('EMP010000_PROFILE:')
if profile:
    avatar_present = isinstance(profile.get('avatar'), str) and profile.get('avatar').strip().lower().startswith(('http://','https://'))
    safe_profile = {
        'userId': profile.get('userId'),
        'empId': profile.get('empId'),
        'role': profile.get('role'),
        'department': profile.get('department'),
        'avatar_present': avatar_present
    }
    print(json.dumps(safe_profile, indent=2))
else:
    print('null')

client.close()
