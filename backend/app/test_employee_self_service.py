import os

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))

from backend.app.config import settings
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run Step 3 self-service tests: DATABASE_NAME must be exactly 'workforce_db_test'."
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


def test_employee_can_retrieve_own_profile():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/profile", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload.get("empId") == EMPLOYEE_ID


def test_employee_cannot_access_another_employee_profile():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/employees/{OTHER_EMPLOYEE_ID}", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_retrieve_own_employee_record():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/employees/{EMPLOYEE_ID}", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload.get("empId") == EMPLOYEE_ID


def test_employee_cannot_access_another_employee_record():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/employees/{OTHER_EMPLOYEE_ID}", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_retrieve_own_attendance():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/attendance?page=1&size=50", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        items = payload.get("items", [])
        assert any(item.get("empId") == EMPLOYEE_ID for item in items)


def test_employee_cannot_access_another_employee_attendance():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/attendance?department=Engineering&page=1&size=50", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        items = payload.get("items", [])
        assert all(item.get("empId") == EMPLOYEE_ID for item in items)


def test_employee_cannot_manipulate_attendance_empid():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "empId": OTHER_EMPLOYEE_ID,
            "date": "2026-08-18",
            "checkIn": "09:00",
            "checkOut": "17:00",
            "workingHours": 8.0,
            "status": "Present"
        }
        response = client.post("/api/attendance/check-in", headers=headers, json=payload)
        assert response.status_code == 403, response.text


def test_employee_can_access_own_permitted_payroll():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/payroll?month=2023-05&page=1&size=10", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload, list)
        assert all(item.get("empId") == EMPLOYEE_ID for item in payload)


def test_employee_cannot_access_another_employee_payroll():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/payroll/{OTHER_EMPLOYEE_ID}/payslip", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_access_own_permitted_performance():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/performance/{EMPLOYEE_ID}", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload.get("empId") == EMPLOYEE_ID


def test_employee_cannot_access_another_employee_performance():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/performance/{OTHER_EMPLOYEE_ID}", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_can_access_own_timesheets():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/timesheets?emp_id={EMPLOYEE_ID}&page=1&size=10", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload, list)
        assert all(item.get("empId") == EMPLOYEE_ID for item in payload)


def test_employee_cannot_access_another_employee_timesheets():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/timesheets?emp_id={OTHER_EMPLOYEE_ID}&page=1&size=10", headers=headers)
        assert response.status_code == 403, response.text


def test_employee_cannot_access_another_employee_notifications():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/notifications", headers=headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert all(item.get("empId", EMPLOYEE_ID) == EMPLOYEE_ID for item in payload)


def test_employee_cannot_perform_hr_only_operation():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/settings", headers=headers).status_code == 403
        assert client.get("/api/reports/summary", headers=headers).status_code == 403


def test_hr_admin_can_access_authorized_employee_information():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get(f"/api/employees/{EMPLOYEE_ID}", headers=headers).status_code == 200
        assert client.get("/api/settings", headers=headers).status_code == 200


def test_unauthenticated_protected_requests_return_401():
    with TestClient(app) as client:
        assert client.get("/api/profile").status_code == 401
        assert client.get(f"/api/employees/{EMPLOYEE_ID}").status_code == 401
        assert client.get("/api/attendance").status_code == 401
        assert client.get("/api/payroll").status_code == 401
        assert client.get(f"/api/performance/{EMPLOYEE_ID}").status_code == 401
