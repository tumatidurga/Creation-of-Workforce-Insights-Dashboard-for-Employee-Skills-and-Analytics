import asyncio
from backend.app.automation.jobs.attendance_jobs import attendance_reconciliation_job

if __name__ == '__main__':
    res = asyncio.get_event_loop().run_until_complete(attendance_reconciliation_job())
    print(res)
