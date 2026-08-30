"""
Read-only validation of employee manager relationships in MongoDB.

This script reads the existing employees collection and reports:
- total employees
- total manager records by Role == 'Manager'
- total employee-to-manager assignments
- valid vs broken ManagerID references
- employees per manager

It does not insert, update, delete, or modify any MongoDB data.
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Set

from pymongo import MongoClient
from pymongo.errors import PyMongoError

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings


def normalize_emp_id(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def is_non_empty_manager_id(value: Any) -> bool:
    if value is None:
        return False
    text = normalize_emp_id(value)
    return bool(text) and text.upper() not in {"N/A", "NA", "NONE", "NULL", "UNKNOWN"}


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

        employees = list(db.employees.find({}, {"_id": 0, "EmpID": 1, "Role": 1, "ManagerID": 1}))

        total_employees = len(employees)
        all_emp_ids: Set[str] = set()
        manager_emp_ids: Set[str] = set()
        manager_doc_counts: Dict[str, int] = defaultdict(int)
        manager_employee_counts: Dict[str, int] = defaultdict(int)
        broken_manager_refs: List[str] = []
        valid_manager_refs = 0
        total_employee_to_manager_assignments = 0

        for emp in employees:
            emp_id = normalize_emp_id(emp.get("EmpID"))
            if emp_id:
                all_emp_ids.add(emp_id)

            role = str(emp.get("Role") or "").strip()
            if role.lower() == "manager":
                if emp_id:
                    manager_emp_ids.add(emp_id)
                manager_doc_counts[emp_id] += 1

        for emp in employees:
            emp_id = normalize_emp_id(emp.get("EmpID"))
            manager_id = emp.get("ManagerID")
            if is_non_empty_manager_id(manager_id):
                total_employee_to_manager_assignments += 1
                manager_ref = normalize_emp_id(manager_id)
                if manager_ref in all_emp_ids:
                    valid_manager_refs += 1
                    if manager_ref in manager_emp_ids:
                        manager_employee_counts[manager_ref] += 1
                else:
                    broken_manager_refs.append(f"{emp_id}->{manager_ref}")

        # Some manager records may not have assigned reports; include them with zero.
        for manager_id in sorted(manager_emp_ids):
            manager_employee_counts.setdefault(manager_id, 0)

        print("READ_ONLY_MANAGER_RELATIONSHIP_SUMMARY")
        print(f"database: {db_name}")
        print(f"total_employees: {total_employees}")
        print(f"total_managers: {len(manager_emp_ids)}")
        print(f"total_employee_to_manager_assignments: {total_employee_to_manager_assignments}")
        print(f"valid_manager_references: {valid_manager_refs}")
        print(f"broken_manager_references: {len(broken_manager_refs)}")

        if broken_manager_refs:
            print("broken_manager_reference_examples:")
            for entry in broken_manager_refs[:20]:
                print(f"  - {entry}")
        else:
            print("broken_manager_reference_examples: none")

        print("employees_per_manager:")
        if manager_emp_ids:
            for manager_id in sorted(manager_employee_counts):
                print(f"  - {manager_id}: {manager_employee_counts[manager_id]}")
        else:
            print("  - none")

        # Compact summary line as requested
        print("SUMMARY")
        print(
            f"Total Employees={total_employees}; "
            f"Managers={len(manager_emp_ids)}; "
            f"Assignments={total_employee_to_manager_assignments}; "
            f"Valid={valid_manager_refs}; "
            f"Broken={len(broken_manager_refs)}"
        )

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
