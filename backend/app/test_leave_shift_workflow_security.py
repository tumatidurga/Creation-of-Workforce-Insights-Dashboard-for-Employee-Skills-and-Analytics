import asyncio
from datetime import datetime, timedelta

import os

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))
from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.config import settings
from backend.app.database import get_database
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run Step 4 leave/shift workflow tests: DATABASE_NAME must be exactly 'workforce_db_test'."
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
    db = client[settings.DATABASE_NAME]
    return db


def _create_leave_record(emp_id, start_date, end_date, status="Pending"):
    async def _op():
        db = _db()
        record = {
            "EmpID": emp_id,
            "LeaveType": "Casual",
            "StartDate": start_date,
            "EndDate": end_date,
            "Status": status,
            "LeaveBalance": 3,
            "days": (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1,
        }
        result = await db.leaves.insert_one(record)
        return str(result.inserted_id)

    return asyncio.run(_op())


def _create_shift_record(emp_id, requested_date, shift_name="Night", shift_start="22:00", shift_end="07:00"):
    async def _op():
        db = _db()
        shift_id = f"SH-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        record = {
            "EmpID": emp_id,
            "ShiftName": shift_name,
            "ShiftStart": shift_start,
            "ShiftEnd": shift_end,
            "OvertimeHours": 0.0,
            "ShiftSwapApproved": False,
            "ShiftDate": requested_date,
            "ShiftID": shift_id,
            "ShiftSwapStatus": "Pending",
            "Reason": "Workflow security test",
            "AppliedOn": datetime.now().strftime("%Y-%m-%d"),
        }
        await db.shifts.insert_one(record)
        return shift_id

    return asyncio.run(_op())


def test_leave_unauthenticated_access_is_rejected():
    with TestClient(app) as client:
        assert client.get("/api/leaves").status_code == 401
        assert client.put("/api/leaves/invalid-id/status", json={"status": "Approved"}).status_code == 401
        assert client.get("/api/shifts").status_code == 401


def test_employee_can_view_own_leave_requests():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/leaves?page=1&size=25", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload, list)
        assert all(item.get("empId") == EMPLOYEE_ID for item in payload)


def test_employee_cannot_view_another_employee_leave():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get(f"/api/leaves?emp_id={OTHER_EMPLOYEE_ID}&page=1&size=25", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_query_empid_tampering_is_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get(f"/api/shifts?emp_id={OTHER_EMPLOYEE_ID}&page=1&size=25", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_submit_own_leave():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": EMPLOYEE_ID,
            "leaveType": "Casual",
            "startDate": "2041-04-10",
            "endDate": "2041-04-12",
            "leaveBalance": 3,
            "status": "Pending",
        }
        response = client.post("/api/leaves", headers=headers, json=payload)
        assert response.status_code == 201, response.text
        created = response.json()
        assert created.get("empId") == EMPLOYEE_ID
        assert created.get("status") == "Pending"


def test_employee_cannot_submit_leave_for_another_employee():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": OTHER_EMPLOYEE_ID,
            "leaveType": "Casual",
            "startDate": "2036-05-10",
            "endDate": "2036-05-12",
            "leaveBalance": 3,
            "status": "Pending",
        }
        response = client.post("/api/leaves", headers=headers, json=payload)
        assert response.status_code == 403, response.text


def test_employee_cannot_manipulate_leave_status():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": EMPLOYEE_ID,
            "leaveType": "Casual",
            "startDate": "2036-06-10",
            "endDate": "2036-06-12",
            "leaveBalance": 3,
            "status": "Approved",
        }
        response = client.post("/api/leaves", headers=headers, json=payload)
        assert response.status_code == 400, response.text


def test_invalid_leave_dates_are_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": EMPLOYEE_ID,
            "leaveType": "Sick",
            "startDate": "2036-07-15",
            "endDate": "2036-07-10",
            "leaveBalance": 3,
            "status": "Pending",
        }
        response = client.post("/api/leaves", headers=headers, json=payload)
        assert response.status_code == 400, response.text


def test_overlapping_leave_is_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        first = {
            "empId": EMPLOYEE_ID,
            "leaveType": "Casual",
            "startDate": "2041-08-01",
            "endDate": "2041-08-04",
            "leaveBalance": 3,
            "status": "Pending",
        }
        response1 = client.post("/api/leaves", headers=headers, json=first)
        assert response1.status_code == 201, response1.text

        overlap = {
            "empId": EMPLOYEE_ID,
            "leaveType": "Casual",
            "startDate": "2041-08-03",
            "endDate": "2041-08-06",
            "leaveBalance": 3,
            "status": "Pending",
        }
        response2 = client.post("/api/leaves", headers=headers, json=overlap)
        assert response2.status_code == 400, response2.text


def test_employee_cannot_approve_or_reject_leave():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        other_leave_id = _create_leave_record(OTHER_EMPLOYEE_ID, "2036-09-10", "2036-09-12", "Pending")
        response = client.put(f"/api/leaves/{other_leave_id}/status", headers=headers, json={"status": "Approved"})
        assert response.status_code == 403, response.text


def test_hr_admin_can_view_leave_requests():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/leaves?page=1&size=25", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload, list)


def test_hr_admin_can_approve_leave():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        employee_token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        employee_headers = _headers(employee_token)
        created = client.post(
            "/api/leaves",
            headers=employee_headers,
            json={
                "empId": EMPLOYEE_ID,
                "leaveType": "Casual",
                "startDate": "2041-10-01",
                "endDate": "2041-10-02",
                "leaveBalance": 3,
                "status": "Pending",
            },
        )
        assert created.status_code == 201, created.text
        leave_id = created.json().get("id")

        hr_token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        hr_headers = _headers(hr_token)
        response = client.put(
            f"/api/leaves/{leave_id}/status",
            headers=hr_headers,
            json={"status": "Approved", "approverComments": "Approved by test"},
        )
        assert response.status_code == 200, response.text
        assert response.json().get("status") == "Approved"


def test_employee_can_view_own_shift_requests():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/shifts?page=1&size=25", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload, list)
        assert all(item.get("empId") == EMPLOYEE_ID for item in payload)


def test_employee_cannot_view_another_employee_shift_requests():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get(f"/api/shifts?emp_id={OTHER_EMPLOYEE_ID}&page=1&size=25", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_submit_own_shift_request():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": EMPLOYEE_ID,
            "requestedShift": "Night (22:00 - 07:00)",
            "requestedDate": "2036-11-20",
            "reason": "Test shift request",
        }
        response = client.post("/api/shifts", headers=headers, json=payload)
        assert response.status_code == 201, response.text
        created = response.json()
        assert created.get("empId") == EMPLOYEE_ID
        assert created.get("status") == "Pending"


def test_employee_cannot_submit_shift_request_for_another_employee():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": OTHER_EMPLOYEE_ID,
            "requestedShift": "Night (22:00 - 07:00)",
            "requestedDate": "2036-11-21",
            "reason": "Should fail",
        }
        response = client.post("/api/shifts", headers=headers, json=payload)
        assert response.status_code == 403, response.text


def test_employee_cannot_approve_or_reject_shift_request():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        other_shift_id = _create_shift_record(OTHER_EMPLOYEE_ID, "2036-12-15")
        response = client.put(f"/api/shifts/{other_shift_id}/status", headers=headers, json={"status": "Approved"})
        assert response.status_code == 403, response.text


def test_hr_admin_can_manage_shift_requests():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        employee_token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        employee_headers = _headers(employee_token)
        created = client.post(
            "/api/shifts",
            headers=employee_headers,
            json={
                "empId": EMPLOYEE_ID,
                "requestedShift": "Morning (07:00 - 16:00)",
                "requestedDate": "2036-12-18",
                "reason": "Approved by HR test",
            },
        )
        assert created.status_code == 201, created.text
        shift_id = created.json().get("id")

        hr_token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        hr_headers = _headers(hr_token)
        response = client.put(
            f"/api/shifts/{shift_id}/status",
            headers=hr_headers,
            json={"status": "Approved"},
        )
        assert response.status_code == 200, response.text
        assert response.json().get("status") == "Approved"


def test_employee_cannot_manipulate_shift_empid():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        payload = {
            "empId": OTHER_EMPLOYEE_ID,
            "requestedShift": "Night (22:00 - 07:00)",
            "requestedDate": "2036-12-22",
            "reason": "Tamper",
        }
        response = client.post("/api/shifts", headers=headers, json=payload)
        assert response.status_code == 403, response.text


def test_leave_resource_id_substitution_is_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        other_leave_id = _create_leave_record(OTHER_EMPLOYEE_ID, "2036-12-29", "2036-12-30")
        response = client.put(f"/api/leaves/{other_leave_id}/status", headers=headers, json={"status": "Rejected"})
        assert response.status_code == 403, response.text


def test_shift_resource_id_substitution_is_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        other_shift_id = _create_shift_record(OTHER_EMPLOYEE_ID, "2037-01-02")
        response = client.put(f"/api/shifts/{other_shift_id}/status", headers=headers, json={"status": "Rejected"})
        assert response.status_code == 403, response.text
