from pymongo import MongoClient
import os

url = os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017')
db_name = os.environ.get('DATABASE_NAME','workforce_db_test')
client = MongoClient(url, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[db_name]

seen = set()
removed = 0
for doc in db.leaves.find({}, {'_id':1,'EmpID':1,'StartDate':1,'EndDate':1}):
    key = (doc.get('EmpID'), doc.get('StartDate'), doc.get('EndDate'))
    if key in seen:
        db.leaves.delete_one({'_id': doc['_id']})
        removed += 1
    else:
        seen.add(key)

print('DEDUPED_REMOVED=', removed)
