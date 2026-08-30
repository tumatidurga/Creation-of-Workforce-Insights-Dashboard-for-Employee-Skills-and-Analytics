from pymongo import MongoClient
import os
import bcrypt

MONGO = os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017')
DB = os.environ.get('DATABASE_NAME','workforce_db_test')
HR_PW = os.environ.get('HR_ADMIN_TEST_PASSWORD','hr-bootstrap-test')
EMP_PW = os.environ.get('EMPLOYEE_TEST_PASSWORD','EMP000001')

client = MongoClient(MONGO, serverSelectionTimeoutMS=5000)
db = client[DB]

hr_hash = bcrypt.hashpw(HR_PW.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
emp_hash = bcrypt.hashpw(EMP_PW.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

res1 = db.user_accounts.update_one({'userId':'hr-admin'}, {'$set':{'passwordHash':hr_hash,'status':'ACTIVE'}})
res2 = db.user_accounts.update_one({'userId':'employee-self-service'}, {'$set':{'passwordHash':emp_hash,'status':'ACTIVE','empId':'EMP000001'}})

print('UPDATED HR:', res1.matched_count)
print('UPDATED EMP:', res2.matched_count)
