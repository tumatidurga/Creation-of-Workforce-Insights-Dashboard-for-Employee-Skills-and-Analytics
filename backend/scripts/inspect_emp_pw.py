from pymongo import MongoClient
import os
url=os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017')
db_name=os.environ.get('DATABASE_NAME','workforce_db_test')
client=MongoClient(url)
db=client[db_name]
for doc in db.user_accounts.find({'empId': 'EMP000002'}, {'_id':1,'empId':1,'passwordHash':1,'passwordStatus':1}):
    print('id:',str(doc.get('_id')))
    ph = doc.get('passwordHash')
    print('has_passwordHash:', ph is not None)
    if ph:
        print('hash_len:', len(ph))
    print('passwordStatus:', doc.get('passwordStatus'))
