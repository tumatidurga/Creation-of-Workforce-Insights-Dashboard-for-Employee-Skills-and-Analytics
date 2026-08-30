import math
from typing import Optional
from ..database import get_database

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from backend.app.models.schemas import (
    EmployeeResponse,
    EmployeeCreate,
    EmployeeUpdate,
    PaginatedResponse
)
from backend.app.routers.auth import require_employee_self_or_hr, require_hr_admin, require_authenticated_user, get_manager_team_emp_ids

from backend.app.services.workforce_services import (
    EmployeeService,
    MissingEmployeeCounterError,
)


# ==========================================================================
# Router Configuration
# ==========================================================================

router = APIRouter(
    prefix="/employees",
    tags=["Employee Management"]
)


# ==========================================================================
# GET ALL EMPLOYEES
# ==========================================================================

@router.get(
    "",
    response_model=PaginatedResponse[EmployeeResponse]
)
async def get_employees(
    request: Request,
    department: Optional[str] = Query(
        None,
        description="Filter by department name"
    ),

    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by employment status"
    ),

    search: Optional[str] = Query(
        None,
        description="Search by employee ID, name, email, department, role, or location"
    ),

    sort_by: str = Query(
        "empId",
        description="Field to sort by"
    ),

    sort_order: str = Query(
        "asc",
        description="Sort order: asc or desc"
    ),

    page: int = Query(
        1,
        ge=1,
        description="Page number"
    ),

    size: int = Query(
        50,
        ge=1,
        le=500,
        description="Number of records per page"
    )
):
    """
    Retrieve employees with filtering,
    searching, sorting and pagination.
    """
    auth_user = await require_authenticated_user(request)
    role = str(auth_user.get("role") or "").upper()
    if role.startswith("HR"):
        items, total = await EmployeeService.get_all(
            department=department,
            status=status_filter,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
    elif role == "MANAGER":
        team_ids = await get_manager_team_emp_ids(auth_user)
        if not team_ids:
            items, total = [], 0
        else:
            items, total = await EmployeeService.get_all(
                department=department,
                status=status_filter,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                size=size,
                emp_ids=team_ids
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Employee permissions required.")

    pages = math.ceil(total / size) if size > 0 else 1

    # Ensure API contract: skills should always be an array (empty list if missing/null)
    for emp in items:
        skills_val = emp.get("skills", None)
        if skills_val is None:
            emp["skills"] = []
        elif isinstance(skills_val, str):
            emp["skills"] = [s.strip() for s in skills_val.split(",") if s.strip()]

    # Return a JSON response using jsonable_encoder to ensure normalized types
    payload = {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
    return JSONResponse(content=jsonable_encoder(payload))


# ==========================================================================
# GET EMPLOYEE BY ID
# ==========================================================================

@router.get(
    "/{emp_id}",
    response_model=EmployeeResponse
)
async def get_employee_by_id(
    request: Request,
    emp_id: str
):
    """
    Retrieve a single employee using Employee ID.
    """
    await require_employee_self_or_hr(request, emp_id=emp_id)

    employee = await EmployeeService.get_by_id(
        emp_id
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Employee record for ID "
                f"'{emp_id}' was not found."
            )
        )

    # Enrich employee payload with optional related records (performance, payroll, aiPrediction)
    # Do not fail if related documents are missing - return null/leave fields absent
    db = get_database()
    if db is not None:
        try:
            from backend.app.services.workforce_services import (
                normalize_performance,
                normalize_payroll,
                normalize_ai_prediction
            )

            perf_doc = await db.performance.find_one({"EmpID": emp_id}, {"_id": 0})
            if perf_doc:
                perf = normalize_performance(perf_doc)
                # Map performance fields to top-level to match frontend expectations
                for key in [
                    "performanceScore",
                    "productivityScore",
                    "kpiCompletionRate",
                    "performanceRating",
                    "reviewDate",
                ]:
                    if key in perf:
                        employee[key] = perf[key]
                # Provide goalsCompleted/totalGoals if available in raw document
                if perf_doc.get("GoalCompletion") is not None:
                    employee["goalsCompleted"] = perf_doc.get("GoalCompletion")
                if perf_doc.get("TotalGoals") is not None:
                    employee["totalGoals"] = perf_doc.get("TotalGoals")
                else:
                    # If totalGoals missing, leave as None so frontend shows 'Not available'
                    employee.setdefault("totalGoals", None)
                # Promotion mapping
                if "promotionRecommended" in perf:
                    employee["promotionRecommended"] = perf.get("promotionRecommended")

            # Latest payroll record
            payroll_doc = await db.payroll.find_one({"EmpID": emp_id}, sort=[("PayrollMonth", -1)], projection={"_id":0})
            if payroll_doc:
                pay = normalize_payroll(payroll_doc)
                # expose month and netPay on top-level if helpful
                if "month" in pay:
                    employee["lastPayrollMonth"] = pay.get("month")
                if "netPay" in pay:
                    employee["lastNetPay"] = pay.get("netPay")

            # AI prediction
            ai_doc = await db.ai_predictions.find_one({"EmpID": emp_id}, {"_id": 0})
            if ai_doc:
                ai = normalize_ai_prediction(ai_doc)
                # The frontend expects aiFeedback; map recommendation -> aiFeedback
                if ai.get("recommendation"):
                    employee["aiFeedback"] = ai.get("recommendation")
                # attrition risk may be useful
                if ai.get("attritionRisk") is not None:
                    employee["attritionRisk"] = ai.get("attritionRisk")

        except Exception as e:
            # Do not fail the request for enrichment issues - log and continue
            import logging as _logging
            _logging.getLogger(__name__).warning(f"Failed to enrich employee {emp_id} with related records: {e}")

    return employee


# ==========================================================================
# CREATE EMPLOYEE
# ==========================================================================

@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_employee(
    request: Request,
    employee: EmployeeCreate
):
    """
    Register a new employee.

    NOTE:
    The EmployeeService.create() operation will be
    handled separately because the existing MongoDB
    dataset uses legacy field names such as EmpID,
    EmployeeName, Department, etc.
    """
    await require_hr_admin(request)

    # If client supplied an empId, verify it does not already exist.
    # If empId is omitted, EmployeeService.create() will generate one server-side.
    if getattr(employee, 'empId', None):
        existing = await EmployeeService.get_by_id(employee.empId)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Employee ID "
                    f"'{employee.empId}' already exists."
                )
            )

    try:
        return await EmployeeService.create(employee)
    except ValueError as ve:
        # Map duplicate-key conflict (raised by service) to HTTP 409 Conflict
        msg = str(ve)
        if "already exists" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        # Other ValueErrors indicate bad request — surface as 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except MissingEmployeeCounterError as mce:
        # Counter-specific condition — surface as 503 Service Unavailable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Employee ID generator is not initialized. "
                "Please initialize counters.employee_id before creating employees."
            )
        )
    except RuntimeError as rte:
        # Other runtime issues (e.g., DB connection problems) should not be
        # misreported as a missing counter. Surface a 500 to indicate server
        # error instead of the 503 counter-initialization message.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(rte))


# ==========================================================================
# UPDATE EMPLOYEE
# ==========================================================================

@router.put(
    "/{emp_id}",
    response_model=EmployeeResponse
)
async def update_employee(
    request: Request,
    emp_id: str,
    employee_update: EmployeeUpdate
):
    """
    Update an existing employee.
    """
    await require_employee_self_or_hr(request, emp_id=emp_id)

    updated_employee = await EmployeeService.update(
        emp_id,
        employee_update
    )

    if not updated_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Employee record for ID "
                f"'{emp_id}' was not found."
            )
        )

    return updated_employee


# ==========================================================================
# DELETE EMPLOYEE
# ==========================================================================

@router.delete(
    "/{emp_id}",
    status_code=status.HTTP_200_OK
)
async def delete_employee(
    request: Request,
    emp_id: str
):
    """
    Delete an employee record.
    """
    await require_hr_admin(request)

    success = await EmployeeService.delete(
        emp_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Employee record for ID "
                f"'{emp_id}' was not found."
            )
        )

    return {
        "message": (
            f"Employee record {emp_id} "
            "successfully deleted."
        )
    }