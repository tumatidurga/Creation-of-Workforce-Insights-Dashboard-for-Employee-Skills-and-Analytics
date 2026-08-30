import asyncio
import json
import os
import sys
# Ensure repository root is on sys.path so 'backend' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.database import connect_to_mongo, get_database, close_mongo_connection
from backend.app.services.workforce_services import AuditService, normalize_audit_log, EmployeeService

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print(json.dumps({"error": "db_connect_failed", "detail": str(e)}))
        return

    db = get_database()
    if db is None:
        print(json.dumps({"error": "no_db_instance"}))
        return

    # Inspect raw audit documents
    raw_docs = await db.audit_logs.find().to_list(length=None)
    total = len(raw_docs)
    missing_id_count = 0
    null_id_count = 0
    empty_id_count = 0
    explicit_id_count = 0
    normalized_ids = []

    for doc in raw_docs:
        has_id_key = 'id' in doc
        id_val = doc.get('id', None)
        if not has_id_key:
            missing_id_count += 1
        else:
            if id_val is None:
                null_id_count += 1
            elif isinstance(id_val, str) and id_val.strip() == '':
                empty_id_count += 1
            else:
                explicit_id_count += 1
        norm = normalize_audit_log(doc)
        normalized_ids.append(norm.get('id'))

    unique_normalized = len(set([i for i in normalized_ids if i is not None]))

    # Use AuditService.get_all to verify normalized list returned to API
    try:
        api_items = await AuditService.get_all()
    except Exception as e:
        api_items = None
        api_error = str(e)
    else:
        api_error = None

    # EmployeeService test
    try:
        emp_items, emp_total = await EmployeeService.get_all()
    except Exception as e:
        emp_error = str(e)
        emp_items = None
        emp_total = None

    # Inspect hr-admin user account
    ua = await db.user_accounts.find_one({"userId": "hr-admin"}, {"_id": 0, "userId":1, "empId":1, "email":1, "role":1, "status":1, "passwordHash":1})
    hr_account = None
    if ua:
        hr_account = {
            "userId": ua.get("userId"),
            "empId": ua.get("empId"),
            "email": ua.get("email"),
            "role": ua.get("role"),
            "status": ua.get("status"),
            "hasPasswordHash": bool(ua.get("passwordHash"))
        }

    output = {
        "audit_total": total,
        "audit_missing_id": missing_id_count,
        "audit_null_id": null_id_count,
        "audit_empty_id": empty_id_count,
        "audit_explicit_id": explicit_id_count,
        "audit_normalized_unique_ids": unique_normalized,
        "api_items_returned": len(api_items) if api_items is not None else None,
        "api_error": api_error,
        "employee_service_result_count": emp_total,
        "employee_service_returned_items_sample": (emp_items[:3] if emp_items else None),
        "hr_account": hr_account
    }

    print(json.dumps(output, indent=2))

    await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
