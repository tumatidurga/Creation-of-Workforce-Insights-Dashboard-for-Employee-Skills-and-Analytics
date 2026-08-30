#!/usr/bin/env python3
"""
Strict remediation script for the test authentication bootstrap.

Safety rules:
- DATABASE_NAME must be explicitly provided via environment.
- The script will only proceed if the user_accounts collection contains exactly two
  known test accounts.
- The script will not create, upsert, or modify any other accounts.
- Plaintext credentials are never written to the repository, source tree, logs, or
  other project-scoped files. Passwords are generated and retained only in memory
  while the script runs.
"""

import asyncio
import os
import secrets
import sys

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.environ.get("MONGODB_URL")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
HR_PW = os.environ.get("HR_ADMIN_TEST_PASSWORD")
EMP_PW = os.environ.get("EMPLOYEE_TEST_PASSWORD")

if not MONGODB_URL:
    print("ERROR: MONGODB_URL must be set in environment before running this script. Exiting.")
    sys.exit(1)
if not DATABASE_NAME:
    print("ERROR: DATABASE_NAME must be set in environment before running this script. No default allowed. Exiting.")
    sys.exit(1)

if not HR_PW:
    HR_PW = secrets.token_urlsafe(24)
if not EMP_PW:
    EMP_PW = secrets.token_urlsafe(24)


async def main():
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[DATABASE_NAME]

    try:
        total = await db.user_accounts.count_documents({})
    except Exception as exc:
        print("ERROR: Unable to query user_accounts collection:", str(exc))
        client.close()
        sys.exit(1)

    if total != 2:
        print(f"ABORT: user_accounts contains {total} documents (expected exactly 2). Aborting without changes.")
        client.close()
        sys.exit(1)

    targets = ["hr-admin", "employee-self-service"]
    docs = []
    for uid in targets:
        doc = await db.user_accounts.find_one({"userId": uid})
        if not doc:
            print(f"ABORT: Required account with userId=\"{uid}\" not found. Aborting without changes.")
            client.close()
            sys.exit(1)
        docs.append(doc)

    hr_hash = bcrypt.hashpw(HR_PW.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    emp_hash = bcrypt.hashpw(EMP_PW.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        res_hr = await db.user_accounts.update_one(
            {"userId": "hr-admin"},
            {"$set": {"passwordHash": hr_hash, "status": "ACTIVE", "updatedAt": __import__("datetime").datetime.utcnow().isoformat()}},
            upsert=False,
        )

        res_emp = await db.user_accounts.update_one(
            {"userId": "employee-self-service"},
            {"$set": {"passwordHash": emp_hash, "status": "ACTIVE", "empId": "EMP000001", "updatedAt": __import__("datetime").datetime.utcnow().isoformat()}},
            upsert=False,
        )

        if res_hr.matched_count != 1 or res_emp.matched_count != 1:
            print("ERROR: One or both updates did not match exactly one document. Aborting and not making partial changes.")
            client.close()
            sys.exit(1)
    except Exception as exc:
        print("ERROR: Exception during updates:", str(exc))
        client.close()
        sys.exit(1)

    docs_after = await db.user_accounts.find({}, {"_id": 0, "userId": 1, "empId": 1, "role": 1, "status": 1, "passwordHash": 1}).to_list(None)
    if len(docs_after) != 2:
        print("ERROR: post-update user_accounts contains unexpected number of documents. Aborting.")
        client.close()
        sys.exit(1)

    hashes = []
    for doc in docs_after:
        if doc.get("status") != "ACTIVE":
            print(f"ERROR: Account {doc.get('userId')} is not ACTIVE. Aborting.")
            client.close()
            sys.exit(1)
        if not doc.get("passwordHash"):
            print(f"ERROR: Account {doc.get('userId')} missing passwordHash. Aborting.")
            client.close()
            sys.exit(1)
        hashes.append(doc.get("passwordHash"))

    if len(set(hashes)) != 2:
        print("ERROR: Both accounts have the same password hash after update. Aborting.")
        client.close()
        sys.exit(1)

    emp_doc = next((doc for doc in docs_after if doc.get("userId") == "employee-self-service"), None)
    if not emp_doc or emp_doc.get("empId") != "EMP000001":
        print("ERROR: employee-self-service empId is not EMP000001. Aborting.")
        client.close()
        sys.exit(1)

    client.close()
    print(f"DATABASE_NAME={DATABASE_NAME}")
    print(f"ACCOUNT_COUNT={len(docs_after)}")
    print("STATUS=SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
