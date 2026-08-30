from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List, Optional

from backend.app.models.schemas import (
    ShiftRequestBase,
    ShiftRequestResponse,
    ShiftStatusUpdate
)
from backend.app.database import get_database

from backend.app.services.workforce_services import ShiftService
from backend.app.routers.auth import require_authenticated_user, require_employee_self_or_hr, require_hr_admin, get_manager_team_emp_ids


router = APIRouter(
    prefix="/shifts",
    tags=["Shift Scheduling & Swaps"]
)


@router.get(
    "",
    response_model=List[ShiftRequestResponse]
)
async def get_shift_requests(
    request: Request,
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (Pending, Approved, Rejected, Not Requested)"
    ),
    emp_id: Optional[str] = Query(
        None,
        description="Employee ID filter. Employees may only query their own records."
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(50, ge=1, le=1000, description="Page size for pagination")
):
    """Retrieve shift requests and swap applications with pagination."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role == "EMPLOYEE":
        if emp_id and str(emp_id).strip() and str(emp_id).strip() != str(auth_user.get("empId") or "").strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access another employee's shift requests."
            )
        return await ShiftService.get_all(
            status=status_filter,
            page=page,
            size=size,
            emp_id=str(auth_user.get("empId") or "").strip() or None,
        )
    # Managers review swap requests across the whole organisation, not only their own direct
    # reports, so they fall through to the same unscoped query HR uses. Kept in step with
    # GET /leaves and with the approval check in PUT /{shift_id}/status.
    if role.startswith("HR"):
        return await ShiftService.get_all(status=status_filter, page=page, size=size, emp_id=emp_id)
    return await ShiftService.get_all(status=status_filter, page=page, size=size, emp_id=emp_id)


@router.post(
    "",
    response_model=ShiftRequestResponse,
    status_code=status.HTTP_201_CREATED
)
async def submit_shift_request(
    request: Request,
    payload: ShiftRequestBase
):
    """Submit a shift swap or preference request."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role == "EMPLOYEE":
        auth_emp_id = str(auth_user.get("empId") or "").strip()
        if not auth_emp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee profile could not be loaded."
            )
        if str(payload.empId or "").strip() != auth_emp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to submit a shift request for another employee."
            )
        payload.empId = auth_emp_id
    elif role == "MANAGER":
        auth_emp_id = str(auth_user.get("empId") or "").strip()
        team_ids = set(await get_manager_team_emp_ids(auth_user) or [])
        if not auth_emp_id or str(payload.empId or "").strip() not in team_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to submit a shift request for this employee.")
    elif role.startswith("HR"):
        pass

    try:
        return await ShiftService.submit(payload, actor_user=auth_user)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.put(
    "/{shift_id}/status",
    response_model=ShiftRequestResponse
)
async def update_shift_status(
    request: Request,
    shift_id: str,
    update: ShiftStatusUpdate
):
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    # Allow any HR-prefixed role (HR, HR_ADMIN, HR_MANAGER, etc.) or MANAGER to perform approvals
    if not (role.startswith("HR") or role == "MANAGER"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Manager or HR permissions required.")

    # No team-membership check: managers can see every request in GET /shifts, so restricting
    # approval to their own reports would 403 on rows their dashboard offers them.
    try:
        updated = await ShiftService.update_status(
            shift_id,
            update,
            actor_user=auth_user,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift request ID '{shift_id}' not found."
        )

    return updated