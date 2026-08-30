from pymongo import MongoClient
import os
client=MongoClient(os.environ.get('MONGODB_URL','mongodb://127.0.0.1:27017'))
db=client[os.environ.get('DATABASE_NAME','workforce_db_test')]
res=db.notifications.delete_many({})
print('deleted notifications:', res.deleted_count)
