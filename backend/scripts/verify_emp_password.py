from pymongo import MongoClient
import os
import bcrypt
client=MongoClient(os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017'))
db=client[os.environ.get('DATABASE_NAME','workforce_db_test')]
emp = db.user_accounts.find_one({'empId':'EMP000001'})
print('emp exists', emp is not None)
print('passwordStatus', emp.get('passwordStatus'))
print('bcrypt_check old(empid):', bcrypt.checkpw('EMP000001'.encode('utf-8'), emp.get('passwordHash').encode('utf-8')))
print('bcrypt_check new(custom):', bcrypt.checkpw('my-custom-secret-!'.encode('utf-8'), emp.get('passwordHash').encode('utf-8')))
