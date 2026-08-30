#!/usr/bin/env python3
"""Normalize password lifecycle metadata for existing employee accounts.

Rules:
- Only operate against an explicitly supplied DATABASE_NAME.
- Refuse to run against workforce_db.
- Never overwrite passwordHash or plaintext passwords.
- Idempotent: safe to rerun.
- Report counts only.
"""

import os
import sys
from datetime import datetime, timezone

import bcrypt
from pymongo import MongoClient

MONGODB_URL = os.environ.get("MONGODB_URL")
DATABASE_NAME = os.environ.get("DATABASE_NAME")

if not MONGODB_URL:
    print("ERROR: MONGODB_URL must be set before running this script.")
    sys.exit(1)
if not DATABASE_NAME:
    print("ERROR: DATABASE_NAME must be set before running this script.")
    sys.exit(1)
if DATABASE_NAME == "workforce_db":
    print("ERROR: Refusing to run this migration against workforce_db. Use workforce_db_test or an explicit override.")
    sys.exit(2)

client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]

updated_default = 0
updated_custom = 0
unchanged = 0
for account in db.user_accounts.find({"role": "EMPLOYEE"}, {
    "_id": 1,
    "empId": 1,
    "passwordHash": 1,
    "passwordStatus": 1,
    "mustChangePassword": 1,
    "passwordChangedAt": 1,
}):
    emp_id = str(account.get("empId") or "").strip()
    password_hash = str(account.get("passwordHash") or "").strip()
    if not emp_id or not password_hash:
        continue

    try:
        matches_default = bcrypt.checkpw(emp_id.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        matches_default = False

    desired_status = "default" if matches_default else "custom"
    desired_change = False
    now = datetime.now(timezone.utc).isoformat()
    update_doc = {"$set": {"mustChangePassword": desired_change}} 

    current_status = str(account.get("passwordStatus") or "").strip().lower()
    if current_status != desired_status:
        update_doc["$set"]["passwordStatus"] = desired_status
        if desired_status == "default":
            update_doc["$set"]["passwordChangedAt"] = account.get("passwordChangedAt") or None
            updated_default += 1
        else:
            update_doc["$set"]["passwordChangedAt"] = account.get("passwordChangedAt") or now
            updated_custom += 1
    else:
        # If we are already in the correct status, keep passwordChangedAt only when it is meaningful.
        if current_status == "custom" and account.get("passwordChangedAt") is None:
            update_doc["$set"]["passwordChangedAt"] = now
        if current_status == "default" and account.get("passwordChangedAt") is not None:
            update_doc["$set"]["passwordChangedAt"] = account.get("passwordChangedAt")
        unchanged += 1

    if len(update_doc["$set"]) > 1 or current_status != desired_status or (current_status == "custom" and account.get("passwordChangedAt") is None):
        db.user_accounts.update_one({"_id": account["_id"]}, update_doc)

print(f"TOTAL_EMPLOYEE_ACCOUNTS={db.user_accounts.count_documents({'role': 'EMPLOYEE'})}")
print(f"UPDATED_DEFAULT={updated_default}")
print(f"UPDATED_CUSTOM={updated_custom}")
print(f"UNCHANGED={unchanged}")
print("STATUS=SUCCESS")
