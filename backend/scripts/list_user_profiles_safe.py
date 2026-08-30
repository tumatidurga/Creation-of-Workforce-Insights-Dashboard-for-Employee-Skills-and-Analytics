"""
List existing user_profiles documents with only safe fields (userId, empId, role).
Read-only helper for migration preflight.
"""
from backend.app.config import settings
from pymongo import MongoClient
import json

client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[settings.DATABASE_NAME]

rows = []
for doc in db.user_profiles.find({}, {'_id':0, 'userId':1, 'empId':1, 'role':1}):
    rows.append(doc)

print(json.dumps(rows, indent=2))
client.close()
