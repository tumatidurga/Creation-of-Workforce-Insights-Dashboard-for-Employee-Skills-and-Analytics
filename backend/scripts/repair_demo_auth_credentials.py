#!/usr/bin/env python3
"""Repair demo/test authentication credentials without changing application logic.

This script intentionally restores the development/demo credential policy used by the
project: employee accounts authenticate with their EmpID as the default password,
while the HR admin account uses the externally supplied HR_ADMIN_TEST_PASSWORD.

The script is intentionally minimal and does not alter roles, statuses, profiles,
JWT settings, or any non-credential fields beyond passwordHash when required.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import bcrypt
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parents[2]
if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env", override=True)

try:
    from backend.app.config import settings
except ImportError:  # pragma: no cover
    settings = None


ACTUAL_DB_NAME = os.environ.get("DATABASE_NAME")
ACTUAL_MONGO_URL = os.environ.get("MONGODB_URL")


def _mongo_client() -> MongoClient:
    mongo_url = ACTUAL_MONGO_URL or (settings.MONGODB_URL if settings else "mongodb://127.0.0.1:27017")
    db_name = ACTUAL_DB_NAME or (settings.DATABASE_NAME if settings else "workforce_db")
    return MongoClient(mongo_url, serverSelectionTimeoutMS=5000)[db_name]


def _hash_for_emp_id(emp_id: str) -> str:
    return bcrypt.hashpw(emp_id.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _matches_default_password(emp_id: str, password_hash: Any) -> bool:
    if not emp_id or not password_hash:
        return False
    try:
        return bcrypt.checkpw(emp_id.encode("utf-8"), str(password_hash).encode("utf-8"))
    except (TypeError, ValueError):
        return False


def _employee_audit(db) -> Tuple[int, int, int, int, List[Dict[str, Any]]]:
    total = 0
    active = 0
    already_valid = 0
    invalid = 0
    audit_rows: List[Dict[str, Any]] = []

    for account in db.user_accounts.find({"role": "EMPLOYEE"}):
        total += 1
        status = str(account.get("status") or "").strip().upper()
        emp_id = str(account.get("empId") or "").strip()
        user_id = str(account.get("userId") or "").strip() or emp_id
        matches_default = False

        if status == "ACTIVE":
            active += 1
            password_hash = account.get("passwordHash")
            matches_default = _matches_default_password(emp_id, password_hash)
            if matches_default:
                already_valid += 1
            else:
                invalid += 1

        audit_rows.append({
            "userId": user_id,
            "empId": emp_id,
            "role": str(account.get("role") or "").strip() or "EMPLOYEE",
            "status": status,
            "matchesDefaultPassword": matches_default,
        })

    return total, active, already_valid, invalid, audit_rows


def _persist_audit_report(rows: List[Dict[str, Any]], dry_run: bool) -> None:
    report_path = Path(r"C:\Users\abhi7\.copilot\session-state\0a30215a-1c79-4256-918c-a87e912df5ed\files\auth_repair_audit.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dryRun": dry_run,
        "accounts": [
            {
                "userId": row.get("userId"),
                "empId": row.get("empId"),
                "role": row.get("role"),
                "status": row.get("status"),
                "matchesDefaultPassword": bool(row.get("matchesDefaultPassword")),
            }
            for row in rows
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _find_hr_account(db):
    return db.user_accounts.find_one({
        "$or": [
            {"userId": "hr-admin"},
            {"email": "priya.sharma@enterprise.com"},
        ],
        "role": "HR_ADMIN",
    })


def _repair_employee_credentials(db, dry_run: bool) -> Tuple[int, int, List[str]]:
    repaired = 0
    repaired_ids: List[str] = []
    if dry_run:
        _, _, _, _, _ = _employee_audit(db)
        return 0, 0, []

    for account in db.user_accounts.find({"role": "EMPLOYEE", "status": "ACTIVE"}):
        emp_id = str(account.get("empId") or "").strip()
        if not emp_id:
            continue
        new_hash = _hash_for_emp_id(emp_id)
        db.user_accounts.update_one(
            {"_id": account["_id"]},
            {"$set": {"passwordHash": new_hash}},
        )
        repaired += 1
        repaired_ids.append(emp_id)

    return repaired, 0, repaired_ids


def _repair_hr_account_if_needed(db, dry_run: bool) -> bool:
    env_password = os.environ.get("HR_ADMIN_TEST_PASSWORD")
    account = _find_hr_account(db)
    if not account:
        return False
    if not env_password:
        return False
    expected_hash = bcrypt.hashpw(env_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    current_hash = str(account.get("passwordHash") or "")
    if current_hash and bcrypt.checkpw(env_password.encode("utf-8"), current_hash.encode("utf-8")):
        return True
    if dry_run:
        return True
    db.user_accounts.update_one({"_id": account["_id"]}, {"$set": {"passwordHash": expected_hash}})
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair demo auth credentials using EmpID as the default employee password.")
    parser.add_argument("--dry-run", action="store_true", help="Audit and print the expected changes without writing to MongoDB.")
    args = parser.parse_args()

    db = _mongo_client()
    total, active, already_valid, invalid, audit_rows = _employee_audit(db)
    hr_account = _find_hr_account(db)
    hr_configured = bool(os.environ.get("HR_ADMIN_TEST_PASSWORD"))

    _persist_audit_report(audit_rows, args.dry_run)

    if args.dry_run:
        employee_repair_count = sum(1 for row in audit_rows if row["status"] == "ACTIVE" and not row["matchesDefaultPassword"])
        hr_repair = bool(hr_account and hr_configured)
        print(f"TOTAL_EMPLOYEE_ACCOUNTS = {total}")
        print(f"ACTIVE_EMPLOYEE_ACCOUNTS = {active}")
        print(f"ALREADY_VALID_EMPLOYEE_HASHES = {already_valid}")
        print(f"INVALID_EMPLOYEE_HASHES = {invalid}")
        print(f"EMPLOYEE_HASHES_REPAIRED = {employee_repair_count}")
        print(f"HR_ACCOUNT_FOUND = {'TRUE' if hr_account else 'FALSE'}")
        print(f"HR_ADMIN_TEST_PASSWORD_CONFIGURED = {'TRUE' if hr_configured else 'FALSE'}")
        print(f"HR_PASSWORD_REPAIRED = {'TRUE' if hr_repair else 'FALSE'}")
        return 0

    repaired_count, _, _ = _repair_employee_credentials(db, dry_run=False)
    hr_repaired = _repair_hr_account_if_needed(db, dry_run=False)

    print(f"TOTAL_EMPLOYEE_ACCOUNTS = {total}")
    print(f"ACTIVE_EMPLOYEE_ACCOUNTS = {active}")
    print(f"ALREADY_VALID_EMPLOYEE_HASHES = {already_valid}")
    print(f"INVALID_EMPLOYEE_HASHES = {invalid}")
    print(f"EMPLOYEE_HASHES_REPAIRED = {repaired_count}")
    print(f"HR_ACCOUNT_FOUND = {'TRUE' if hr_account else 'FALSE'}")
    print(f"HR_ADMIN_TEST_PASSWORD_CONFIGURED = {'TRUE' if hr_configured else 'FALSE'}")
    print(f"HR_PASSWORD_REPAIRED = {'TRUE' if hr_repaired else 'FALSE'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"AUTH_REPAIR_FAILED = {type(exc).__name__}", file=sys.stderr)
        raise
