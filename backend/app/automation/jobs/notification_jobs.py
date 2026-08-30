import logging
import time
from datetime import datetime

logger = logging.getLogger("uvicorn.error")


async def notification_maintenance_job():
    """Placeholder job for notification maintenance.

    This job currently performs a safe read-only scan and logs the number of notifications present.
    It is intentionally non-destructive in Phase 1.
    """
    start_ts = time.time()
    try:
        # Best-effort read of notifications collection if available
        from backend.app.database import get_database
        db = get_database()
        count = None
        if db is not None and hasattr(db, "notifications"):
            try:
                count = await db.notifications.count_documents({})
            except Exception:
                logger.exception("Failed to count notifications")
        logger.info(f"[Automation] notification_maintenance completed notifications_count={count}")
        return {
            "job_name": "notification_maintenance",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "finished_at": datetime.utcnow().isoformat() + "Z",
            "status": "COMPLETED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "notifications_count": count,
        }
    except Exception as e:
        logger.exception(f"notification_maintenance failed: {e}")
        return {
            "job_name": "notification_maintenance",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "finished_at": datetime.utcnow().isoformat() + "Z",
            "status": "FAILED",
            "duration_ms": int((time.time() - start_ts) * 1000),
            "error": str(e),
        }
