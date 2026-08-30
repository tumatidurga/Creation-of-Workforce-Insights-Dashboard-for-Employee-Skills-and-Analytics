import logging
from fastapi import APIRouter, Request
from fastapi import HTTPException, status

from backend.app.routers.auth import require_hr_admin
from backend.app.automation.scheduler import get_scheduler
from backend.app.automation.jobs.attendance_jobs import (
    attendance_reconciliation_job,
    missing_checkout_detection_job,
    late_arrival_detection_job,
    leave_reminder_job,
)

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/automation", tags=["Automation"])


@router.get("/status")
async def automation_status(request: Request):
    """Return status of the automation engine. HR_ADMIN only."""
    await require_hr_admin(request)

    scheduler = get_scheduler()
    scheduler_running = bool(scheduler and getattr(scheduler, "running", False))
    jobs = []
    if scheduler_running:
        try:
            for job in scheduler.get_jobs():
                jobs.append({
                    "name": job.id,
                    "next_run": job.next_run_time.isoformat() + "Z" if job.next_run_time else None,
                    "status": "scheduled",
                })
        except Exception:
            logger.exception("Failed to enumerate scheduler jobs")

    return {"scheduler_running": scheduler_running, "jobs": jobs}


@router.post("/run/attendance-reconciliation")
async def run_attendance_reconciliation(request: Request):
    """Manually trigger attendance reconciliation (HR only)."""
    await require_hr_admin(request)

    try:
        result = await attendance_reconciliation_job()
        return {
            "job": "attendance_reconciliation",
            "status": result.get("status", "UNKNOWN"),
            "records_scanned": result.get("records_scanned", 0),
            "findings": result.get("findings_count", 0),
            "duration_ms": result.get("duration_ms", 0),
            "details": result,
        }
    except Exception as e:
        logger.exception(f"Manual attendance reconciliation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/run/missing-checkout")
async def run_missing_checkout_job(request: Request):
    """Manually trigger missing-checkout automation (HR only)."""
    await require_hr_admin(request)
    try:
        result = await missing_checkout_detection_job()
        return {"job": "missing_checkout_detection", "status": result.get("status", "UNKNOWN"), "details": result}
    except Exception as e:
        logger.exception(f"Manual missing-checkout job failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/run/late-arrival")
async def run_late_arrival_job(request: Request):
    """Manually trigger late-arrival automation (HR only)."""
    await require_hr_admin(request)
    try:
        result = await late_arrival_detection_job()
        return {"job": "late_arrival_detection", "status": result.get("status", "UNKNOWN"), "details": result}
    except Exception as e:
        logger.exception(f"Manual late-arrival job failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/run/leave-reminder")
async def run_leave_reminder_job(request: Request):
    """Manually trigger leave-reminder automation (HR only)."""
    await require_hr_admin(request)
    try:
        result = await leave_reminder_job()
        return {"job": "leave_reminder", "status": result.get("status", "UNKNOWN"), "details": result}
    except Exception as e:
        logger.exception(f"Manual leave-reminder job failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
