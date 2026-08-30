import asyncio
import os

from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.config import settings
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run notification workflow tests: DATABASE_NAME must be exactly 'workforce_db_test'."
    )


def _login(client, identifier, password):
    response = client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def _db():
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    return client[settings.DATABASE_NAME]


def _fetch_notifications(query):
    async def _op():
        db = _db()
        cursor = db.notifications.find(query)
        return await cursor.to_list(length=None)

    return asyncio.run(_op())


def test_employee_leave_request_notifies_hr_and_reporting_manager():
    with TestClient(app) as client:
        emp_token = _login(client, "EMP000001", os.environ.get("EMPLOYEE_TEST_PASSWORD", "EMP000001"))
        emp_headers = {"Authorization": f"Bearer {emp_token}"}

        leave_payload = {
            "empId": "EMP000001",
            "leaveType": "Casual",
            "startDate": "2041-12-10",
            "endDate": "2041-12-12",
            "leaveBalance": 3,
            "status": "Pending",
        }
        response = client.post("/api/leaves", headers=emp_headers, json=leave_payload)
        assert response.status_code == 201, response.text
        created = response.json()
        leave_id = created["id"]

        notifications = _fetch_notifications({"relatedEntityType": "leave", "relatedEntityId": str(leave_id)})
        assert len(notifications) == 2, notifications

        recipients = {
            doc.get("recipientUserId") or doc.get("EmpID")
            for doc in notifications
            if doc.get("recipientUserId") or doc.get("EmpID")
        }
        assert "hr-admin" in recipients
        assert "EMP010010" in recipients
        assert "EMP000001" not in recipients

        for doc in notifications:
            assert doc.get("notificationType") == "leave_request_submitted"
            assert doc.get("Status") in {"Unread", "unread"}
            assert doc.get("isRead") is False

        manager_docs = _fetch_notifications({"relatedEntityType": "leave", "relatedEntityId": str(leave_id), "EmpID": "EMP010020"})
        assert manager_docs == []


def test_hr_leave_approval_notifies_employee_once():
    with TestClient(app) as client:
        emp_token = _login(client, "EMP000001", os.environ.get("EMPLOYEE_TEST_PASSWORD", "EMP000001"))
        hr_token = _login(client, "hr-admin", os.environ.get("HR_ADMIN_TEST_PASSWORD", "hr-bootstrap-test-password"))

        leave_payload = {
            "empId": "EMP000001",
            "leaveType": "Sick",
            "startDate": "2042-01-05",
            "endDate": "2042-01-07",
            "leaveBalance": 3,
            "status": "Pending",
        }
        created = client.post("/api/leaves", headers={"Authorization": f"Bearer {emp_token}"}, json=leave_payload)
        assert created.status_code == 201, created.text
        leave_id = created.json()["id"]

        approval = client.put(
            f"/api/leaves/{leave_id}/status",
            headers={"Authorization": f"Bearer {hr_token}"},
            json={"status": "Approved", "approverComments": "Approved after review"},
        )
        assert approval.status_code == 200, approval.text

        employee_notifications = _fetch_notifications({
            "EmpID": "EMP000001",
            "notificationType": "leave_request_approved",
            "relatedEntityId": str(leave_id),
        })
        assert len(employee_notifications) == 1, employee_notifications
        note = employee_notifications[0]
        assert note.get("Status") in {"Read", "Unread"}
        assert note.get("metadata", {}).get("requestId") == str(leave_id)
        assert note.get("actorName") or note.get("actorUserId")
        assert note.get("metadata", {}).get("status") == "Approved"


def test_manager_shift_rejection_notifies_employee_once():
    with TestClient(app) as client:
        emp_token = _login(client, "EMP000001", os.environ.get("EMPLOYEE_TEST_PASSWORD", "EMP000001"))
        manager_token = _login(client, "EMP010010", "ManagerOne123")

        shift_payload = {
            "empId": "EMP000001",
            "requestedShift": "Night (22:00 - 07:00)",
            "requestedDate": "2042-02-15",
            "reason": "Need a different shift",
            "status": "Pending",
        }
        created = client.post("/api/shifts", headers={"Authorization": f"Bearer {emp_token}"}, json=shift_payload)
        assert created.status_code == 201, created.text
        shift_id = created.json()["id"]

        submission_notifications = _fetch_notifications({
            "relatedEntityType": "shift",
            "relatedEntityId": str(shift_id),
        })
        assert len(submission_notifications) == 2, submission_notifications

        rejection = client.put(
            f"/api/shifts/{shift_id}/status",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"status": "Rejected", "approverComments": "Shift not available"},
        )
        assert rejection.status_code == 200, rejection.text

        employee_notifications = _fetch_notifications({
            "EmpID": "EMP000001",
            "notificationType": "shift_request_rejected",
            "relatedEntityId": str(shift_id),
        })
        assert len(employee_notifications) == 1, employee_notifications
        note = employee_notifications[0]
        assert note.get("metadata", {}).get("status") == "Rejected"
        assert "Shift not available" in str(note.get("metadata", {}).get("approverComments") or note.get("message") or "")


def test_notifications_are_scoped_to_authenticated_user():
    with TestClient(app) as client:
        emp_token = _login(client, "EMP000001", os.environ.get("EMPLOYEE_TEST_PASSWORD", "EMP000001"))
        hr_token = _login(client, "hr-admin", os.environ.get("HR_ADMIN_TEST_PASSWORD", "hr-bootstrap-test-password"))

        response = client.get("/api/notifications", headers={"Authorization": f"Bearer {emp_token}"})
        assert response.status_code == 200, response.text
        emp_items = response.json()
        assert all(item.get("empId") == "EMP000001" or item.get("recipientUserId") == "EMP000001" for item in emp_items if item.get("empId") or item.get("recipientUserId"))

        hr_response = client.get("/api/notifications", headers={"Authorization": f"Bearer {hr_token}"})
        assert hr_response.status_code == 200, hr_response.text
        hr_items = hr_response.json()
        assert all(item.get("recipientUserId") == "hr-admin" or not item.get("recipientUserId") for item in hr_items)

        first_item = emp_items[0] if emp_items else None
        if first_item:
            read_response = client.put(f"/api/notifications/{first_item['id']}/read", headers={"Authorization": f"Bearer {emp_token}"})
            assert read_response.status_code == 200, read_response.text

            forbidden = client.put(f"/api/notifications/{first_item['id']}/read", headers={"Authorization": f"Bearer {hr_token}"})
            assert forbidden.status_code == 403, forbidden.text


def test_legacy_notification_documents_still_read_without_new_fields():
    with TestClient(app) as client:
        emp_token = _login(client, "EMP000001", os.environ.get("EMPLOYEE_TEST_PASSWORD", "EMP000001"))
        legacy_id = "LEGACY-EMP000001-NOTICE-1"

        async def _insert_legacy():
            db = _db()
            await db.notifications.insert_one({
                "id": legacy_id,
                "EmpID": "EMP000001",
                "Type": "Attendance",
                "Message": "Legacy attendance alert",
                "Status": "Unread",
                "NotificationDate": "2026-01-01",
            })

        asyncio.run(_insert_legacy())

        response = client.get("/api/notifications", headers={"Authorization": f"Bearer {emp_token}"})
        assert response.status_code == 200, response.text
        payload = response.json()
        legacy = next((item for item in payload if item.get("id") == legacy_id), None)
        assert legacy is not None, payload
        assert legacy.get("notificationType") in {"Attendance", None}
        assert legacy.get("isRead") in {False, None}

        read_resp = client.put(f"/api/notifications/{legacy_id}/read", headers={"Authorization": f"Bearer {emp_token}"})
        assert read_resp.status_code == 200, read_resp.text
