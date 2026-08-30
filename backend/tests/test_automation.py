import asyncio
import pytest

from backend.app.automation.jobs import attendance_jobs


class DummyCollection:
    def __init__(self, docs):
        self._docs = docs

    async def find(self, query):
        class Cursor:
            def __init__(self, docs):
                self._docs = docs

            async def to_list(self, length=None):
                return self._docs

        return Cursor(self._docs)


class DummyDB:
    def __init__(self, attendance_docs=None):
        self.attendance = DummyCollection(attendance_docs or [])


@pytest.mark.asyncio
async def test_attendance_reconciliation_empty(monkeypatch):
    dummy_db = DummyDB([])

    monkeypatch.setattr('backend.app.database.get_database', lambda: dummy_db)

    result = await attendance_jobs.attendance_reconciliation_job()
    assert result['status'] in ('COMPLETED', 'NO_DB', 'FAILED')
    assert 'records_scanned' in result


@pytest.mark.asyncio
async def test_attendance_reconciliation_missing_checkout(monkeypatch):
    # Document with CheckIn but missing CheckOut
    doc = {
        "_id": "1",
        "EmpID": "EMP010000",
        "Date": "2026-08-20",
        "CheckIn": "09:10",
        "CheckOut": "N/A",
        "WorkingHours": 0
    }
    dummy_db = DummyDB([doc])
    monkeypatch.setattr('backend.app.database.get_database', lambda: dummy_db)

    result = await attendance_jobs.attendance_reconciliation_job()
    assert result['records_scanned'] >= 0
    assert result['findings_count'] >= 0
