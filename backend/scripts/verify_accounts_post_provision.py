from pymongo import MongoClient
import os
import bcrypt

url = os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017')
db_name = os.environ.get('DATABASE_NAME','workforce_db_test')
client = MongoClient(url, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[db_name]

ua_total = db.user_accounts.count_documents({})
ua_default = db.user_accounts.count_documents({'passwordStatus':'default'})
ua_custom = db.user_accounts.count_documents({'passwordStatus':'custom'})
ua_missing_hash = db.user_accounts.count_documents({'$or':[{'passwordHash':{'$exists':False}},{'passwordHash':None},{'passwordHash':''}]})
ua_missing_empid = db.user_accounts.count_documents({'$or':[{'empId':{'$exists':False}},{'empId':None},{'empId':''}]})

print('USER_ACCOUNTS_TOTAL=', ua_total)
print('ACCOUNTS_WITH_DEFAULT_PASSWORD_STATUS=', ua_default)
print('ACCOUNTS_WITH_CUSTOM_PASSWORD_STATUS=', ua_custom)
print('ACCOUNTS_WITHOUT_PASSWORD_HASH=', ua_missing_hash)
print('ACCOUNTS_WITHOUT_EMPID=', ua_missing_empid)

# Verify mapping between employees and accounts
employees = list(db.employees.find({}, {'_id':0,'EmpID':1,'Email':1}))
emp_count = len(employees)
mapped = 0
for emp in employees:
    empid = emp.get('EmpID') or emp.get('empId')
    acc = db.user_accounts.find_one({'empId': empid})
    if acc:
        mapped += 1
print('TOTAL_EMPLOYEES=', emp_count)
print('EMPLOYEES_WITH_ACCOUNTS=', mapped)

# bcrypt check for accounts with default passwordStatus
for acc in db.user_accounts.find({'passwordStatus':'default'}, {'userId':1,'empId':1,'passwordHash':1}):
    empid = acc.get('empId')
    ph = acc.get('passwordHash') or ''
    ok = False
    try:
        ok = bcrypt.checkpw(empid.encode('utf-8'), ph.encode('utf-8'))
    except Exception:
        ok = False
    print('CHECK_DEFAULT_PASSWORD for', acc.get('userId'), 'empId=', empid, 'bcrypt_matches_empid=', ok)
