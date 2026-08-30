"""Job registry for automation engine."""
import logging
from typing import Any

from backend.app.config import settings

logger = logging.getLogger("uvicorn.error")


async def register_jobs(scheduler: Any):
    """Register automation jobs with the provided scheduler instance.

    This function is idempotent and uses replace_existing to avoid duplicate job registration.
    """
    # Lazy import of IntervalTrigger to avoid import-time dependency on APScheduler
    try:
        from apscheduler.triggers.interval import IntervalTrigger
    except Exception:
        # If APScheduler is not available, raise; the caller will handle failure to start scheduler
        raise

    # Register attendance reconciliation job
    try:
        interval_mins = int(settings.ATTENDANCE_RECONCILIATION_INTERVAL_MINUTES or 15)
    except Exception:
        interval_mins = 15

    from backend.app.automation.jobs import attendance_jobs

    scheduler.add_job(
        attendance_jobs.attendance_reconciliation_job,
        trigger=IntervalTrigger(minutes=interval_mins),
        id="attendance_reconciliation",
        replace_existing=True,
        kwargs={},
    )
    scheduler.add_job(
        attendance_jobs.missing_checkout_detection_job,
        trigger=IntervalTrigger(minutes=15),
        id="missing_checkout_detection",
        replace_existing=True,
        kwargs={},
    )
    scheduler.add_job(
        attendance_jobs.late_arrival_detection_job,
        trigger=IntervalTrigger(minutes=30),
        id="late_arrival_detection",
        replace_existing=True,
        kwargs={},
    )
    scheduler.add_job(
        attendance_jobs.leave_reminder_job,
        trigger=IntervalTrigger(hours=12),
        id="leave_reminder",
        replace_existing=True,
        kwargs={},
    )

    # Placeholder: notification maintenance job (daily)
    try:
        from backend.app.automation.jobs import notification_jobs

        scheduler.add_job(
            notification_jobs.notification_maintenance_job,
            trigger=IntervalTrigger(minutes=60 * 24),
            id="notification_maintenance",
            replace_existing=True,
            kwargs={},
        )
    except Exception:
        logger.exception("Failed to register notification_maintenance job")

    logger.info("Automation registry: registered jobs: attendance_reconciliation, missing_checkout_detection, late_arrival_detection, leave_reminder, notification_maintenance")
