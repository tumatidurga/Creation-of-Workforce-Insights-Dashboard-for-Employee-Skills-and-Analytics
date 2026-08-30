import jwt
from datetime import datetime, timedelta, timezone
import os

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))
from backend.app.main import app
from backend.app.config import settings

# Safety guard: require a dedicated test database before running these tests.
# Tests must NEVER run against production. Ensure settings.DATABASE_NAME points to an isolated test DB.
if not getattr(settings, "DATABASE_NAME", None) or not settings.DATABASE_NAME.endswith("_test"):
    raise RuntimeError(
        "Refusing to run auth revocation tests: configure a dedicated test database. "
        "Set DATABASE_NAME in your environment or .env to a test-only database before running these tests."
    )

EMP_IDENTIFIER = "EMP000001"
HR_IDENTIFIER = "priya.sharma@enterprise.com"


def _get_test_passwords():
    hr_pw = os.environ.get("HR_ADMIN_TEST_PASSWORD")
    emp_pw = os.environ.get("EMPLOYEE_TEST_PASSWORD")
    if not hr_pw or not emp_pw:
        raise RuntimeError(
            "Set HR_ADMIN_TEST_PASSWORD and EMPLOYEE_TEST_PASSWORD before running backend auth tests."
        )
    return {"HR_ADMIN_TEST_PASSWORD": hr_pw, "EMPLOYEE_TEST_PASSWORD": emp_pw}


def test_employee_logout_revocation():
    creds = _get_test_passwords()
    emp_pw = creds.get("EMPLOYEE_TEST_PASSWORD")
    assert emp_pw

    with TestClient(app) as client:
        # Login
        r = client.post("/api/auth/login", json={"identifier": EMP_IDENTIFIER, "password": emp_pw})
        assert r.status_code == 200
        token = r.json()["token"]

        # Authenticated request succeeds
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        # Logout (should record revocation in the test DB)
        r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        # Old token is rejected
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

        r = client.get("/api/attendance?page=1&size=50", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

        # Login again to obtain a fresh token
        r = client.post("/api/auth/login", json={"identifier": EMP_IDENTIFIER, "password": emp_pw})
        assert r.status_code == 200
        token = r.json()["token"]  # reuse token variable for fresh token

        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        r = client.get("/api/attendance?page=1&size=50", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


def test_hr_logout_revocation():
    creds = _get_test_passwords()
    hr_pw = creds.get("HR_ADMIN_TEST_PASSWORD")
    assert hr_pw

    with TestClient(app) as client:
        # HR login
        r = client.post("/api/auth/login", json={"identifier": HR_IDENTIFIER, "password": hr_pw})
        assert r.status_code == 200
        token = r.json()["token"]

        # Authenticated request succeeds
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        # Logout
        r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        # Old token is rejected
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

        r = client.get("/api/attendance?page=1&size=50", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

        # Login again to obtain a fresh token
        r = client.post("/api/auth/login", json={"identifier": HR_IDENTIFIER, "password": hr_pw})
        assert r.status_code == 200
        token = r.json()["token"]

        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        r = client.get("/api/attendance?page=1&size=50", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


def test_token_contains_jti():
    creds = _get_test_passwords()
    emp_pw = creds.get("EMPLOYEE_TEST_PASSWORD")
    assert emp_pw

    with TestClient(app) as client:
        r = client.post("/api/auth/login", json={"identifier": EMP_IDENTIFIER, "password": emp_pw})
        assert r.status_code == 200
        token = r.json()["token"]

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "jti" in payload and payload["jti"]


def test_legacy_token_without_jti_revocable():
    creds = _get_test_passwords()
    emp_pw = creds.get("EMPLOYEE_TEST_PASSWORD")
    assert emp_pw

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    legacy_payload = {
        "sub": EMP_IDENTIFIER,
        "empId": EMP_IDENTIFIER,
        "email": None,
        "name": "Test Employee",
        "role": "EMPLOYEE",
        "department": None,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    legacy_token = jwt.encode(legacy_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with TestClient(app) as client:
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy_token}"})
        assert r.status_code == 200

        r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {legacy_token}"})
        assert r.status_code == 200

        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy_token}"})
        assert r.status_code == 401
