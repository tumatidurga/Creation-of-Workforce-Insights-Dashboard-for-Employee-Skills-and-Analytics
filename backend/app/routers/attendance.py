import math
from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List, Optional
from backend.app.models.schemas import AttendanceBase, AttendanceCheckIn, AttendanceCheckOut, AttendanceExceptionCreate, PaginatedResponse
from backend.app.routers.auth import get_authenticated_user, require_employee_self_or_hr, require_hr_admin, get_manager_team_emp_ids
from backend.app.services.workforce_services import AttendanceService, AuditService
from backend.app.models.schemas import AuditLogCreate

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])

@router.get("", response_model=PaginatedResponse[AttendanceBase])
async def get_attendance_records(
    request: Request,
    department: Optional[str] = Query(None, description="Filter by department"),
    employeeId: Optional[str] = Query(None, description="Filter by employee ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by attendance status"),
    startDate: Optional[str] = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="Inclusive end date (YYYY-MM-DD)"),
    date: Optional[str] = Query(None, description="Single date (YYYY-MM-DD). Defaults to today if omitted"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200)
):
    """Get attendance records with filtering and pagination."""
    auth_user = await require_employee_self_or_hr(request, emp_id=employeeId)

    emp_filter = None
    emp_filters = None
    if auth_user.get("role") == "EMPLOYEE":
        emp_filter = auth_user.get("empId")
        if not emp_filter:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employee profile could not be loaded.")
        if employeeId and str(employeeId).strip() and str(employeeId).strip() != str(emp_filter).strip():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to access another employee's attendance record.")
    elif auth_user.get("role") == "MANAGER":
        emp_filters = await get_manager_team_emp_ids(auth_user)
        if not emp_filters:
            emp_filters = []
        if employeeId and str(employeeId).strip() and str(employeeId).strip() not in {str(item).strip() for item in emp_filters if str(item).strip()}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to access this employee's attendance record.")

    items, total, summary = await AttendanceService.get_all(
        department=department,
        status=status_filter,
        page=page,
        size=size,
        employee_emp_id=emp_filter,
        employee_emp_ids=emp_filters,
        employee_id=employeeId,
        date=date,
        start_date=startDate,
        end_date=endDate,
        include_summary=True,
    )

    pages = math.ceil(total / size) if size > 0 else 1
    return PaginatedResponse[AttendanceBase](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
        summary=summary,
    )

@router.get("/anomalies", response_model=List[AttendanceBase])
async def get_attendance_anomalies(request: Request):
    """Retrieve flagged attendance anomalies."""
    await require_hr_admin(request)
    return await AttendanceService.get_anomalies()


@router.post("/exceptions", status_code=status.HTTP_201_CREATED)
async def submit_attendance_exception(request: Request, payload: AttendanceExceptionCreate):
    """Create a pending attendance exception request for the employee."""
    auth_user = await require_employee_self_or_hr(request, emp_id=payload.empId)
    if auth_user.get("role") == "EMPLOYEE" and payload.empId != auth_user.get("empId"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to submit an exception for another employee."
        )
    try:
        record = await AttendanceService.create_attendance_exception(payload)
        actor = auth_user.get("email") or auth_user.get("empId") or "System"
        await AuditService.create(AuditLogCreate(
            actor=actor,
            action=f"Attendance exception submitted for {payload.empId}",
            module="Attendance",
            ipAddress=request.client.host if request.client else "unknown",
            status="SUCCESS",
        ))
        return record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/today-context")
async def get_today_context(request: Request, empId: Optional[str] = Query(None, alias="empId")):
    """Return today's attendance policy context for the authenticated employee or (for HR) for the provided empId."""
    auth_user = await require_employee_self_or_hr(request, emp_id=empId)
    target_emp = empId or auth_user.get("empId")
    if not target_emp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee identifier is required.")
    try:
        context = await AttendanceService.get_today_context(target_emp)
        return context
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/check-in", response_model=AttendanceBase, status_code=status.HTTP_201_CREATED)
async def check_in(request: Request, payload: AttendanceCheckIn):
    """Manual Check In for employee attendance."""
    auth_user = await require_employee_self_or_hr(request, emp_id=payload.empId)
    if auth_user.get("role") == "EMPLOYEE" and payload.empId != auth_user.get("empId"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify another employee's attendance record."
        )
    try:
        return await AttendanceService.check_in(payload)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

@router.post("/check-out", response_model=AttendanceBase)
async def check_out(request: Request, payload: AttendanceCheckOut):
    """Manual Check Out for employee attendance and compute working hours."""
    auth_user = await require_employee_self_or_hr(request, emp_id=payload.empId)
    if auth_user.get("role") == "EMPLOYEE" and payload.empId != auth_user.get("empId"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify another employee's attendance record."
        )
    try:
        record = await AttendanceService.check_out(payload)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active check-in record found to check out for Emp ID '{payload.empId}'."
            )
        return record
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
