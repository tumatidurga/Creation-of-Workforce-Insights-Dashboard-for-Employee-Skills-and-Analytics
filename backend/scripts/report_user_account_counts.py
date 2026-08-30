from pymongo import MongoClient
import os
client=MongoClient(os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017'))
db=client[os.environ.get('DATABASE_NAME','workforce_db_test')]
# counts
total_employees = db.employees.count_documents({})
user_accounts = db.user_accounts.count_documents({})
accounts_with_default = db.user_accounts.count_documents({'passwordStatus':'default'})
accounts_with_custom = db.user_accounts.count_documents({'passwordStatus':'custom'})
accounts_without_password_hash = db.user_accounts.count_documents({'passwordHash': {'$exists': False}})
accounts_without_empid = db.user_accounts.count_documents({'empId': {'$exists': False}})
print('TOTAL_EMPLOYEES', total_employees)
print('USER_ACCOUNTS_TOTAL', user_accounts)
print('ACCOUNTS_WITH_DEFAULT_PASSWORD_STATUS', accounts_with_default)
print('ACCOUNTS_WITH_CUSTOM_PASSWORD_STATUS', accounts_with_custom)
print('ACCOUNTS_WITHOUT_PASSWORD_HASH', accounts_without_password_hash)
print('ACCOUNTS_WITHOUT_EMPID', accounts_without_empid)
