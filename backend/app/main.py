import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import connect_to_mongo, close_mongo_connection
from backend.app.routers import (
    auth,
    employees,
    attendance,
    leaves,
    shifts,
    timesheets,
    payroll,
    performance,
    notifications,
    audit,
    ai,
    analytics,
    reports,
    settings as settings_router,
    profile,
    holidays
)

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for MongoDB connections and automation scheduler."""
    logger.info("Initializing Enterprise FastAPI Backend Application...")
    try:
        await connect_to_mongo()
    except Exception:
        logger.warning("MongoDB connection failed on startup — will retry on first request if connection is re-established.")

    # Start automation scheduler if enabled (best-effort)
    try:
        from backend.app.automation.scheduler import start_scheduler
        # start_scheduler is async; call and do not block the lifetime context
        sched = await start_scheduler()
        if sched is None:
            logger.info("Automation Engine: not started (disabled or failed to start)")
    except Exception:
        logger.exception("Failed to initialize automation scheduler")

    try:
        yield
    finally:
        logger.info("Shutting down Enterprise FastAPI Backend Application...")
        # Shutdown automation scheduler
        try:
            from backend.app.automation.scheduler import shutdown_scheduler
            await shutdown_scheduler()
        except Exception:
            logger.exception("Failed to shut down automation scheduler")
        await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

def _parse_cors_origins(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


trusted_origins = _parse_cors_origins(settings.CORS_ALLOWED_ORIGINS)
if not trusted_origins:
    trusted_origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

# Configure CORS for the known browser-facing frontend origins only.
# allow_origin_regex covers Vercel preview & production deployments automatically.
app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-CSRF-Token"],
)

# Health Check Endpoint — enhanced for Vercel diagnostics
@app.get("/api/health", tags=["Health"])
async def health_check():
    """System health check — shows DB connectivity and config status."""
    import os
    from backend.app.database import get_database, connect_to_mongo

    db = get_database()
    db_status = "unknown"
    db_error = None
    db_name = settings.DATABASE_NAME or os.environ.get("DATABASE_NAME", "")
    mongo_url_set = bool(settings.MONGODB_URL)

    # Attempt lazy connect if not yet connected (cold start on Vercel)
    if db is None and mongo_url_set:
        try:
            await connect_to_mongo()
            db = get_database()
        except Exception as e:
            db_error = str(e)

    if db is not None:
        try:
            await db.command("ping")
            db_status = "connected"
        except Exception as e:
            db_status = "error"
            db_error = str(e)
    elif not mongo_url_set:
        db_status = "no_url_configured"
    else:
        db_status = "disconnected"
        if not db_error:
            db_error = "DB instance is None after connect attempt"

    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "framework": "FastAPI (Python 3.11+)",
        "database": {
            "status": db_status,
            "name": db_name,
            "mongo_url_configured": mongo_url_set,
            "error": db_error,
        },
        "env": {
            "JWT_SECRET_KEY_set": bool(settings.JWT_SECRET_KEY),
            "AUTH_BOOTSTRAP_PASSWORD_set": bool(settings.AUTH_BOOTSTRAP_PASSWORD),
            "AUTOMATION_ENABLED": settings.AUTOMATION_ENABLED,
        }
    }


# Include All Feature Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(employees.router, prefix=settings.API_V1_STR)
app.include_router(attendance.router, prefix=settings.API_V1_STR)
app.include_router(leaves.router, prefix=settings.API_V1_STR)
app.include_router(shifts.router, prefix=settings.API_V1_STR)
app.include_router(timesheets.router, prefix=settings.API_V1_STR)
app.include_router(payroll.router, prefix=settings.API_V1_STR)
app.include_router(performance.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(settings_router.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
# Holidays router (static JSON-backed read-only for current-month calendar)
from backend.app.routers import holidays
app.include_router(holidays.router, prefix=settings.API_V1_STR)

# Automation router (HR-only automation status & manual triggers)
try:
    from backend.app.routers import automation as automation_router
    app.include_router(automation_router.router, prefix=settings.API_V1_STR)
except Exception:
    logger.exception("Failed to include automation router")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
