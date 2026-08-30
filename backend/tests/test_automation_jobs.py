import re
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.automation.jobs import attendance_jobs


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, query=None, projection=None, *args, **kwargs):
        if query is None:
            return FakeCollection(self.docs)
        filtered = [doc for doc in self.docs if self._matches(doc, query)]
        return FakeCollection(filtered)

    async def to_list(self, length=None):
        return list(self.docs)

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                return doc
        return None

    async def insert_one(self, doc):
        self.docs.append(doc)
        return doc

    async def distinct(self, key, query=None):
        if query is None:
            return list({doc.get(key) for doc in self.docs if key in doc})
        values = []
        for doc in self.docs:
            if self._matches(doc, query):
                value = doc.get(key)
                if value is not None:
                    values.append(value)
        return list(dict.fromkeys(values))

    def _matches(self, doc, query):
        if not isinstance(query, dict):
            return False
        for key, expected in query.items():
            if key == "$or":
                if not any(self._matches(doc, item) for item in expected):
                    return False
                continue
            if key == "$and":
                if not all(self._matches(doc, item) for item in expected):
                    return False
                continue
            if isinstance(expected, dict):
                if "$regex" in expected:
                    regex = expected["$regex"]
                    if not re.search(regex, str(doc.get(key, "")), flags=re.IGNORECASE):
                        return False
                    continue
                if "$in" in expected:
                    if doc.get(key) not in expected["$in"]:
                        return False
                    continue
                if "$ne" in expected:
                    if doc.get(key) == expected["$ne"]:
                        return False
                    continue
                if "$exists" in expected:
                    if (key in doc) != expected["$exists"]:
                        return False
                    continue
                if "$gte" in expected:
                    if not (doc.get(key) >= expected["$gte"]):
                        return False
                    continue
                if "$lt" in expected:
                    if not (doc.get(key) < expected["$lt"]):
                        return False
                    continue
            if doc.get(key) != expected:
                return False
        return True


class FakeDB:
    def __init__(self, attendance=None, employees=None, shifts=None, leaves=None):
        self.attendance = FakeCollection(attendance or [])
        self.employees = FakeCollection(employees or [])
        self.shifts = FakeCollection(shifts or [])
        self.leaves = FakeCollection(leaves or [])
        self.audit_logs = FakeCollection([])
        self.notifications = FakeCollection([])


def _attendance_window(hours_ago):
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")


@pytest.mark.asyncio
async def test_missing_checkout_no_alert_before_expected_elapsed_hours(monkeypatch):
    attendance_date, check_in = _attendance_window(2)
    db = FakeDB(
        attendance=[{"EmpID": "EMP000101", "Date": attendance_date, "CheckIn": check_in, "CheckOut": None}],
        employees=[{"EmpID": "EMP000101", "EmploymentStatus": "Active"}],
        shifts=[{"EmpID": "EMP000101", "ShiftDate": attendance_date, "ShiftStart": "08:00", "ShiftEnd": "16:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.missing_checkout_detection_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_missing_checkout_alert_after_shift_window(monkeypatch):
    attendance_date, check_in = _attendance_window(9)
    db = FakeDB(
        attendance=[{"EmpID": "EMP000102", "Date": attendance_date, "CheckIn": check_in, "CheckOut": None}],
        employees=[{"EmpID": "EMP000102", "EmploymentStatus": "Active"}],
        shifts=[{"EmpID": "EMP000102", "ShiftDate": attendance_date, "ShiftStart": "08:00", "ShiftEnd": "16:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.missing_checkout_detection_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_missing_checkout_alert_for_yesterday_completed_shift(monkeypatch):
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000103", "Date": yesterday, "CheckIn": "08:00", "CheckOut": None}],
        employees=[{"EmpID": "EMP000103", "EmploymentStatus": "Active"}],
        shifts=[{"EmpID": "EMP000103", "ShiftDate": yesterday, "ShiftStart": "08:00", "ShiftEnd": "16:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.missing_checkout_detection_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_missing_checkout_skips_active_shift_not_ended(monkeypatch):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000104", "Date": today, "CheckIn": "10:00", "CheckOut": None}],
        employees=[{"EmpID": "EMP000104", "EmploymentStatus": "Active"}],
        shifts=[{"EmpID": "EMP000104", "ShiftDate": today, "ShiftStart": "08:00", "ShiftEnd": "18:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.missing_checkout_detection_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_missing_checkout_uses_valid_shift_duration(monkeypatch):
    attendance_date, check_in = _attendance_window(5)
    db = FakeDB(
        attendance=[{"EmpID": "EMP000105", "Date": attendance_date, "CheckIn": check_in, "CheckOut": None}],
        employees=[{"EmpID": "EMP000105", "EmploymentStatus": "Active"}],
        shifts=[{"EmpID": "EMP000105", "ShiftDate": attendance_date, "ShiftStart": "08:00", "ShiftEnd": "12:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.missing_checkout_detection_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_missing_checkout_uses_conservative_fallback_without_shift(monkeypatch):
    attendance_date, check_in = _attendance_window(9)
    db = FakeDB(
        attendance=[{"EmpID": "EMP000106", "Date": attendance_date, "CheckIn": check_in, "CheckOut": None}],
        employees=[{"EmpID": "EMP000106", "EmploymentStatus": "Active"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.missing_checkout_detection_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_late_arrival_uses_grace_threshold(monkeypatch):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000201", "Date": today, "CheckIn": "09:05", "CheckOut": "17:00", "LateArrival": False}],
        shifts=[{"EmpID": "EMP000201", "ShiftDate": today, "ShiftStart": "09:00", "ShiftEnd": "17:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.late_arrival_detection_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_late_arrival_alerts_after_grace_period(monkeypatch):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000202", "Date": today, "CheckIn": "09:20", "CheckOut": "17:00", "LateArrival": False}],
        shifts=[{"EmpID": "EMP000202", "ShiftDate": today, "ShiftStart": "09:00", "ShiftEnd": "17:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.late_arrival_detection_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_late_arrival_alerts_for_later_shift(monkeypatch):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000203", "Date": today, "CheckIn": "14:20", "CheckOut": "22:00", "LateArrival": False}],
        shifts=[{"EmpID": "EMP000203", "ShiftDate": today, "ShiftStart": "14:00", "ShiftEnd": "22:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.late_arrival_detection_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_late_arrival_skips_when_shift_missing(monkeypatch):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000204", "Date": today, "CheckIn": "09:20", "CheckOut": "17:00", "LateArrival": False}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.late_arrival_detection_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_leave_reminder_no_alert_for_recent_submission(monkeypatch):
    db = FakeDB(leaves=[{"EmpID": "EMP000301", "StartDate": "2030-01-05", "Status": "Pending", "createdAt": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace('+00:00', 'Z')}])
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.leave_reminder_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_leave_reminder_alert_after_72_hours(monkeypatch):
    db = FakeDB(leaves=[{"EmpID": "EMP000302", "StartDate": "2030-01-05", "Status": "Pending", "createdAt": (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat().replace('+00:00', 'Z')}])
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.leave_reminder_job()
    assert result["events_detected"] == 1


@pytest.mark.asyncio
async def test_leave_reminder_skips_future_leave(monkeypatch):
    future_start = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
    db = FakeDB(leaves=[{"EmpID": "EMP000303", "StartDate": future_start, "Status": "Pending", "createdAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace('+00:00', 'Z')}])
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.leave_reminder_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_leave_reminder_skips_approved_and_rejected(monkeypatch):
    db = FakeDB(leaves=[
        {"EmpID": "EMP000304", "StartDate": "2030-01-05", "Status": "Approved", "createdAt": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat().replace('+00:00', 'Z')},
        {"EmpID": "EMP000305", "StartDate": "2030-01-06", "Status": "Rejected", "createdAt": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat().replace('+00:00', 'Z')},
    ])
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    result = await attendance_jobs.leave_reminder_job()
    assert result["events_detected"] == 0


@pytest.mark.asyncio
async def test_missing_checkout_job_is_idempotent(monkeypatch):
    attendance_date, check_in = _attendance_window(9)
    db = FakeDB(
        attendance=[{"EmpID": "EMP000401", "Date": attendance_date, "CheckIn": check_in, "CheckOut": None}],
        employees=[{"EmpID": "EMP000401", "EmploymentStatus": "Active"}],
        shifts=[{"EmpID": "EMP000401", "ShiftDate": attendance_date, "ShiftStart": "08:00", "ShiftEnd": "16:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    first = await attendance_jobs.missing_checkout_detection_job()
    second = await attendance_jobs.missing_checkout_detection_job()
    assert first["events_detected"] == 1
    assert second["events_detected"] == 0
    assert len(db.audit_logs.docs) == 1
    assert len(db.notifications.docs) == 2


@pytest.mark.asyncio
async def test_late_arrival_job_is_idempotent(monkeypatch):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = FakeDB(
        attendance=[{"EmpID": "EMP000402", "Date": today, "CheckIn": "09:20", "CheckOut": "17:00", "LateArrival": False}],
        shifts=[{"EmpID": "EMP000402", "ShiftDate": today, "ShiftStart": "09:00", "ShiftEnd": "17:00"}],
    )
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    first = await attendance_jobs.late_arrival_detection_job()
    second = await attendance_jobs.late_arrival_detection_job()
    assert first["events_detected"] == 1
    assert second["events_detected"] == 0
    assert len(db.audit_logs.docs) == 1
    assert len(db.notifications.docs) == 2


@pytest.mark.asyncio
async def test_leave_reminder_job_is_idempotent(monkeypatch):
    db = FakeDB(leaves=[{"EmpID": "EMP000403", "StartDate": "2030-01-05", "Status": "Pending", "createdAt": (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat().replace('+00:00', 'Z')}])
    monkeypatch.setattr('backend.app.automation.jobs.attendance_jobs.get_database', lambda: db)
    first = await attendance_jobs.leave_reminder_job()
    second = await attendance_jobs.leave_reminder_job()
    assert first["events_detected"] == 1
    assert second["events_detected"] == 0
    assert len(db.audit_logs.docs) == 1
    assert len(db.notifications.docs) == 2
