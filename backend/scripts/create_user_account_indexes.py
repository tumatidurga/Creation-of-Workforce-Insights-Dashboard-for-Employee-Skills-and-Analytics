#!/usr/bin/env python3
"""Create safe unique indexes on user_accounts.empId and user_accounts.email.

Safety rules:
- Only works on explicitly supplied DATABASE_NAME.
- Refuses to run against workforce_db.
- Detects duplicate empId / normalized email values before creating indexes.
- Idempotent: repeated runs are safe and do not create duplicate indexes.
- Does not print password data or hashes.
"""

import os
import sys
from pymongo import MongoClient

MONGODB_URL = os.environ.get("MONGODB_URL")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
PRODUCTION_INDEX_CONFIRM = os.environ.get("PRODUCTION_INDEX_CONFIRM", "").strip().upper()

if not MONGODB_URL:
    print("ERROR: MONGODB_URL must be set before running this migration.")
    sys.exit(1)
if not DATABASE_NAME:
    print("ERROR: DATABASE_NAME must be set before running this migration.")
    sys.exit(1)
if DATABASE_NAME == "workforce_db" and PRODUCTION_INDEX_CONFIRM != "YES":
    print("ERROR: Production index creation requires DATABASE_NAME=workforce_db and PRODUCTION_INDEX_CONFIRM=YES.")
    sys.exit(2)

client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]

# Detect duplicates before creating any unique index.
empid_duplicates = []
for value in db.user_accounts.aggregate([
    {"$match": {"empId": {"$ne": None, "$exists": True}}},
    {"$group": {"_id": "$empId", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}},
    {"$project": {"_id": 0, "empId": "$_id", "count": 1}},
]):
    empid_duplicates.append(value)

email_duplicates = []
for value in db.user_accounts.aggregate([
    {"$match": {"email": {"$ne": None, "$exists": True, "$ne": ""}}},
    {"$group": {"_id": {"$toLower": "$email"}, "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}},
    {"$project": {"_id": 0, "email": "$_id", "count": 1}},
]):
    email_duplicates.append(value)

if empid_duplicates or email_duplicates:
    print(f"DUPLICATE_EMPID={len(empid_duplicates)}")
    print(f"DUPLICATE_EMAIL={len(email_duplicates)}")
    print("STATUS=ABORT_DUPLICATES")
    sys.exit(3)

# Safe sparse unique indexes for employee IDs and email addresses.
# Multiple runs leave existing indexes in place.
try:
    db.user_accounts.create_index("empId", unique=True, sparse=True)
except Exception as exc:
    print(f"ERROR: failed to create empId index: {exc}")
    sys.exit(4)

try:
    db.user_accounts.create_index("email", unique=True, sparse=True)
except Exception as exc:
    print(f"ERROR: failed to create email index: {exc}")
    sys.exit(5)

info = db.user_accounts.index_information()
print(f"UNIQUE_EMPID_INDEX={'empId_1' in info}")
print(f"UNIQUE_EMAIL_INDEX={'email_1' in info}")
print("STATUS=SUCCESS")
