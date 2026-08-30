import json
import os

from pymongo import MongoClient


url = os.environ.get("MONGODB_URL", "mongodb://127.0.0.1:27017")
db_name = os.environ.get("DATABASE_NAME", "workforce_db_test")

client = MongoClient(url, serverSelectionTimeoutMS=5000)
try:
    client.admin.command("ping")
except Exception as exc:
    print(f"MONGO_CONNECTION_ERROR: {exc}")
    raise SystemExit(1)

collection = client[db_name].get_collection("leaves")

for raw_doc in collection.find({}):
    doc = {key: value for key, value in raw_doc.items() if key != "_id"}
    for canonical, aliases in {
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
    }.items():
        if canonical in doc:
            continue
        for alias in aliases:
            if alias in doc:
                doc[canonical] = doc.pop(alias)
                break
    print(json.dumps(doc, default=str, sort_keys=True))
