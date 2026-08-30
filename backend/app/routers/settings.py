from fastapi import APIRouter, HTTPException, Request, status
from backend.app.routers.auth import require_hr_admin

from backend.app.models.additional_schemas import SystemSettings
from backend.app.database import get_database


router = APIRouter(
    prefix="/settings",
    tags=["System Configuration"]
)


@router.get("", response_model=SystemSettings)
async def get_system_settings(request: Request):
    """Retrieve app-managed configuration settings without creating synthetic defaults."""
    await require_hr_admin(request)

    db = get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected."
        )

    settings_doc = await db.system_settings.find_one(
        {"configId": "SYSTEM"},
        {"_id": 0}
    )

    if settings_doc:
        settings_doc.pop("configId", None)
        return SystemSettings(**settings_doc)

    return SystemSettings()


@router.put("", response_model=SystemSettings)
async def update_system_settings(
    request: Request,
    settings: SystemSettings
):
    """Persist app-managed configuration only when an existing settings record is present."""
    await require_hr_admin(request)

    db = get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected."
        )

    existing = await db.system_settings.find_one({"configId": "SYSTEM"})
    if not existing:
        return settings

    settings_data = settings.model_dump()
    await db.system_settings.update_one(
        {"configId": "SYSTEM"},
        {"$set": settings_data}
    )

    return settings


@router.get('/status')
async def get_system_status(request: Request):
    """Return read-only operational status flags for secure integrations and database connectivity.

    This endpoint intentionally does NOT return secrets or API keys. It only reports boolean/config flags
    and non-sensitive indicators that the frontend can show in integration cards.
    """
    await require_hr_admin(request)

    from backend.app.config import settings as app_settings
    db = get_database()

    mongo_connected = False
    try:
        if db is not None:
            # perform a cheap ping - do not reveal connection details
            await db.command('ping')
            mongo_connected = True
    except Exception:
        mongo_connected = False

    return {
        'geminiConfigured': bool(app_settings.GEMINI_API_KEY),
        'activeAIModel': app_settings.GEMINI_API_KEY and 'gemini-2.5-flash' or None,
        'mongoConnected': mongo_connected,
        'vectorEngine': 'local-embeddings' if app_settings.GEMINI_API_KEY else None
    }