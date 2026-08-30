from pymongo import MongoClient
import os
client=MongoClient(os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017'))
db=client[os.environ.get('DATABASE_NAME','workforce_db_test')]
criteria = [
    {'EmpID':'EMP000001','StartDate':'2041-04-10','EndDate':'2041-04-12'},
    {'EmpID':'EMP000001','StartDate':'2041-08-01','EndDate':'2041-08-04'},
    {'EmpID':'EMP000001','StartDate':'2041-10-01','EndDate':'2041-10-02'},
]
for c in criteria:
    res = db.leaves.delete_many(c)
    print('deleted', res.deleted_count, 'for', c)
