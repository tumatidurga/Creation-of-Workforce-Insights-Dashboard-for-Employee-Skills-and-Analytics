import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

os.environ.setdefault("MONGODB_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("DATABASE_NAME", "workforce_db_test")
os.environ.setdefault("AUTH_BOOTSTRAP_PASSWORD", os.environ.get("HR_ADMIN_TEST_PASSWORD", "bootstrap-test-password"))

from backend.app.config import settings
from backend.app.main import app


@pytest.fixture(autouse=True)
def isolate_lifecycle_state():
    db = _db()
    default_password = os.environ.get("EMPLOYEE_TEST_PASSWORD", "EMP000001")
    db.user_accounts.update_one(
        {"empId": "EMP000001"},
        {"$set": {"passwordHash": bcrypt.hashpw(default_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(), "role": "EMPLOYEE", "status": "ACTIVE"}},
        upsert=True,
    )
    db.user_accounts.update_one(
        {"empId": "EMP000002"},
        {"$set": {"passwordHash": bcrypt.hashpw("EMP000002".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(), "role": "EMPLOYEE", "status": "ACTIVE"}},
        upsert=True,
    )
    yield


def _require_test_passwords():
    hr_pw = os.environ.get("HR_ADMIN_TEST_PASSWORD")
    emp_pw = os.environ.get("EMPLOYEE_TEST_PASSWORD")
    if not hr_pw or not emp_pw:
        raise RuntimeError("Set HR_ADMIN_TEST_PASSWORD and EMPLOYEE_TEST_PASSWORD before running these tests.")
    return hr_pw, emp_pw


def _db():
    client = MongoClient(os.environ["MONGODB_URL"], serverSelectionTimeoutMS=5000)
    return client[os.environ["DATABASE_NAME"]]


def _login(client, identifier, password):
    response = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _run_script(script_name, extra_env=None):
    env = os.environ.copy()
    env["MONGODB_URL"] = os.environ.get("MONGODB_URL", "mongodb://127.0.0.1:27017")
    env["DATABASE_NAME"] = os.environ.get("DATABASE_NAME", "workforce_db_test")
    if extra_env:
        env.update(extra_env)
    script = os.path.join(os.path.dirname(__file__), "..", "scripts", script_name)
    script = os.path.normpath(script)
    return subprocess.run([sys.executable, script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)


def test_new_employee_provisioning_uses_default_password_status():
    db = _db()
    emp_id = "EMP_LIFECYCLE_9001"
    email = "lifecycle.9001@company.com"
    db.employees.delete_many({"EmpID": emp_id})
    db.user_accounts.delete_many({"empId": emp_id})

    db.employees.insert_one({
        "EmpID": emp_id,
        "EmployeeName": "Lifecycle Test User",
        "Email": email,
        "Department": "Product",
        "EmploymentStatus": "Active",
    })

    result = _run_script("provision_employee_accounts.py")
    assert result.returncode == 0, result.stderr
    account = db.user_accounts.find_one({"empId": emp_id}, {"_id": 0, "passwordHash": 1, "passwordStatus": 1, "mustChangePassword": 1, "passwordChangedAt": 1})
    assert account is not None, "missing provisioned employee account"
    assert account.get("passwordStatus") == "default"
    assert account.get("mustChangePassword") is False
    assert bcrypt.checkpw(emp_id.encode("utf-8"), account["passwordHash"].encode("utf-8"))


def test_default_password_login_and_change_password_lifecycle():
    if not getattr(settings, "DATABASE_NAME", None) or not settings.DATABASE_NAME.endswith("_test"):
        raise RuntimeError("This test must use a test database only.")

    db = _db()
    emp_id = "EMP000001"
    emp_pw = os.environ["EMPLOYEE_TEST_PASSWORD"]

    account = db.user_accounts.find_one({"empId": emp_id})
    assert account is not None, "missing employee self-service account"
    old_password_changed = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    db.user_accounts.update_one(
        {"empId": emp_id},
        {"$set": {"passwordHash": bcrypt.hashpw(emp_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": old_password_changed}}
    )

    with TestClient(app) as client:
        payload = _login(client, emp_id, emp_pw)
        token = payload["token"]
        assert payload["user"]["passwordStatus"] in {"default", "custom"}

        old_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert old_me.status_code == 200, old_me.text

        new_password = "NewPass!2026"
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"currentPassword": emp_pw, "newPassword": new_password, "confirmPassword": new_password},
        )
        assert response.status_code == 200, response.text

        updated = db.user_accounts.find_one({"empId": emp_id}, {"passwordStatus": 1, "mustChangePassword": 1, "passwordChangedAt": 1, "passwordHash": 1})
        assert updated.get("passwordStatus") == "custom"
        assert updated.get("mustChangePassword") is False
        assert updated.get("passwordChangedAt") is not None
        assert bcrypt.checkpw(new_password.encode("utf-8"), updated["passwordHash"].encode("utf-8"))

        rejected = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert rejected.status_code == 401, rejected.text

        bad_old = client.post("/api/auth/login", json={"identifier": emp_id, "password": emp_pw})
        assert bad_old.status_code == 401, bad_old.text

        new_login = _login(client, emp_id, new_password)
        assert new_login["user"]["passwordStatus"] == "custom"

        login_after = new_login["token"]
        fresh_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_after}"})
        assert fresh_me.status_code == 200, fresh_me.text


def test_password_status_normalization_script_and_reprovisioning_preserve_custom_password():
    db = _db()
    emp_id = "EMP000001"
    custom_password = "Custom-Password-2026!"
    current_hash = bcrypt.hashpw(custom_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.user_accounts.update_one({"empId": emp_id}, {"$set": {"passwordHash": current_hash, "passwordStatus": None, "mustChangePassword": False, "passwordChangedAt": None}})

    result = _run_script("normalize_password_status.py")
    assert result.returncode == 0, result.stderr
    normalized = db.user_accounts.find_one({"empId": emp_id}, {"passwordStatus": 1, "passwordHash": 1})
    assert normalized["passwordStatus"] == "custom"

    before_hash = db.user_accounts.find_one({"empId": emp_id}, {"passwordHash": 1})["passwordHash"]
    provision_result = _run_script("provision_employee_accounts.py")
    assert provision_result.returncode == 0, provision_result.stderr
    after_hash = db.user_accounts.find_one({"empId": emp_id}, {"passwordHash": 1})["passwordHash"]
    assert before_hash == after_hash
    assert db.user_accounts.find_one({"empId": emp_id}, {"passwordStatus": 1})["passwordStatus"] == "custom"


def test_unique_indexes_script_is_idempotent_and_rejects_duplicates():
    db = _db()
    db.user_accounts.update_one({"empId": "EMP_DUP_CHECK_1"}, {"$set": {"email": "dup1@example.com", "role": "EMPLOYEE", "passwordHash": bcrypt.hashpw(b"dup1", bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom"}}, upsert=True)
    db.user_accounts.update_one({"empId": "EMP_DUP_CHECK_2"}, {"$set": {"email": "dup2@example.com", "role": "EMPLOYEE", "passwordHash": bcrypt.hashpw(b"dup2", bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom"}}, upsert=True)

    for index_name in ["empId_1", "email_1"]:
        try:
            db.user_accounts.drop_index(index_name)
        except Exception:
            pass

    dup_emp_id = "EMP_DUP_CHECK_DUP"
    duplicate_email = "dup@duplicate.com"
    db.user_accounts.update_many({"$or": [{"empId": dup_emp_id}, {"email": duplicate_email}]}, {"$set": {"role": "EMPLOYEE"}})
    db.user_accounts.insert_one({"userId": "dup-a", "empId": dup_emp_id, "email": duplicate_email, "role": "EMPLOYEE", "passwordHash": bcrypt.hashpw(b"dup-a", bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "default"})
    db.user_accounts.insert_one({"userId": "dup-b", "empId": dup_emp_id, "email": "dup-b@example.com", "role": "EMPLOYEE", "passwordHash": bcrypt.hashpw(b"dup-b", bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom"})

    result = _run_script("create_user_account_indexes.py")
    assert result.returncode == 3, result.stdout + result.stderr

    db.user_accounts.delete_many({"empId": {"$in": ["EMP_DUP_CHECK_1", "EMP_DUP_CHECK_2", dup_emp_id]}})
    db.user_accounts.delete_many({"email": {"$in": ["dup1@example.com", "dup2@example.com", duplicate_email, "dup-b@example.com"]}})

    first = _run_script("create_user_account_indexes.py")
    assert first.returncode == 0, first.stdout + first.stderr
    second = _run_script("create_user_account_indexes.py")
    assert second.returncode == 0, second.stdout + second.stderr


def test_employee_cannot_change_another_employee_password():
    db = _db()
    emp_id = "EMP000001"
    other_emp_id = "EMP000002"
    emp_pw = os.environ["EMPLOYEE_TEST_PASSWORD"]
    other_pw = "EMP000002"

    db.user_accounts.update_one({"empId": emp_id}, {"$set": {"passwordHash": bcrypt.hashpw(emp_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()}})
    db.user_accounts.update_one({"empId": other_emp_id}, {"$set": {"passwordHash": bcrypt.hashpw(other_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()}})
    with TestClient(app) as client:
        emp_token = _login(client, emp_id, emp_pw)["token"]
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {emp_token}"},
            json={"currentPassword": emp_pw, "newPassword": "NewProtect!123", "confirmPassword": "NewProtect!123"},
        )
        assert response.status_code == 200, response.text

        other_record = db.user_accounts.find_one({"empId": other_emp_id}, {"passwordHash": 1})
        assert other_record is not None
        assert bcrypt.checkpw(other_pw.encode("utf-8"), other_record["passwordHash"].encode("utf-8"))

        other_login = _login(client, other_emp_id, other_pw)
        assert other_login["user"]["empId"] == other_emp_id


def test_password_lifecycle_tokens_follow_password_changed_at_rule():
    db = _db()
    emp_id = "EMP000001"
    original_pw = os.environ["EMPLOYEE_TEST_PASSWORD"]
    new_pw = "LaterPass!456"
    db.user_accounts.update_one(
        {"empId": emp_id},
        {"$set": {"passwordHash": bcrypt.hashpw(original_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"), "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()}}
    )

    with TestClient(app) as client:
        login = _login(client, emp_id, original_pw)
        token_before = login["token"]

        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token_before}"},
            json={"currentPassword": original_pw, "newPassword": new_pw, "confirmPassword": new_pw},
        )
        assert response.status_code == 200, response.text

        account = db.user_accounts.find_one({"empId": emp_id}, {"passwordChangedAt": 1})
        assert account and account.get("passwordChangedAt")
        assert account["passwordChangedAt"]

        old_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_before}"})
        assert old_after.status_code == 401, old_after.text

        login_after = _login(client, emp_id, new_pw)
        assert login_after["user"]["empId"] == emp_id
        fresh_token = login_after["token"]
        fresh_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {fresh_token}"})
        assert fresh_me.status_code == 200, fresh_me.text


def test_index_and_password_migration_scripts_work_on_test_db():
    db = _db()
    if db.user_accounts.count_documents({"empId": "EMP_TEST_INDEX_NORMALIZE"}):
        db.user_accounts.delete_many({"empId": "EMP_TEST_INDEX_NORMALIZE"})

    db.user_accounts.insert_one({
        "userId": "EMP_TEST_INDEX_NORMALIZE",
        "empId": "EMP_TEST_INDEX_NORMALIZE",
        "email": "normalize.index@example.com",
        "role": "EMPLOYEE",
        "passwordHash": bcrypt.hashpw(b"EMP_TEST_INDEX_NORMALIZE", bcrypt.gensalt()).decode("utf-8"),
        "passwordStatus": None,
        "mustChangePassword": False,
    })

    normalize = _run_script("normalize_password_status.py")
    assert normalize.returncode == 0, normalize.stdout + normalize.stderr
    indexed = _run_script("create_user_account_indexes.py")
    assert indexed.returncode == 0, indexed.stdout + indexed.stderr

    account = db.user_accounts.find_one({"empId": "EMP_TEST_INDEX_NORMALIZE"}, {"passwordStatus": 1})
    assert account["passwordStatus"] == "default"

    db.user_accounts.delete_many({"empId": "EMP_TEST_INDEX_NORMALIZE"})
