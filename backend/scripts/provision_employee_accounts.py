#!/usr/bin/env python3
"""
Provision login accounts for employees based on the employees master collection.

Safety rules:
- DATABASE_NAME and MONGODB_URL must be provided via environment when a real execution is attempted.
- The script defaults to dry-run mode for safety and requires an explicit production confirmation.
- Plaintext passwords are NEVER printed or written to files. The default password is the employee's EmpID but only its bcrypt hash is stored.
- The script is idempotent and will not overwrite existing accounts or custom passwords.
- Mass provisioning must only allow employees with EmploymentStatus exactly "Active" and without an ExitDate.

Output: summary counts only.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - project may not vendor python-dotenv
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

MONGODB_URL = os.environ.get("MONGODB_URL")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
DRY_RUN = os.environ.get("PROVISION_DRY_RUN", "true").lower() in ("1", "true", "yes")
PRODUCTION_CONFIRMATION = os.environ.get("PROVISION_CONFIRM_PRODUCTION", "").strip().upper()
CANARY_EMP_ID = os.environ.get("CANARY_EMP_ID", "").strip()

BATCH_SIZE = 500
ALLOWED_ACTIVE_STATUS = "active"


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_email(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _is_valid_email(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    return bool(v) and "@" in v and "." in v.split("@")[-1]


def _employee_has_exit_date(doc: Dict[str, Any]) -> bool:
    raw = doc.get("ExitDate")
    if raw is None:
        return False
    if isinstance(raw, str):
        value = raw.strip()
        return bool(value) and value.upper() not in {"N/A", "NONE", "NULL", "UNKNOWN"}
    return True


def _is_active_employee(doc: Dict[str, Any]) -> bool:
    return _normalize_status(doc.get("EmploymentStatus") or doc.get("status") or "") == ALLOWED_ACTIVE_STATUS


def _build_account(emp_id: str, email: str, name: str, now: str) -> Dict[str, Any]:
    pw_hash = bcrypt.hashpw(emp_id.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return {
        "userId": emp_id,
        "empId": emp_id,
        "email": email or None,
        "name": name,
        "role": "EMPLOYEE",
        "passwordHash": pw_hash,
        "passwordStatus": "default",
        "mustChangePassword": False,
        "passwordChangedAt": None,
        "status": "ACTIVE",
        "createdAt": now,
        "updatedAt": now,
    }


def _employee_duplicate_sets(employees: Iterable[Dict[str, Any]]) -> Tuple[Set[str], Set[str]]:
    emp_ids: Set[str] = set()
    email_values: Set[str] = set()
    duplicate_emp_ids: Set[str] = set()
    duplicate_emails: Set[str] = set()
    seen_emp_ids: Set[str] = set()
    seen_emails: Set[str] = set()

    for doc in employees:
        emp_id_raw = doc.get("EmpID") or doc.get("empId")
        emp_id = str(emp_id_raw).strip() if emp_id_raw is not None else ""
        if emp_id:
            if emp_id in seen_emp_ids:
                duplicate_emp_ids.add(emp_id)
            else:
                seen_emp_ids.add(emp_id)
            emp_ids.add(emp_id)

        email_raw = doc.get("Email") or doc.get("email") or ""
        email = _normalize_email(email_raw)
        if email:
            if email in seen_emails:
                duplicate_emails.add(email)
            else:
                seen_emails.add(email)
            email_values.add(email)

    return duplicate_emp_ids, duplicate_emails


def _existing_account_index(accounts: Iterable[Dict[str, Any]]) -> Dict[str, Set[str]]:
    result = {"empId": set(), "email": set()}
    for account in accounts:
        emp_id = str(account.get("empId") or "").strip()
        email = _normalize_email(account.get("email") or "")
        if emp_id:
            result["empId"].add(emp_id)
        if email:
            result["email"].add(email)
    return result


def _evaluate_employee_for_account(
    doc: Dict[str, Any],
    duplicate_emp_ids: Set[str],
    duplicate_emails: Set[str],
    existing_accounts: Dict[str, Set[str]],
) -> Optional[str]:
    emp_id_raw = doc.get("EmpID") or doc.get("empId")
    emp_id = str(emp_id_raw).strip() if emp_id_raw is not None else ""
    if not emp_id:
        return "missing_empid"

    if emp_id in duplicate_emp_ids:
        return "duplicate_empid"

    status = _normalize_status(doc.get("EmploymentStatus") or doc.get("status") or "")
    if status != ALLOWED_ACTIVE_STATUS:
        return "non_active_status"

    if _employee_has_exit_date(doc):
        return "exit_date"

    email = _normalize_email(doc.get("Email") or doc.get("email") or "")
    if not _is_valid_email(email):
        return "invalid_email"

    if email in duplicate_emails:
        return "duplicate_email"

    if emp_id in existing_accounts.get("empId", set()):
        return "existing_empid"

    if email in existing_accounts.get("email", set()):
        return "existing_email"

    return None


async def _run_canary_mode(db) -> None:
    global DRY_RUN

    if not CANARY_EMP_ID:
        return

    canary_emp_id = CANARY_EMP_ID.strip()
    employee_doc = await db.employees.find_one({"EmpID": canary_emp_id})
    if employee_doc is None:
        print("CANARY_MODE=TRUE")
        print("CANARY_MATCH_COUNT=0")
        print("CANARY_ALREADY_EXISTS=FALSE")
        print("CANARY_WOULD_CREATE=0")
        print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
        print("CANARY_STATUS=NOT_FOUND")
        return

    match_count = await db.employees.count_documents({"EmpID": canary_emp_id})
    if match_count != 1:
        print("CANARY_MODE=TRUE")
        print(f"CANARY_MATCH_COUNT={match_count}")
        print("CANARY_ALREADY_EXISTS=FALSE")
        print("CANARY_WOULD_CREATE=0")
        print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
        print("CANARY_STATUS=INVALID_SELECTION")
        return

    if not _is_active_employee(employee_doc):
        print("CANARY_MODE=TRUE")
        print("CANARY_MATCH_COUNT=1")
        print("CANARY_ALREADY_EXISTS=FALSE")
        print("CANARY_WOULD_CREATE=0")
        print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
        print("CANARY_STATUS=INACTIVE")
        return

    if _employee_has_exit_date(employee_doc):
        print("CANARY_MODE=TRUE")
        print("CANARY_MATCH_COUNT=1")
        print("CANARY_ALREADY_EXISTS=FALSE")
        print("CANARY_WOULD_CREATE=0")
        print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
        print("CANARY_STATUS=EXIT_DATE")
        return

    email = _normalize_email(employee_doc.get("Email") or employee_doc.get("email") or "")
    if not _is_valid_email(email):
        print("CANARY_MODE=TRUE")
        print("CANARY_MATCH_COUNT=1")
        print("CANARY_ALREADY_EXISTS=FALSE")
        print("CANARY_WOULD_CREATE=0")
        print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
        print("CANARY_STATUS=INVALID_EMAIL")
        return

    existing = await db.user_accounts.find_one({"$or": [{"empId": canary_emp_id}, {"email": {"$regex": f"^{email}$", "$options": "i"}}]})
    if existing:
        print("CANARY_MODE=TRUE")
        print("CANARY_MATCH_COUNT=1")
        print("CANARY_ALREADY_EXISTS=TRUE")
        print("CANARY_WOULD_CREATE=0")
        print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
        print("CANARY_STATUS=ALREADY_EXISTS")
        return

    if DRY_RUN:
        print("CANARY_MODE=TRUE")
        print("CANARY_MATCH_COUNT=1")
        print("CANARY_ALREADY_EXISTS=FALSE")
        print("CANARY_WOULD_CREATE=1")
        print("PROVISION_DRY_RUN=TRUE")
        print("CANARY_STATUS=DRY_RUN_OK")
        return

    now = datetime.now(timezone.utc).isoformat()
    account = _build_account(canary_emp_id, email, str(employee_doc.get("EmployeeName") or canary_emp_id), now)
    await db.user_accounts.insert_one(account)
    print("CANARY_MODE=TRUE")
    print("CANARY_MATCH_COUNT=1")
    print("CANARY_ALREADY_EXISTS=FALSE")
    print("CANARY_WOULD_CREATE=1")
    print("PROVISION_DRY_RUN=FALSE")
    print("CANARY_STATUS=CREATED")
    return


async def main():
    global DRY_RUN, MONGODB_URL, DATABASE_NAME

    if not MONGODB_URL:
        print("ERROR: MONGODB_URL must be set in environment before running this script. Exiting.")
        sys.exit(1)
    if not DATABASE_NAME:
        print("ERROR: DATABASE_NAME must be set in environment before running this script. No default allowed. Exiting.")
        sys.exit(1)
    if not DRY_RUN and PRODUCTION_CONFIRMATION != "YES":
        print("ERROR: Real provisioning is blocked. Set PROVISION_DRY_RUN=true for dry-run, or set PROVISION_CONFIRM_PRODUCTION=YES to confirm production execution.")
        sys.exit(2)

    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[DATABASE_NAME]

    if CANARY_EMP_ID:
        await _run_canary_mode(db)
        client.close()
        return

    try:
        total_employees = await db.employees.count_documents({})
    except Exception as exc:
        print("ERROR: Unable to query employees collection:", str(exc))
        client.close()
        sys.exit(1)

    try:
        employee_docs = await db.employees.find({}, {"_id": 1, "EmpID": 1, "empId": 1, "Email": 1, "email": 1, "EmployeeName": 1, "firstName": 1, "lastName": 1, "status": 1, "EmploymentStatus": 1, "ExitDate": 1}).to_list(length=total_employees)
    except Exception as exc:
        print("ERROR: Unable to read employee documents:", str(exc))
        client.close()
        sys.exit(1)

    duplicate_emp_ids, duplicate_emails = _employee_duplicate_sets(employee_docs)

    try:
        existing_user_accounts = await db.user_accounts.find({}, {"_id": 0, "empId": 1, "email": 1}).to_list(length=None)
    except Exception as exc:
        print("ERROR: Unable to read user_accounts documents:", str(exc))
        client.close()
        sys.exit(1)
    existing_index = _existing_account_index(existing_user_accounts)

    totals = {
        "total_employees": total_employees,
        "active_employees_examined": 0,
        "already_accounted_skipped": 0,
        "non_active_skipped": 0,
        "exit_date_skipped": 0,
        "invalid_email_skipped": 0,
        "duplicate_empid_skipped": 0,
        "duplicate_email_skipped": 0,
        "missing_empid_skipped": 0,
        "eligible_candidates": 0,
    }
    to_create = []

    for doc in employee_docs:
        reason = _evaluate_employee_for_account(doc, duplicate_emp_ids, duplicate_emails, existing_index)
        if reason is None:
            emp_id_raw = doc.get("EmpID") or doc.get("empId")
            emp_id = str(emp_id_raw).strip() if emp_id_raw is not None else ""
            email = _normalize_email(doc.get("Email") or doc.get("email") or "")
            name = doc.get("EmployeeName") or "".join([str(doc.get("firstName") or ""), " ", str(doc.get("lastName") or "")]).strip() or emp_id
            totals["active_employees_examined"] += 1
            totals["eligible_candidates"] += 1
            to_create.append({
                "emp_id": emp_id,
                "email": email,
                "name": name,
            })
            continue

        if reason == "missing_empid":
            totals["missing_empid_skipped"] += 1
        elif reason == "duplicate_empid":
            totals["duplicate_empid_skipped"] += 1
        elif reason == "non_active_status":
            totals["non_active_skipped"] += 1
        elif reason == "exit_date":
            totals["exit_date_skipped"] += 1
        elif reason == "invalid_email":
            totals["invalid_email_skipped"] += 1
        elif reason == "duplicate_email":
            totals["duplicate_email_skipped"] += 1
        elif reason in {"existing_empid", "existing_email"}:
            totals["already_accounted_skipped"] += 1

    if totals["eligible_candidates"] == 0 and not to_create and total_employees == 0:
        print("DATABASE_NAME={}").format(DATABASE_NAME)
        print(f"TOTAL_EMPLOYEES={total_employees}")
        print("ACTIVE_EMPLOYEES_EXAMINED=0")
        print(f"ALREADY_ACCOUNTED_SKIPPED={totals['already_accounted_skipped']}")
        print(f"NON_ACTIVE_SKIPPED={totals['non_active_skipped']}")
        print(f"EXITDATE_SKIPPED={totals['exit_date_skipped']}")
        print(f"INVALID_EMAIL_SKIPPED={totals['invalid_email_skipped']}")
        print(f"DUPLICATE_EMPID_SKIPPED={totals['duplicate_empid_skipped']}")
        print(f"DUPLICATE_EMAIL_SKIPPED={totals['duplicate_email_skipped']}")
        print(f"CANDIDATES_ELIGIBLE={totals['eligible_candidates']}")
        print("TOTAL_ACCOUNTS_WOULD_BE_CREATED=0")
        print("STATUS=SUCCESS")
        client.close()
        return

    created = 0
    failed = 0
    for index in range(0, len(to_create), BATCH_SIZE):
        batch = to_create[index:index + BATCH_SIZE]
        if DRY_RUN:
            created += len(batch)
            continue
        try:
            docs = [
                _build_account(item["emp_id"], item["email"], item["name"], datetime.now(timezone.utc).isoformat())
                for item in batch
            ]
            res = await db.user_accounts.insert_many(docs)
            created += len(res.inserted_ids)
        except Exception:
            failed += len(batch)

    print(f"DATABASE_NAME={DATABASE_NAME}")
    print(f"TOTAL_EMPLOYEES={total_employees}")
    print(f"ACTIVE_EMPLOYEES_EXAMINED={totals['active_employees_examined']}")
    print(f"ALREADY_ACCOUNTED_SKIPPED={totals['already_accounted_skipped']}")
    print(f"NON_ACTIVE_SKIPPED={totals['non_active_skipped']}")
    print(f"EXITDATE_SKIPPED={totals['exit_date_skipped']}")
    print(f"INVALID_EMAIL_SKIPPED={totals['invalid_email_skipped']}")
    print(f"DUPLICATE_EMPID_SKIPPED={totals['duplicate_empid_skipped']}")
    print(f"DUPLICATE_EMAIL_SKIPPED={totals['duplicate_email_skipped']}")
    print(f"MISSING_EMPID_SKIPPED={totals['missing_empid_skipped']}")
    print(f"CANDIDATES_ELIGIBLE={totals['eligible_candidates']}")
    print(f"TOTAL_ACCOUNTS_WOULD_BE_CREATED={created if DRY_RUN else len(to_create)}")
    print(f"PROVISION_DRY_RUN={'TRUE' if DRY_RUN else 'FALSE'}")
    print(f"BATCH_SIZE={BATCH_SIZE}")
    print(f"FAILED={failed}")
    print("STATUS=SUCCESS")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
