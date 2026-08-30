import os

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))

from backend.app.config import settings
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run Step 7 CORS tests: DATABASE_NAME must be exactly 'workforce_db_test'."
    )

ALLOWED_ORIGIN = "http://127.0.0.1:5173"
UNTRUSTED_ORIGIN = "https://evil.example"
EMPLOYEE_ID = "EMP000001"


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


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_allowed_trusted_origin_receives_cors_headers():
    with TestClient(app) as client:
        response = client.get("/api/health", headers={"Origin": ALLOWED_ORIGIN})
        assert response.status_code == 200, response.text
        assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
        assert response.headers.get("access-control-allow-credentials", "").lower() == "true"


def test_untrusted_origin_does_not_receive_cors_permission():
    with TestClient(app) as client:
        response = client.get("/api/health", headers={"Origin": UNTRUSTED_ORIGIN})
        assert response.status_code == 200, response.text
        assert response.headers.get("access-control-allow-origin") is None


def test_credentialed_requests_do_not_use_wildcard_origin():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        response = client.get(
            "/api/auth/me",
            headers={"Origin": ALLOWED_ORIGIN, **_auth_headers(token)},
        )
        assert response.status_code == 200, response.text
        assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
        assert response.headers.get("access-control-allow-origin") != "*"
        assert response.headers.get("access-control-allow-credentials", "").lower() == "true"


def test_allowed_origin_preflight_options_are_accepted():
    with TestClient(app) as client:
        response = client.options(
            "/api/auth/login",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code in (200, 204), response.text
        assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
        assert response.headers.get("access-control-allow-credentials", "").lower() == "true"
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods.upper()
        allow_headers = response.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allow_headers


def test_untrusted_origin_preflight_is_rejected_or_blocked():
    with TestClient(app) as client:
        response = client.options(
            "/api/auth/login",
            headers={
                "Origin": UNTRUSTED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code in (200, 204, 400, 403, 404), response.text
        assert response.headers.get("access-control-allow-origin") is None


def test_authorization_header_remains_permitted_for_trusted_frontend():
    creds = _get_test_passwords()
    with TestClient(app) as client:
        token = _login(client, EMPLOYEE_ID, creds["EMPLOYEE_TEST_PASSWORD"])
        response = client.get(
            "/api/auth/me",
            headers={"Origin": ALLOWED_ORIGIN, **_auth_headers(token)},
        )
        assert response.status_code == 200, response.text
        assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


def test_protected_auth_behavior_remains_unchanged_for_cors_origin_requests():
    with TestClient(app) as client:
        response = client.get(
            "/api/auth/me",
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert response.status_code == 401, response.text

        response = client.get(
            "/api/attendance?page=1&size=10",
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert response.status_code == 401, response.text
