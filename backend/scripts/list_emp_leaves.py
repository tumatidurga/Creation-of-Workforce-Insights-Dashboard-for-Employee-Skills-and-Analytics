from pymongo import MongoClient
import os
client=MongoClient(os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017'))
db=client[os.environ.get('DATABASE_NAME','workforce_db_test')]
for l in db.leaves.find({'EmpID':'EMP000001'},{'_id':0,'StartDate':1,'EndDate':1,'Status':1}):
    print(l)
