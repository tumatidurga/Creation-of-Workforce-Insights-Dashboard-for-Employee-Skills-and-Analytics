import logging
from typing import Optional

from typing import Optional

from backend.app.config import settings

import logging
logger = logging.getLogger("uvicorn.error")

_scheduler: Optional[object] = None


def get_scheduler() -> Optional[object]:
    return _scheduler


async def start_scheduler():
    """Start the AsyncIO scheduler if automation is enabled.

    This function is safe to call multiple times; it will not create duplicate schedulers.
    """
    global _scheduler

    if not settings.AUTOMATION_ENABLED:
        logger.info("Automation Engine: DISABLED by configuration (AUTOMATION_ENABLED=False)")
        return None

    if _scheduler is not None and _scheduler.running:
        logger.info("Automation Engine: Scheduler already running")
        return _scheduler

    try:
        # Lazy import of APScheduler to avoid import-time dependency failure if the package is not installed
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        # Create scheduler with the project's timezone convention. The app uses UTC for automation and comparisons.
        _scheduler = AsyncIOScheduler(timezone=settings.APP_TIMEZONE)
        # default job settings: avoid overlapping runs
        _scheduler.configure(job_defaults={"max_instances": 1, "coalesce": True, "misfire_grace_time": 300})

        # Register jobs via registry (imported lazily to avoid circular import during startup)
        from backend.app.automation import registry
        await registry.register_jobs(_scheduler)

        _scheduler.start()
        logger.info("Automation Engine: ENABLED and scheduler started")
        return _scheduler
    except Exception as e:
        logger.exception(f"Failed to start automation scheduler: {e}")
        _scheduler = None
        return None


async def shutdown_scheduler():
    global _scheduler
    if _scheduler is None:
        logger.info("Automation Engine: No scheduler to shut down")
        return

    try:
        logger.info("Automation Engine: Shutting down scheduler...")
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Automation Engine: Scheduler shutdown complete")
    except Exception as e:
        logger.exception(f"Error shutting down scheduler: {e}")
