from pymongo import MongoClient
import bcrypt
import os
url=os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017')
db_name=os.environ.get('DATABASE_NAME','workforce_db_test')
client=MongoClient(url)
db=client[db_name]
doc=db.user_accounts.find_one({'empId':'EMP000002'})
ph=doc.get('passwordHash')
print('ph_len', len(ph) if ph else 0)
print('bcrypt_check:', bcrypt.checkpw('EMP000002'.encode('utf-8'), ph.encode('utf-8')) if ph else False)
