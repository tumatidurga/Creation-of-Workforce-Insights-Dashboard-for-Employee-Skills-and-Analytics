"""
Compute dry-run migration stats: how many user_accounts have empId matching employees.
"""
from backend.app.config import settings
from pymongo import MongoClient

client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
db = client[settings.DATABASE_NAME]

pipeline = [
    {"$match": {"empId": {"$exists": True, "$ne": None, "$ne": ""}}},
    {"$lookup": {"from": "employees", "localField": "empId", "foreignField": "EmpID", "as": "emp"}},
    {"$match": {"emp.0": {"$exists": True}}},
    {"$count": "matched"}
]
res = list(db.user_accounts.aggregate(pipeline))
print('employees_matched:', res[0]['matched'] if res else 0)

# count of accounts with empId null
count_empid_null = db.user_accounts.count_documents({'$or':[{'empId': None}, {'empId': {'$exists': False}}]})
print('accounts_empId_null:', count_empid_null)
