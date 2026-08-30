"""
Preflight read-only check: prints MongoDB connectivity and counts.
Outputs exactly:
MONGODB_CONNECTION_OK
DATABASE_NAME
user_accounts_count
user_profiles_count
employees_count

Does not print connection strings or documents.
"""
from backend.app.config import settings
from pymongo import MongoClient
import sys

try:
    url = settings.MONGODB_URL
    if not url:
        print('MONGODB_CONNECTION_FAILED')
        sys.exit(2)
    client = MongoClient(url, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[settings.DATABASE_NAME]
    print('MONGODB_CONNECTION_OK')
    print(settings.DATABASE_NAME)
    print(db.user_accounts.count_documents({}))
    print(db.user_profiles.count_documents({}))
    print(db.employees.count_documents({}))
    client.close()
except Exception as e:
    print('MONGODB_CONNECTION_FAILED')
    print(str(e))
    sys.exit(3)
