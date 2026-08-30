import asyncio
from datetime import datetime

import os

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))
from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.config import settings
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run Step 6 bulk export tests: DATABASE_NAME must be exactly 'workforce_db_test'."
    )

EMPLOYEE_ID = "EMP000001"
OTHER_EMPLOYEE_ID = "EMP000002"
HR_EMAIL = "priya.sharma@enterprise.com"
VALID_DEPARTMENT = "Engineering"


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


async def _find_latest_audit(pattern: str):
    db = _db()
    return await db.audit_logs.find_one({"action": {"$regex": pattern, "$options": "i"}}, sort=[("timestamp", -1)])


def test_unauthenticated_reports_and_payroll_export_are_rejected():
    with TestClient(app) as client:
        assert client.post("/api/reports/generate", json={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "PDF"}).status_code == 401
        assert client.get("/api/reports/download", params={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "PDF"}).status_code == 401
        assert client.get("/api/payroll/export", params={"month": "2023-05"}).status_code == 401


def test_employee_is_blocked_from_report_and_payroll_exports():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)
        assert client.post("/api/reports/generate", headers=headers, json={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "PDF"}).status_code == 403
        assert client.get("/api/reports/download", headers=headers, params={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "PDF"}).status_code == 403
        assert client.get("/api/payroll/export", headers=headers, params={"month": "2023-05"}).status_code == 403


def test_hr_admin_can_generate_and_download_valid_report():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)

        response = client.post(
            "/api/reports/generate",
            headers=headers,
            json={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "PDF", "limit": 50},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["departmentFilter"] == VALID_DEPARTMENT
        assert payload["downloadUrl"].startswith("/reports/download?")

        response = client.get(
            "/api/reports/download",
            headers=headers,
            params={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "CSV", "limit": 50},
        )
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/csv")


def test_hr_admin_can_export_payroll_with_valid_scope():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/payroll/export", headers=headers, params={"month": "2023-05", "limit": 50})
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/csv")


def test_invalid_report_type_and_invalid_department_are_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)

        response = client.post(
            "/api/reports/generate",
            headers=headers,
            json={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "XML"},
        )
        assert response.status_code == 400, response.text

        response = client.get(
            "/api/reports/download",
            headers=headers,
            params={"department": "UnknownDepartment", "dateRange": "Current Month", "format": "CSV"},
        )
        assert response.status_code == 400, response.text


def test_invalid_month_and_over_limit_are_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)

        response = client.get("/api/payroll/export", headers=headers, params={"month": "2023/05"})
        assert response.status_code == 400, response.text

        response = client.get("/api/payroll/export", headers=headers, params={"month": "2023-05", "limit": 5001})
        assert response.status_code == 400, response.text

        response = client.get("/api/reports/download", headers=headers, params={"department": "All", "dateRange": "Current Month", "format": "JSON", "limit": 1000})
        assert response.status_code == 413, response.text


def test_employee_cannot_tamper_with_payroll_scope_and_payslip_access_stays_restricted():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        headers = _headers(token)

        assert client.get("/api/payroll/export", headers=headers, params={"month": "2023-05"}).status_code == 403
        assert client.get(f"/api/payroll/{OTHER_EMPLOYEE_ID}/payslip", headers=headers, params={"month": "2023-05"}).status_code == 403
        assert client.get(f"/api/payroll/{EMPLOYEE_ID}/payslip", headers=headers, params={"month": "2023-05"}).status_code == 200


def test_hr_export_generates_audit_record_without_sensitive_payloads():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get("/api/payroll/export", headers=headers, params={"month": "2023-05", "limit": 50})
        assert response.status_code == 200, response.text

        audit = asyncio.run(_find_latest_audit("Export payroll"))
        assert audit is not None
        assert audit.get("status") == "SUCCESS"
        assert "JWT" not in str(audit)
        assert "password" not in str(audit).lower()
        assert "BasicSalary" not in str(audit).lower()


def test_hr_report_generation_generates_audit_record():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.post(
            "/api/reports/generate",
            headers=headers,
            json={"department": VALID_DEPARTMENT, "dateRange": "Current Month", "format": "PDF", "limit": 50},
        )
        assert response.status_code == 200, response.text

        audit = asyncio.run(_find_latest_audit("Generate report"))
        assert audit is not None
        assert audit.get("status") == "SUCCESS"
        assert audit.get("module") == "Exports"


def test_invalid_date_range_is_rejected():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, HR_EMAIL, creds["HR_ADMIN_TEST_PASSWORD"])
        headers = _headers(token)
        response = client.get(
            "/api/reports/download",
            headers=headers,
            params={"department": VALID_DEPARTMENT, "dateRange": "Future Range", "format": "CSV", "limit": 50},
        )
        assert response.status_code == 400, response.text
