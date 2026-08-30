import os
import re
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))

from backend.app.config import settings
from backend.app.main import app

if settings.DATABASE_NAME != "workforce_db_test":
    raise RuntimeError(
        "Refusing to run Step 8 credential tests: DATABASE_NAME must be exactly 'workforce_db_test'."
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "backend" / "scripts" / "remediate_auth.py"


def _resolve_test_credentials():
    hr_pw = os.environ.get("HR_ADMIN_TEST_PASSWORD")
    emp_pw = os.environ.get("EMPLOYEE_TEST_PASSWORD")
    if not hr_pw or not emp_pw:
        hr_pw = "hr-test-secure-" + os.urandom(8).hex()
        emp_pw = "emp-test-secure-" + os.urandom(8).hex()
        os.environ["HR_ADMIN_TEST_PASSWORD"] = hr_pw
        os.environ["EMPLOYEE_TEST_PASSWORD"] = emp_pw
    return hr_pw, emp_pw


HR_ADMIN_TEST_PASSWORD, EMPLOYEE_TEST_PASSWORD = _resolve_test_credentials()


def _run_remediation(env_override):
    env = os.environ.copy()
    env.update(env_override)
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _require_test_credentials():
    return HR_ADMIN_TEST_PASSWORD, EMPLOYEE_TEST_PASSWORD


def test_remediation_does_not_create_repository_credential_artifact():
    repo_credential = REPO_ROOT / "auth-temporary-credentials.txt"
    if repo_credential.exists():
        repo_credential.unlink(missing_ok=True)

    env = {
        "DATABASE_NAME": "workforce_db_test",
        "MONGODB_URL": os.environ.get("MONGODB_URL", ""),
        "HR_ADMIN_TEST_PASSWORD": HR_ADMIN_TEST_PASSWORD,
        "EMPLOYEE_TEST_PASSWORD": EMPLOYEE_TEST_PASSWORD,
    }
    result = _run_remediation(env)

    assert result.returncode == 0, result.stderr
    assert not repo_credential.exists()
    assert "auth-temporary-credentials" not in result.stdout.lower()
    assert "auth-temporary-credentials" not in result.stderr.lower()
    assert HR_ADMIN_TEST_PASSWORD not in result.stdout
    assert EMPLOYEE_TEST_PASSWORD not in result.stdout
    assert HR_ADMIN_TEST_PASSWORD not in result.stderr
    assert EMPLOYEE_TEST_PASSWORD not in result.stderr


def test_environment_credentials_provision_and_authenticate_test_accounts():
    env = {
        "DATABASE_NAME": "workforce_db_test",
        "MONGODB_URL": os.environ.get("MONGODB_URL", ""),
        "HR_ADMIN_TEST_PASSWORD": HR_ADMIN_TEST_PASSWORD,
        "EMPLOYEE_TEST_PASSWORD": EMPLOYEE_TEST_PASSWORD,
    }
    result = _run_remediation(env)
    assert result.returncode == 0, result.stderr

    with TestClient(app) as client:
        hr_login = client.post("/api/auth/login", json={"identifier": "priya.sharma@enterprise.com", "password": HR_ADMIN_TEST_PASSWORD})
        assert hr_login.status_code == 200, hr_login.text
        assert hr_login.json()["token"]

        emp_login = client.post("/api/auth/login", json={"identifier": "EMP000001", "password": EMPLOYEE_TEST_PASSWORD})
        assert emp_login.status_code == 200, emp_login.text
        assert emp_login.json()["token"]


def test_no_source_file_contains_generated_test_passwords():
    hr_pw, emp_pw = _require_test_credentials()
    suspicious = [hr_pw, emp_pw]

    for candidate in REPO_ROOT.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.name.endswith(".pyc") or candidate.name.endswith(".db"):
            continue
        if ".git" in candidate.parts:
            continue
        try:
            content = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for value in suspicious:
            assert value not in content, f"Secret appears in {candidate}"
