from fastapi import APIRouter, HTTPException, Query, Request, status
from backend.app.routers.auth import require_authenticated_user, require_hr_admin
from typing import List

from backend.app.models.schemas import (
    NotificationBase,
    NotificationCreate
)
from backend.app.services.workforce_services import NotificationService


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# ==========================================================================
# GET Notifications
# ==========================================================================

@router.get(
    "",
    response_model=List[NotificationBase]
)
async def get_notifications(
    request: Request,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(50, ge=1, le=1000, description="Page size for pagination")
):
    """Retrieve notifications scoped to the authenticated user."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    return await NotificationService.get_all(
        page=page,
        size=size,
        emp_id=auth_user.get("empId"),
        user_id=auth_user.get("userId"),
        role=role,
    )


@router.get("/unread-count")
async def get_unread_notification_count(request: Request):
    """Return the current user's unread notification count."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    count = await NotificationService.count_unread(
        emp_id=auth_user.get("empId"),
        user_id=auth_user.get("userId"),
        role=role,
    )
    return {"count": count}


# ==========================================================================
# POST Create Notification
# ==========================================================================

@router.post(
    "",
    response_model=NotificationBase,
    status_code=status.HTTP_201_CREATED
)
async def create_notification(
    request: Request,
    notification: NotificationCreate
):
    """Create a new system or workforce activity notification."""
    await require_hr_admin(request)

    return await NotificationService.create(
        notification
    )


# ==========================================================================
# PUT Mark Notification as Read
# ==========================================================================

@router.put(
    "/{notif_id}/read"
)
async def mark_notification_read(
    request: Request,
    notif_id: str
):
    """Mark a specific notification as read."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()

    existing = await NotificationService.get_by_id(notif_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notif_id}' not found."
        )

    current_emp_id = str(auth_user.get("empId") or "").strip()
    current_user_id = str(auth_user.get("userId") or "").strip()

    if not NotificationService.user_can_access_notification(
        existing,
        emp_id=current_emp_id,
        user_id=current_user_id,
        role=role,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this notification."
        )

    success = await NotificationService.mark_read(
        notif_id,
        emp_id=current_emp_id,
        user_id=current_user_id,
        role=role,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notif_id}' not found."
        )

    return {
        "message": f"Notification {notif_id} marked as read"
    }


# ==========================================================================
# POST Mark All Notifications as Read
# ==========================================================================

@router.post(
    "/mark-all-read"
)
async def mark_all_notifications_read(request: Request):
    """Mark the current user's notifications as read."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()

    await NotificationService.mark_all_read(
        emp_id=auth_user.get("empId"),
        user_id=auth_user.get("userId"),
        role=role,
    )
    return {
        "message": "Your notifications marked as read"
    }