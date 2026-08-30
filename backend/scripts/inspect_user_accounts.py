from pymongo import MongoClient
import os
url = os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017')
db_name = os.environ.get('DATABASE_NAME','workforce_db_test')
client = MongoClient(url, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[db_name]
for doc in db.user_accounts.find({}, {'_id':0,'userId':1,'empId':1,'email':1,'role':1,'passwordStatus':1,'status':1}):
    print(doc)
