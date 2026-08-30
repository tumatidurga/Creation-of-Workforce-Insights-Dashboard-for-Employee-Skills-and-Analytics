"""
Read-only inspection of manager employee records in MongoDB.

This script reads the current employees collection and prints a small sample of
manager records and a validation summary for all identified manager IDs.
It does not modify MongoDB.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from pymongo import MongoClient
from pymongo.errors import PyMongoError

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings


def clean(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        text = value.strip()
        return text if text else "N/A"
    return str(value)


def main() -> int:
    url = settings.MONGODB_URL
    if not url:
        print("MONGO_READ_FAILED: No MONGODB_URL configured in settings")
        return 2

    db_name = settings.DATABASE_NAME
    print("Attempting read-only MongoDB connection...")

    try:
        client = MongoClient(url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[db_name]

        # Identify managers by Role == 'Manager'
        manager_docs = list(db.employees.find(
            {"Role": "Manager"},
            {
                "_id": 0,
                "EmpID": 1,
                "EmployeeName": 1,
                "Email": 1,
                "Phone": 1,
                "Department": 1,
                "JobRole": 1,
                "Location": 1,
                "EmploymentStatus": 1,
                "Role": 1,
                "ManagerID": 1,
            }
        ))

        manager_ids = [doc.get("EmpID") for doc in manager_docs if doc.get("EmpID")]

        print(f"Manager rows found: {len(manager_docs)}")
        print(f"Unique manager IDs: {len(set(manager_ids))}")
        print()

        sample_ids = ["EMP008010", "EMP000010", "EMP000110", "EMP000210", "EMP008110"]
        print("Sample manager records (selected IDs):")
        for manager_id in sample_ids:
            doc = db.employees.find_one({"EmpID": manager_id}, {
                "_id": 0,
                "EmpID": 1,
                "EmployeeName": 1,
                "Email": 1,
                "Phone": 1,
                "Department": 1,
                "JobRole": 1,
                "Location": 1,
                "EmploymentStatus": 1,
                "Role": 1,
                "ManagerID": 1,
            })
            if not doc:
                print(f"- {manager_id}: NOT_FOUND")
                continue
            print("- " + str(doc))
        print()

        print("Validation of all 100 manager IDs:")
        missing_roles = []
        missing_profile = []
        for manager_id in sorted(set(manager_ids)):
            doc = db.employees.find_one({"EmpID": manager_id}, {"_id": 0, "EmpID": 1, "Role": 1, "EmployeeName": 1})
            if doc is None:
                missing_profile.append(manager_id)
                continue
            if str(doc.get("Role") or "").strip() != "Manager":
                missing_roles.append({"EmpID": manager_id, "Role": doc.get("Role")})

        print(f"manager ids with no employee profile: {len(missing_profile)}")
        if missing_profile:
            print(f"  {missing_profile[:10]}")

        print(f"manager ids with Role != 'Manager': {len(missing_roles)}")
        if missing_roles:
            for item in missing_roles[:10]:
                print(f"  {item}")

        if not missing_profile and not missing_roles:
            print("All manager IDs found in employees collection and all have Role = 'Manager'.")

        return 0

    except PyMongoError as exc:
        print("MONGO_READ_FAILED")
        print(str(exc))
        return 2
    except Exception as exc:  # pragma: no cover
        print("MONGO_READ_FAILED")
        print(str(exc))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
