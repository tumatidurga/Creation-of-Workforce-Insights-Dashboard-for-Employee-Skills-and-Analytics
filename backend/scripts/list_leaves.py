import json
import os

from pymongo import MongoClient


MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://127.0.0.1:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "workforce_db_test")


def normalize_leave(doc):
    if not isinstance(doc, dict):
        return doc

    normalized = {key: value for key, value in doc.items() if key != "_id"}
    legacy_aliases = {
        "empId": ["EmpID", "emp_id"],
        "empName": ["EmployeeName", "employeeName", "fullName"],
        "department": ["Department"],
        "leaveType": ["LeaveType", "type"],
        "startDate": ["StartDate", "start_date"],
        "endDate": ["EndDate", "end_date"],
        "days": ["Days", "dayCount"],
        "reason": ["Reason"],
        "status": ["Status"],
        "appliedOn": ["AppliedOn", "applied_on"],
        "approverComments": ["ApproverComments", "approver_comments"],
        "leaveBalance": ["LeaveBalance", "leave_balance"],
    }

    for canonical, aliases in legacy_aliases.items():
        if canonical in normalized:
            continue
        for alias in aliases:
            if alias in normalized:
                normalized[canonical] = normalized.pop(alias)
                break

    return normalized


def list_leaves():
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        print(f"MONGO_CONNECTION_ERROR: {exc}")
        raise SystemExit(1)

    db = client[DATABASE_NAME]
    collection = db.get_collection("leaves")
    leaves = list(collection.find({}))

    if not leaves:
        print("No leaves found in the database.")
        return

    for doc in leaves:
        print(json.dumps(normalize_leave(doc), default=str, sort_keys=True))


if __name__ == "__main__":
    list_leaves()
