import os
from contextlib import contextmanager

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))

from backend.app.config import settings
from backend.app.main import app

if not getattr(settings, "DATABASE_NAME", None) or not settings.DATABASE_NAME.endswith("_test"):
    raise RuntimeError(
        "Refusing to run Step 2 authorization tests: DATABASE_NAME must point to workforce_db_test."
    )

EMPLOYEE_ID = "EMP000001"
OTHER_EMPLOYEE_ID = "EMP000002"
HR_EMAIL = "priya.sharma@enterprise.com"
MANAGER_ONE_ID = "EMP010010"
MANAGER_TWO_ID = "EMP010020"
MANAGER_LOGIN_ID = "MGR000001"
MANAGER_TWO_LOGIN_ID = "MGR000002"
TEAM_MEMBER_ONE_ID = "EMP010011"
TEAM_MEMBER_TWO_ID = "EMP010012"
OTHER_MANAGER_MEMBER_ID = "EMP010021"


def _get_test_passwords():
    hr_pw = os.environ.get("HR_ADMIN_TEST_PASSWORD") or "hr-bootstrap-test-password"
    emp_pw = os.environ.get("EMPLOYEE_TEST_PASSWORD") or "EMP000001"
    manager_one_pw = os.environ.get("MANAGER_ONE_TEST_PASSWORD") or "ManagerOne123"
    manager_two_pw = os.environ.get("MANAGER_TWO_TEST_PASSWORD") or "ManagerTwo123"
    return {
        "HR_ADMIN_TEST_PASSWORD": hr_pw,
        "EMPLOYEE_TEST_PASSWORD": emp_pw,
        "MANAGER_ONE_TEST_PASSWORD": manager_one_pw,
        "MANAGER_TWO_TEST_PASSWORD": manager_two_pw,
    }


@contextmanager
def client_session():
    with TestClient(app) as client:
        yield client


def _login(client, identifier, password):
    response = client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_unauthenticated_access_to_protected_endpoints():
    with client_session() as client:
        assert client.get("/api/employees/EMP000001").status_code == 401
        assert client.get("/api/payroll/EMP000001/payslip").status_code == 401
        assert client.get("/api/performance/EMP000001").status_code == 401
        assert client.get("/api/reports/summary").status_code == 401
        assert client.get("/api/settings").status_code == 401


def test_employee_accesses_own_permitted_resources():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/employees/EMP000001", headers=headers).status_code == 200
        assert client.get("/api/payroll/EMP000001/payslip", headers=headers).status_code == 200
        assert client.get("/api/performance/EMP000001", headers=headers).status_code == 200
        assert client.get("/api/attendance?page=1&size=50", headers=headers).status_code == 200


def test_employee_cannot_access_another_employees_resources():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get(f"/api/employees/{OTHER_EMPLOYEE_ID}", headers=headers).status_code == 403
        assert client.get(f"/api/payroll/{OTHER_EMPLOYEE_ID}/payslip", headers=headers).status_code == 403
        assert client.get(f"/api/performance/{OTHER_EMPLOYEE_ID}", headers=headers).status_code == 403
        assert client.get("/api/reports/summary", headers=headers).status_code == 403


def test_employee_cannot_perform_hr_admin_operation():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/reports/summary", headers=headers).status_code == 403
        assert client.get("/api/settings", headers=headers).status_code == 403
        assert client.post("/api/notifications", headers=headers, json={"title": "Test", "message": "Denied"}).status_code == 403


def test_hr_admin_can_access_permitted_employee_data():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get(f"/api/employees/{EMPLOYEE_ID}", headers=headers).status_code == 200
        assert client.get("/api/payroll?month=2023-05&page=1&size=10", headers=headers).status_code == 200
        assert client.get("/api/performance", headers=headers).status_code == 200
        assert client.get("/api/reports/summary", headers=headers).status_code == 200


def test_hr_admin_can_perform_permitted_administrative_operations():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/settings", headers=headers).status_code == 200
        response = client.post(
            "/api/notifications",
            headers=headers,
            json={"empId": EMPLOYEE_ID, "title": "Role check", "message": "Authorized", "type": "Attendance", "status": "Unread", "priority": "Medium"},
        )
        assert response.status_code in (200, 201), response.text


def test_manager_login_receives_manager_role_and_can_view_team():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, MANAGER_LOGIN_ID, creds["MANAGER_ONE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["role"] == "MANAGER"
        assert me.json()["empId"] == MANAGER_ONE_ID
        assert me.json()["managerLoginId"] == MANAGER_LOGIN_ID

        team_response = client.get("/api/employees?size=100", headers=headers)
        assert team_response.status_code == 200, team_response.text
        team_ids = {emp["empId"] for emp in team_response.json()["items"]}
        assert MANAGER_ONE_ID in team_ids
        assert TEAM_MEMBER_ONE_ID in team_ids
        assert TEAM_MEMBER_TWO_ID in team_ids
        assert OTHER_MANAGER_MEMBER_ID not in team_ids


def test_manager_can_login_with_email_and_real_empid_is_preserved():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, "sonia.mehta.10@company.com", creds["MANAGER_ONE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["empId"] == MANAGER_ONE_ID
        assert me.json()["role"] == "MANAGER"
        assert me.json()["managerLoginId"] == MANAGER_LOGIN_ID


def test_manager_cannot_access_another_managers_team_member():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, MANAGER_ONE_ID, creds["MANAGER_ONE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/employees/{OTHER_MANAGER_MEMBER_ID}", headers=headers)
        assert response.status_code == 403, response.text

        team_response = client.get("/api/employees?size=100", headers=headers)
        assert team_response.status_code == 200, team_response.text
        returned_ids = {emp["empId"] for emp in team_response.json()["items"]}
        assert OTHER_MANAGER_MEMBER_ID not in returned_ids


def test_employee_path_query_and_body_empid_tampering_is_rejected():
    creds = _get_test_passwords()
    with client_session() as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}

        assert client.get(f"/api/employees/{OTHER_EMPLOYEE_ID}", headers=headers).status_code == 403
        assert client.get(f"/api/timesheets?emp_id={OTHER_EMPLOYEE_ID}&page=1&size=10", headers=headers).status_code == 403

        payload = {
            "empId": OTHER_EMPLOYEE_ID,
            "date": "2026-08-18",
            "projectName": "Payroll Automation",
            "taskDescription": "Tamper check",
            "hoursLogged": 1.0,
            "status": "Submitted"
        }
        response = client.post("/api/timesheets", headers=headers, json=payload)
        assert response.status_code == 403


def test_valid_authenticated_requests_continue_working():
    creds = _get_test_passwords()
    with client_session() as client:
        employee_token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        employee_headers = {"Authorization": f"Bearer {employee_token}"}
        assert client.get("/api/auth/me", headers=employee_headers).status_code == 200
        assert client.get("/api/profile", headers=employee_headers).status_code == 200

        hr_token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        hr_headers = {"Authorization": f"Bearer {hr_token}"}
        assert client.get("/api/auth/me", headers=hr_headers).status_code == 200
        assert client.get("/api/attendance/anomalies", headers=hr_headers).status_code == 200
