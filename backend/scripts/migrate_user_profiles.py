"""
Non-destructive migration script to create per-user user_profiles documents.

Rules:
- Read user_accounts and employees collections.
- For each user_accounts document, if user_profiles.userId does not exist, create a profile using account data and linked employee data (if empId present).
- Never overwrite existing user_profiles documents.
- Never delete CURRENT_USER.
- Idempotent: repeated runs are safe.

This script is intended to be run manually in a controlled environment by an operator.
Do NOT run automatically against production without backup and verification.
"""

import sys
import traceback
from datetime import datetime

from backend.app.database import get_database


def migrate():
    db = get_database()
    if db is None:
        print("ERROR: database not available. Run this script within the application environment where MongoDB is reachable.")
        return 1

    # Limit projection to only the safe, needed account fields so sensitive fields (passwordHash, tokens) are never loaded
    projection = {"userId": 1, "empId": 1, "name": 1, "email": 1, "role": 1, "mfaEnabled": 1, "lastLogin": 1}
    accounts_cursor = db.user_accounts.find({}, projection)

    scanned = 0
    created = 0
    existing = 0
    employees_matched = 0
    hr_profiles_created = 0
    skipped = 0
    errors = 0

    try:
        for acct in accounts_cursor:
            scanned += 1
            try:
                user_id = acct.get("userId")
                if not user_id:
                    skipped += 1
                    continue

                # Check for existing per-user profile
                existing_profile = db.user_profiles.find_one({"userId": user_id}, {"_id": 0})
                if existing_profile:
                    existing += 1
                    continue

                created_at = datetime.utcnow().isoformat()

                profile_doc = {
                    "userId": user_id,
                    "empId": acct.get("empId"),
                    "name": acct.get("name"),
                    "email": acct.get("email"),
                    "role": acct.get("role"),
                    # presentation fields only
                    "department": None,
                    "jobTitle": None,
                    "phone": None,
                    "avatar": None,
                    # preserve existing explicit MFA flag, do not enable by default
                    "mfaEnabled": bool(acct.get("mfaEnabled", False)),
                    "lastLogin": acct.get("lastLogin"),
                    "createdAt": created_at,
                    "updatedAt": created_at,
                    "migratedFrom": "migration_v0.2",
                }

                # If employee exists, copy only non-sensitive presentation fields
                emp_id = acct.get("empId")
                if emp_id:
                    emp = db.employees.find_one({"EmpID": emp_id}, {"_id": 0, "EmployeeName": 1, "Department": 1, "JobRole": 1, "Phone": 1, "avatar": 1})
                    if emp:
                        employees_matched += 1
                        profile_doc["name"] = profile_doc.get("name") or emp.get("EmployeeName")
                        profile_doc["department"] = emp.get("Department") or profile_doc.get("department")
                        profile_doc["jobTitle"] = emp.get("JobRole") or profile_doc.get("jobTitle")
                        profile_doc["phone"] = emp.get("Phone") or profile_doc.get("phone")
                        # Validate avatar: accept only non-empty strings starting with http:// or https://
                        emp_avatar = emp.get("avatar")
                        if isinstance(emp_avatar, str) and emp_avatar.strip() and emp_avatar.strip().lower().startswith(("http://", "https://")):
                            profile_doc["avatar"] = emp_avatar.strip()

                db.user_profiles.insert_one(profile_doc)
                created += 1
                # HR accounts typically have empId == None
                if acct.get("empId") is None and acct.get("role") == "HR_ADMIN":
                    hr_profiles_created += 1
            except Exception:
                errors += 1
                print("Error handling account:", acct.get("userId"))
                traceback.print_exc()
    except Exception:
        print("Failed to iterate accounts. Ensure this script runs in a trusted environment.")
        traceback.print_exc()
        return 2

    print("User profile migration\n----------------------")
    print(f"Accounts scanned: {scanned}")
    print(f"Profiles created: {created}")
    print(f"Profiles already existing: {existing}")
    print(f"Employees matched: {employees_matched}")
    print(f"HR profiles created (empId is null): {hr_profiles_created}")
    print(f"Skipped (invalid account): {skipped}")
    print(f"Errors: {errors}")

    return 0


if __name__ == '__main__':
    sys.exit(migrate())
