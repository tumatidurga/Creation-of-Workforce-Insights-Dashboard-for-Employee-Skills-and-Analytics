import pytest
import asyncio

from backend.app.routers import profile as profile_router
from backend.app.models.additional_schemas import UserProfile


class DummyCollection:
    def __init__(self, docs=None):
        self._docs = docs or []
        self.queries = []

    async def find_one(self, query, projection=None):
        self.queries.append(query)
        for d in self._docs:
            # simple matching for equality on provided fields
            match = True
            for k, v in query.items():
                if isinstance(v, dict):
                    # naive regex handling: just match value ignoring case if $regex present
                    if "$regex" in v:
                        val = v["$regex"].strip("^")
                        if not (d.get(k) and d.get(k).lower() == val.lower()):
                            match = False
                            break
                else:
                    if d.get(k) != v:
                        match = False
                        break
            if match:
                return d
        return None

    def find(self, *a, **k):
        class C:
            def __init__(self, docs):
                self.docs = docs
            def __iter__(self):
                return iter(self.docs)
        return C(self._docs)


class DummyDB:
    def __init__(self, user_accounts=None, employees=None, user_profiles=None):
        self.user_accounts = DummyCollection(user_accounts or [])
        self.employees = DummyCollection(employees or [])
        self.user_profiles = DummyCollection(user_profiles or [])


@pytest.mark.asyncio
async def test_employee_get_profile(monkeypatch):
    # Setup payload and DB: employee with empId and employee doc
    payload = {"empId": "EMP010000", "email": "emp@example.com", "role": "EMPLOYEE", "sub": "EMP010000"}

    account = {"userId": "emp-user-1", "empId": "EMP010000", "name": "Test Employee", "email": "emp@example.com", "role": "EMPLOYEE"}
    employee = {"EmpID": "EMP010000", "EmployeeName": "Test Employee", "Email": "emp@example.com", "Department": "Engineering", "avatar": "http://example.com/emp.png"}

    dummy_db = DummyDB(user_accounts=[account], employees=[employee], user_profiles=[])

    monkeypatch.setattr('backend.app.routers.profile.get_database', lambda: dummy_db)
    async def fake_require(request):
        return payload
    monkeypatch.setattr('backend.app.routers.profile.require_authenticated_user', fake_require)

    result = await profile_router.get_user_profile(None)
    assert result.empId == "EMP010000"
    assert result.name == "Test Employee"
    # missing avatarId should fall back safely without returning an external URL
    assert result.avatar is None
    assert result.avatarId is None
    assert result.email == "emp@example.com"


@pytest.mark.asyncio
async def test_employee_put_profile_upsert_and_forbid_fields(monkeypatch):
    # Setup: authenticated employee account exists without profile
    payload = {"empId": "EMP010000", "email": "emp@example.com", "role": "EMPLOYEE", "sub": "EMP010000"}
    account = {"userId": "emp-user-1", "empId": "EMP010000", "name": "Test Employee", "email": "emp@example.com", "role": "EMPLOYEE"}

    dummy_db = DummyDB(user_accounts=[account], employees=[], user_profiles=[])

    ops = {}

    async def fake_update_one(filter_q, update_doc, upsert=False):
        # Capture what would be saved
        ops['filter'] = filter_q
        ops['update'] = update_doc
        ops['upsert'] = upsert

    dummy_db.user_profiles.update_one = fake_update_one

    monkeypatch.setattr('backend.app.routers.profile.get_database', lambda: dummy_db)
    async def fake_require(request):
        return payload
    monkeypatch.setattr('backend.app.routers.profile.require_authenticated_user', fake_require)

    # Client attempts to change role and userId (forbidden) and set avatar
    incoming = UserProfile(userId="other", empId="SHOULD", name="New Name", email="hacker@example.com", role="HR_ADMIN", avatarId="avatar-03")

    result = await profile_router.update_user_profile(None, incoming)

    # Ensure saved doc uses account_userId and forbidden fields excluded
    assert ops['filter'] == {"userId": "emp-user-1"}
    saved = ops['update']['$set']
    assert saved['userId'] == "emp-user-1"
    assert saved.get('role') != "HR_ADMIN"
    assert saved.get('empId') == "EMP010000"
    assert saved['avatarId'] == "avatar-03"
    assert saved['avatar'] is None


@pytest.mark.asyncio
async def test_hr_admin_profile_get_and_put(monkeypatch):
    # HR admin with empId = None
    payload = {"email": "priya.sharma@enterprise.com", "role": "HR_ADMIN", "sub": "hr-admin"}
    account = {"userId": "hr-admin", "empId": None, "name": "Priya Sharma", "email": "priya.sharma@enterprise.com", "role": "HR_ADMIN"}
    # Existing per-user profile for hr-admin
    profile_doc = {"userId": "hr-admin", "name": "Priya S.", "email": "priya.sharma@enterprise.com", "avatar": "http://example.com/priya.png"}

    dummy_db = DummyDB(user_accounts=[account], employees=[], user_profiles=[profile_doc])

    monkeypatch.setattr('backend.app.routers.profile.get_database', lambda: dummy_db)
    async def fake_require(request):
        return payload
    monkeypatch.setattr('backend.app.routers.profile.require_authenticated_user', fake_require)

    res = await profile_router.get_user_profile(None)
    assert res.userId == "hr-admin"
    assert res.avatar is None
    assert res.avatarId is None

    ops = {}
    async def fake_update_one(filter_q, update_doc, upsert=False):
        ops['filter'] = filter_q
        ops['update'] = update_doc
        ops['upsert'] = upsert
    dummy_db.user_profiles.update_one = fake_update_one

    incoming = UserProfile(name="Priya Sharma", avatarId="avatar-05")
    out = await profile_router.update_user_profile(None, incoming)
    assert ops['filter'] == {"userId": "hr-admin"}
    saved = ops['update']['$set']
    assert saved['avatarId'] == "avatar-05"
    assert saved['avatar'] is None
    assert saved['userId'] == "hr-admin"


@pytest.mark.asyncio
async def test_current_user_string_not_used(monkeypatch):
    # Ensure new logic never queries for CURRENT_USER
    payload = {"empId": None, "email": "someone@company.com", "role": "EMPLOYEE", "sub": "someone"}
    account = {"userId": "someone", "empId": None, "name": "Someone", "email": "someone@company.com", "role": "EMPLOYEE"}

    class SpyCollection(DummyCollection):
        def __init__(self, docs=None):
            super().__init__(docs)
            self.queries = []
        async def find_one(self, query, projection=None):
            self.queries.append(query)
            return await super().find_one(query, projection)

    dummy_db = DummyDB(user_accounts=[account], employees=[], user_profiles=[],)
    dummy_db.user_profiles = SpyCollection([])

    monkeypatch.setattr('backend.app.routers.profile.get_database', lambda: dummy_db)
    async def fake_require(request):
        return payload
    monkeypatch.setattr('backend.app.routers.profile.require_authenticated_user', fake_require)

    res = await profile_router.get_user_profile(None)
    # Ensure no query for {'userId': 'CURRENT_USER'} occurred
    assert not any(q.get('userId') == 'CURRENT_USER' for q in dummy_db.user_profiles.queries)

    # Also ensure passwordHash is never part of the response (UserProfile schema doesn't include it)
    assert not hasattr(res, 'passwordHash')
