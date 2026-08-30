from pymongo import MongoClient
import os

url = os.environ.get('MONGODB_URL', 'mongodb://127.0.0.1:27017')
db_name = os.environ.get('DATABASE_NAME', 'workforce_db_test')

client = MongoClient(url, serverSelectionTimeoutMS=5000)
try:
    client.admin.command('ping')
except Exception as e:
    print('MONGO_CONNECTION_ERROR', e)
    raise SystemExit(1)

db = client[db_name]

emp_count = db.employees.count_documents({})
# distinct empids try both cases
distinct_empids = db.employees.distinct('EmpID')
if not distinct_empids:
    distinct_empids = db.employees.distinct('empId')
unique_empids = len([e for e in distinct_empids if e])
missing_empids = db.employees.count_documents({'$or':[{'EmpID':{'$exists':False}},{'EmpID':None},{'EmpID':''}]})

# emails
distinct_emails = db.employees.distinct('Email')
if not distinct_emails:
    distinct_emails = db.employees.distinct('email')
unique_emails = len([e for e in distinct_emails if e])
missing_emails = db.employees.count_documents({'$or':[{'Email':{'$exists':False}},{'Email':None},{'Email':''}]})

# duplicates
duplicate_empids = max(0, emp_count - unique_empids)
emails = [e.lower() for e in distinct_emails if e]
duplicate_emails = max(0, len(emails) - len(set(emails)))

user_accounts_count = db.user_accounts.count_documents({})

active_count = db.employees.count_documents({'$or':[{'EmploymentStatus':{'$regex':'^(active|Active|ACTIVE)'}},{'status':{'$regex':'^(active|Active|ACTIVE)'}}]})
inactive_count = db.employees.count_documents({'$or':[{'EmploymentStatus':{'$regex':'(terminated|inactive|resigned)', '$options':'i'}},{'status':{'$regex':'(terminated|inactive|resigned)', '$options':'i'}}]})

print('EMP_COLLECTION_NAME=employees')
print('TOTAL_EMPLOYEES=', emp_count)
print('UNIQUE_EMPIDS=', unique_empids)
print('DUPLICATE_EMPIDS=', duplicate_empids)
print('MISSING_EMPIDS=', missing_empids)
print('UNIQUE_EMAILS=', unique_emails)
print('DUPLICATE_EMAILS=', duplicate_emails)
print('MISSING_EMAILS=', missing_emails)
print('USER_ACCOUNTS_COUNT=', user_accounts_count)
print('ACTIVE_EMPLOYEES=', active_count)
print('INACTIVE_EMPLOYEES=', inactive_count)
