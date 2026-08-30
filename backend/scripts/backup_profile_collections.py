"""
Backup helper for profile-related collections.
Creates a timestamped directory and exports JSON-lines files for:
 - user_accounts
 - user_profiles
 - employees

This script is READ-ONLY and will not modify the database.
It omits sensitive fields (passwordHash, password, tokens) from exported documents.
Do NOT run this automatically in production without verifying disk/location permissions.
"""
import os
import sys
import json
from datetime import datetime
from backend.app.config import settings
from pymongo import MongoClient

SENSITIVE_KEYS = {"passwordHash", "password", "tokens", "accessToken", "refreshToken"}


def scrub_doc(doc):
    if not isinstance(doc, dict):
        return doc
    return {k: v for k, v in doc.items() if k not in SENSITIVE_KEYS}


def main():
    url = settings.MONGODB_URL
    if not url:
        print('MONGO_READ_FAILED: No MONGODB_URL configured')
        return 2

    client = MongoClient(url, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command('ping')
    except Exception as e:
        print('MONGO_PING_FAILED')
        print(str(e))
        return 3

    db = client[settings.DATABASE_NAME]

    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    base_dir = os.path.join('backups', f'user_profiles_backup_{ts}')
    os.makedirs(base_dir, exist_ok=False)

    collections = ['user_accounts', 'user_profiles', 'employees']
    report = {}

    for coll_name in collections:
        out_path = os.path.join(base_dir, f"{coll_name}.jsonl")
        count = 0
        with open(out_path, 'w', encoding='utf-8') as fh:
            cursor = db[coll_name].find({}, {'_id': 0})
            for doc in cursor:
                safe_doc = scrub_doc(doc)
                fh.write(json.dumps(safe_doc, default=str) + '\n')
                count += 1
        report[coll_name] = count

    client.close()

    print('Backup complete')
    print('Backup directory:', base_dir)
    for k, v in report.items():
        print(f'Exported {v} documents from {k}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
