from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List, Optional
from backend.app.models.schemas import TimesheetBase
from backend.app.database import get_database
from backend.app.routers.auth import require_authenticated_user, require_employee_self_or_hr, require_hr_admin, get_manager_team_emp_ids
from backend.app.services.workforce_services import TimesheetService

router = APIRouter(prefix="/timesheets", tags=["Timesheets & Billable Hours"])

@router.get("", response_model=List[TimesheetBase])
async def get_timesheets(
    request: Request,
    emp_id: Optional[str] = Query(None, description="Filter by Employee ID"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(50, ge=1, le=1000, description="Page size for pagination")
):
    """Retrieve timesheet entries with pagination."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role == "EMPLOYEE":
        if emp_id and str(emp_id).strip() != str(auth_user.get("empId") or "").strip():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to access another employee's timesheet records.")
        emp_id = str(auth_user.get("empId") or "") if auth_user.get("empId") else emp_id
    elif role == "MANAGER":
        team_ids = await get_manager_team_emp_ids(auth_user)
        if emp_id and str(emp_id).strip() and str(emp_id).strip() not in set(team_ids or []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to access another employee's timesheet records.")
        return await TimesheetService.get_all(emp_ids=team_ids, page=page, size=size)
    return await TimesheetService.get_all(emp_id=emp_id, page=page, size=size)

@router.post("", response_model=TimesheetBase, status_code=status.HTTP_201_CREATED)
async def submit_timesheet(request: Request, timesheet: TimesheetBase):
    """Log timesheet hours for project tasks."""
    auth_user = await require_authenticated_user(request)
    if auth_user.get("role") == "EMPLOYEE" and str(timesheet.empId or "").strip() != str(auth_user.get("empId") or "").strip():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to submit timesheets for another employee.")
    if auth_user.get("role") == "MANAGER":
        team_ids = set(await get_manager_team_emp_ids(auth_user) or [])
        if str(timesheet.empId or "").strip() not in team_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to submit timesheets for this employee.")
    return await TimesheetService.submit(timesheet)

@router.put("/{timesheet_id}/status", response_model=TimesheetBase)
async def update_timesheet_status(request: Request, timesheet_id: str, new_status: str = Query(..., description="Approved or Rejected")):
    """Update approval status for timesheet entry."""
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role not in {"HR_ADMIN", "MANAGER"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Manager or HR_ADMIN permissions required.")
    if role == "MANAGER":
        db = get_database()
        if db is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB database is not connected.")
        timesheet = await db.timesheets.find_one({"_id": timesheet_id}, {"_id": 0})
        if not timesheet:
            try:
                from bson import ObjectId
                timesheet = await db.timesheets.find_one({"_id": ObjectId(timesheet_id)}, {"_id": 0})
            except Exception:
                timesheet = None
        if not timesheet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Timesheet entry ID '{timesheet_id}' not found.")
        team_ids = set(await get_manager_team_emp_ids(auth_user) or [])
        if str(timesheet.get("EmpID") or "").strip() not in team_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to approve this timesheet entry.")
    updated = await TimesheetService.update_status(timesheet_id, new_status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timesheet entry ID '{timesheet_id}' not found."
        )
    return updated
