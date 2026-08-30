from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List, Optional

from backend.app.models.schemas import (
    LeaveRequestBase,
    LeaveStatusUpdate,
    LeaveBalances
)
from backend.app.services.workforce_services import LeaveService
from backend.app.database import get_database
from backend.app.routers.auth import require_authenticated_user, require_employee_self_or_hr, require_hr_admin, get_manager_team_emp_ids


router = APIRouter(
    prefix="/leaves",
    tags=["Leave & Absence Management"]
)


@router.get("", response_model=List[LeaveRequestBase])
async def get_leave_requests(
    request: Request,
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (Pending, Approved, Rejected)"
    ),
    emp_id: Optional[str] = Query(
        None,
        description="Employee ID filter. Employees may only query their own records."
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(50, ge=1, le=1000, description="Page size for pagination")
):
    """Retrieve leave applications with pagination."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role == "EMPLOYEE":
        if emp_id and str(emp_id).strip() and str(emp_id).strip() != str(auth_user.get("empId") or "").strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access another employee's leave records."
            )
        return await LeaveService.get_all(
            status=status_filter,
            page=page,
            size=size,
            emp_id=str(auth_user.get("empId") or "").strip() or None,
        )
    # Managers review leave across the whole organisation, not only their own direct reports, so
    # they fall through to the same unscoped query HR uses. PUT /{leave_id}/status authorises
    # approvals the same way, otherwise every newly visible row would 403 on approve.
    return await LeaveService.get_all(status=status_filter, page=page, size=size, emp_id=emp_id)


@router.get("/balance", response_model=LeaveBalances)
async def get_leave_balance(request: Request):
    """Aggregate leave balances from the real MongoDB leaves collection."""
    auth_user = await require_authenticated_user(request)

    db = get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected."
        )

    query = {}
    if auth_user.get("role") == "EMPLOYEE":
        if not auth_user.get("empId"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee profile could not be loaded.")
        query["EmpID"] = auth_user["empId"]

    leave_documents = await db.leaves.find(
        query,
        {"_id": 0, "LeaveType": 1, "LeaveBalance": 1, "EmpID": 1}
    ).to_list(length=5000)

    def sum_leave_values(match_strings):
        total = 0
        for doc in leave_documents:
            leave_type = str(doc.get("LeaveType", "")).lower()
            leave_balance = doc.get("LeaveBalance")
            if not isinstance(leave_balance, (int, float)):
                continue
            if any(token in leave_type for token in match_strings):
                total += float(leave_balance)
        return total

    casual_total = sum_leave_values(["casual", "personal"])
    sick_total = sum_leave_values(["sick"])
    earned_total = sum_leave_values(["earned", "annual"])
    parental_total = sum_leave_values(["maternity", "parental"])

    return {
        "casualLeave": {
            "total": int(casual_total),
            "used": 0,
            "remaining": int(casual_total)
        },
        "sickLeave": {
            "total": int(sick_total),
            "used": 0,
            "remaining": int(sick_total)
        },
        "earnedLeave": {
            "total": int(earned_total),
            "used": 0,
            "remaining": int(earned_total)
        },
        "parentalLeave": {
            "total": int(parental_total),
            "used": 0,
            "remaining": int(parental_total)
        }
    }


@router.post(
    "",
    response_model=LeaveRequestBase,
    status_code=status.HTTP_201_CREATED
)
async def submit_leave_request(request: Request, payload: LeaveRequestBase):
    """Submit a new leave request."""
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
                detail="You are not authorized to submit leave for another employee."
            )
        payload.empId = auth_emp_id
    elif role == "MANAGER":
        auth_emp_id = str(auth_user.get("empId") or "").strip()
        team_ids = set(await get_manager_team_emp_ids(auth_user) or [])
        if not auth_emp_id or str(payload.empId or "").strip() not in team_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to submit leave for this employee.")
    elif role.startswith("HR"):
        pass

    try:
        return await LeaveService.submit(payload, actor_user=auth_user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc


@router.put("/{leave_id}/status", response_model=LeaveRequestBase)
async def update_leave_status(
    request: Request,
    leave_id: str,
    update: LeaveStatusUpdate
):
    """Approve or reject leave request."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role == "MANAGER" or role.startswith("HR"):
        pass
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Manager or HR permissions required.")

    # No team-membership check: managers can see every request in GET /leaves, so restricting
    # approval to their own reports would 403 on rows their dashboard offers them.
    try:
        updated = await LeaveService.update_status(
            leave_id,
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
            detail=f"Leave request ID '{leave_id}' not found."
        )

    return updated