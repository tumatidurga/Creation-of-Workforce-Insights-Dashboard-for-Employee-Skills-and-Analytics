"""
Read-only MongoDB audit script used for dry-run verification.
DO NOT MODIFY DATABASE. This script only reads counts and detects basic duplicates.
"""
import traceback
from backend.app.config import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import sys

url = settings.MONGODB_URL
if not url:
    print('MONGO_READ_FAILED: No MONGODB_URL configured in settings')
    sys.exit(2)

db_name = settings.DATABASE_NAME
print('Attempting read-only MongoDB connection...')
try:
    client = MongoClient(url, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[db_name]
    res = {}
    # counts
    res['user_accounts_count'] = db.user_accounts.count_documents({})
    res['user_profiles_count'] = db.user_profiles.count_documents({})
    res['employees_count'] = db.employees.count_documents({})

    # user_accounts metadata
    res['ua_userId_present'] = db.user_accounts.count_documents({'userId': {'$exists': True, '$ne': None, '$ne': ''}})
    res['ua_empId_present'] = db.user_accounts.count_documents({'empId': {'$exists': True, '$ne': None, '$ne': ''}})
    res['ua_empId_null'] = db.user_accounts.count_documents({'$or': [{'empId': None}, {'empId': {'$exists': False}}]})
    res['ua_role_employee'] = db.user_accounts.count_documents({'role': 'EMPLOYEE'})
    res['ua_role_hr'] = db.user_accounts.count_documents({'role': 'HR_ADMIN'})

    # user_profiles metadata
    res['up_current_user'] = db.user_profiles.count_documents({'userId': 'CURRENT_USER'})
    res['up_userid_not_current'] = db.user_profiles.count_documents({'userId': {'$ne': 'CURRENT_USER', '$exists': True}})
    res['up_missing_userId'] = db.user_profiles.count_documents({'userId': {'$exists': False}})

    # matches between user_accounts and user_profiles
    ua_userids = db.user_accounts.distinct('userId')
    up_userids = db.user_profiles.distinct('userId')
    ua_userids_set = set([u for u in ua_userids if u])
    up_userids_set = set([u for u in up_userids if u])
    res['accounts_with_matching_profiles'] = len(ua_userids_set & up_userids_set)
    res['accounts_without_profiles'] = max(0, len(ua_userids_set - up_userids_set))

    # duplicates detection helper
    def duplicates(collection, field):
        pipeline = [
            {'$group': {'_id': f'${field}', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}},
            {'$limit': 10}
        ]
        docs = list(db[collection].aggregate(pipeline))
        return len(docs), docs[:5]

    dup_uid_count, dup_uid_examples = duplicates('user_accounts', 'userId')
    dup_email_count, dup_email_examples = duplicates('user_accounts', 'email')
    dup_empid_count, dup_empid_examples = duplicates('employees', 'EmpID')
    dup_up_userid_count, dup_up_userid_examples = duplicates('user_profiles', 'userId')

    res['duplicates'] = {
        'user_accounts.userId.dups': dup_uid_count,
        'user_accounts.email.dups': dup_email_count,
        'employees.EmpID.dups': dup_empid_count,
        'user_profiles.userId.dups': dup_up_userid_count,
    }

    print('MONGO_READ_OK')
    for k, v in res.items():
        print(f"{k}: {v}")
    # Print small duplicate summaries (do not include sensitive data)
    print('dup_examples_user_accounts_userId_count:', dup_uid_count)
    print('dup_examples_user_accounts_email_count:', dup_email_count)
    print('dup_examples_employees_EmpID_count:', dup_empid_count)
    print('dup_examples_user_profiles_userId_count:', dup_up_userid_count)

except PyMongoError as e:
    print('MONGO_READ_FAILED')
    print(str(e))
    traceback.print_exc()
    sys.exit(2)
except Exception as ex:
    print('MONGO_READ_FAILED')
    traceback.print_exc()
    sys.exit(3)
