from fastapi import APIRouter, Request, status
from typing import List

from backend.app.models.schemas import (
    AuditLogBase,
    AuditLogCreate
)
from backend.app.routers.auth import require_authenticated_user, require_hr_admin
from backend.app.services.workforce_services import (
    AuditService
)


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit & Governance"]
)


@router.get(
    "",
    response_model=List[AuditLogBase]
)
async def get_audit_logs(request: Request):
    """Retrieve system security and compliance audit logs."""
    await require_hr_admin(request)
    return await AuditService.get_all()


@router.post(
    "",
    response_model=AuditLogBase,
    status_code=status.HTTP_201_CREATED
)
async def create_audit_log(
    request: Request,
    log: AuditLogCreate
):
    """Log an audit event."""
    await require_hr_admin(request)
    return await AuditService.create(log)