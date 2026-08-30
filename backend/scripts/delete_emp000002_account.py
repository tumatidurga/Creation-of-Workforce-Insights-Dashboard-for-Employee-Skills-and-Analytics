from pymongo import MongoClient
import os
client=MongoClient(os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017'))
db=client[os.environ.get('DATABASE_NAME','workforce_db_test')]
res=db.user_accounts.delete_many({'empId':'EMP000002'})
print('deleted_empId', res.deleted_count)
res2=db.user_accounts.delete_many({'userId':'EMP000002'})
print('deleted_userId', res2.deleted_count)
