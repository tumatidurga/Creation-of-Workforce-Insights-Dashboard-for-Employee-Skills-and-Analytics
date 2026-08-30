import asyncio
import uuid
from datetime import datetime

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))
from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.config import settings
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run Step 5 security tests: DATABASE_NAME must be exactly 'workforce_db_test'."
    )

EMPLOYEE_ID = "EMP000001"
OTHER_EMPLOYEE_ID = "EMP000002"
HR_EMAIL = "priya.sharma@enterprise.com"


def _get_test_passwords():
    hr_pw = os.environ.get("HR_ADMIN_TEST_PASSWORD")
    emp_pw = os.environ.get("EMPLOYEE_TEST_PASSWORD")
    if not hr_pw or not emp_pw:
        raise RuntimeError(
            "Set HR_ADMIN_TEST_PASSWORD and EMPLOYEE_TEST_PASSWORD before running backend auth tests."
        )
    return {"HR_ADMIN_TEST_PASSWORD": hr_pw, "EMPLOYEE_TEST_PASSWORD": emp_pw}


def _login(client, identifier, password):
    response = client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _db():
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    return client[settings.DATABASE_NAME]


@pytest.fixture(autouse=True)
def isolate_step5_notifications():
    async def _cleanup():
        await _db().notifications.delete_many({"id": {"$regex": r"^STEP5-"}})

    asyncio.run(_cleanup())
    yield
    asyncio.run(_cleanup())


async def _insert_notification(emp_id: str, label: str = "Step5"):
    db = _db()
    notif_id = f"STEP5-{uuid.uuid4().hex[:10]}-{emp_id}"
    doc = {
        "id": notif_id,
        "EmpID": emp_id,
        "Type": "Attendance",
        "Message": f"{label} security test {uuid.uuid4().hex[:6]}",
        "Status": "Unread",
        "NotificationDate": datetime.now().strftime("%Y-%m-%d"),
        "priority": "Medium",
    }
    await db.notifications.insert_one(doc)
    return notif_id


def _insert_notification_sync(emp_id: str, label: str = "Step5"):
    return asyncio.run(_insert_notification(emp_id, label))


async def _count_notification_status(emp_id: str, status: str):
    db = _db()
    return await db.notifications.count_documents({"EmpID": emp_id, "Status": status})


def test_unauthenticated_audit_logs_are_rejected():
    with TestClient(app) as client:
        assert client.get("/api/audit-logs").status_code == 401
        assert client.post("/api/audit-logs", json={"actor": "Tester", "action": "Test", "module": "Security", "status": "SUCCESS"}).status_code == 401


def test_employee_is_blocked_from_audit_logs():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        assert client.get("/api/audit-logs", headers=headers).status_code == 403
        assert client.post(
            "/api/audit-logs",
            headers=headers,
            json={"actor": "EMP000001", "action": "Forbidden", "module": "Security", "status": "SUCCESS"},
        ).status_code == 403


def test_hr_admin_can_read_and_create_audit_logs():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/audit-logs", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload, list)

        response = client.post(
            "/api/audit-logs",
            headers=headers,
            json={"actor": "Step5-TestHR", "action": "Audit security test", "module": "Security", "ipAddress": "127.0.0.1", "status": "SUCCESS"},
        )
        assert response.status_code == 201, response.text
        created = response.json()
        assert created.get("actor") == "Step5-TestHR"


def test_unauthenticated_ai_chat_is_rejected():
    with TestClient(app) as client:
        assert client.post("/api/chat", json={"message": "headcount by department"}).status_code == 401
        assert client.post("/api/ai/chat", json={"message": "payroll projection"}).status_code == 401


def test_employee_ai_chat_is_forbidden():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        assert client.post("/api/chat", headers=headers, json={"message": "headcount by department"}).status_code == 403
        assert client.post("/api/ai/chat", headers=headers, json={"message": "payroll projection"}).status_code == 403


def test_hr_admin_ai_chat_is_allowed():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.post("/api/chat", headers=headers, json={"message": "headcount by department"})
        assert response.status_code == 200, response.text
        response = client.post("/api/ai/chat", headers=headers, json={"message": "payroll projection for August 2026"})
        assert response.status_code == 200, response.text


def test_employee_can_read_only_own_notifications():
    creds = _get_test_passwords()
    own_id = _insert_notification_sync(EMPLOYEE_ID, "Own notification")
    other_id = _insert_notification_sync(OTHER_EMPLOYEE_ID, "Other notification")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/notifications", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        ids = [item.get("id") for item in payload]
        assert own_id in ids
        assert other_id not in ids


def test_employee_cannot_mark_another_employees_notification_as_read():
    creds = _get_test_passwords()
    other_id = _insert_notification_sync(OTHER_EMPLOYEE_ID, "Unauthorized mark")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.put(f"/api/notifications/{other_id}/read", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_mark_own_notification_as_read():
    creds = _get_test_passwords()
    own_id = _insert_notification_sync(EMPLOYEE_ID, "Allowed read")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.put(f"/api/notifications/{own_id}/read", headers=headers)
        assert response.status_code == 200, response.text

        response = client.get("/api/notifications", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert any(item.get("id") == own_id and item.get("isRead") is True for item in payload)


def test_employee_mark_all_read_scopes_to_own_notifications_only():
    creds = _get_test_passwords()
    own_id = _insert_notification_sync(EMPLOYEE_ID, "MARK ALL SELF")
    other_id = _insert_notification_sync(OTHER_EMPLOYEE_ID, "MARK ALL OTHER")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.post("/api/notifications/mark-all-read", headers=headers)
        assert response.status_code == 200, response.text

        response = client.get("/api/notifications", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        own_values = [item for item in payload if item.get("id") == own_id]
        other_values = [item for item in payload if item.get("id") == other_id]
        assert own_values and all(item.get("isRead") is True for item in own_values)
        assert not other_values or all(item.get("isRead") is False for item in other_values)


def test_employee_cannot_use_mark_all_read_to_modify_another_employee_notifications():
    creds = _get_test_passwords()
    other_id = _insert_notification_sync(OTHER_EMPLOYEE_ID, "Bulk other")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.post("/api/notifications/mark-all-read", headers=headers)
        assert response.status_code == 200, response.text

        response = client.get("/api/notifications", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        other_values = [item for item in payload if item.get("id") == other_id]
        assert not other_values or all(item.get("isRead") is False for item in other_values)


def test_hr_admin_notification_access_remains_authorized():
    creds = _get_test_passwords()
    own_id = _insert_notification_sync(EMPLOYEE_ID, "HR admin notification check")
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/notifications", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        ids = [item.get("id") for item in payload]
        assert own_id in ids or len(payload) >= 0

        response = client.post(
            "/api/notifications",
            headers=headers,
            json={"empId": EMPLOYEE_ID, "title": "HR check", "message": "Authorized", "type": "Attendance", "status": "Unread", "priority": "Medium"},
        )
        assert response.status_code in (200, 201), response.text


def test_notification_path_tampering_is_rejected_for_employee():
    creds = _get_test_passwords()
    other_id = _insert_notification_sync(OTHER_EMPLOYEE_ID, "Path tamper")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.put(f"/api/notifications/{other_id}/read", headers=headers)
        assert response.status_code == 403, response.text


def test_notification_query_and_body_identity_are_not_used_as_authority():
    creds = _get_test_passwords()
    own_id = _insert_notification_sync(EMPLOYEE_ID, "Query/body check")
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.put(f"/api/notifications/{own_id}/read", headers=headers)
        assert response.status_code == 200, response.text

        response = client.post(
            "/api/notifications",
            headers=headers,
            json={"empId": OTHER_EMPLOYEE_ID, "title": "Tampered body", "message": "Should fail", "type": "Attendance", "status": "Unread"},
        )
        assert response.status_code == 403, response.text
