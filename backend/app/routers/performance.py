from fastapi import APIRouter, HTTPException, Request, status
from typing import List

from backend.app.models.schemas import (
    PerformanceBase,
    PerformanceUpdate
)
from backend.app.routers.auth import require_authenticated_user, require_employee_self_or_hr, require_hr_admin

from backend.app.services.workforce_services import (
    PerformanceService
)


router = APIRouter(
    prefix="/performance",
    tags=["Performance & Talent Intelligence"]
)


# ==========================================================================
# Create Performance Record
# ==========================================================================

@router.post(
    "",
    response_model=PerformanceBase,
    status_code=status.HTTP_201_CREATED
)
async def create_performance_record(
    request: Request,
    data: PerformanceBase
):
    """This workspace uses the real MongoDB performance collection; creating synthetic performance rows is disabled."""
    await require_hr_admin(request)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Performance records are read-only in this backend. Use the existing MongoDB performance collection instead of creating synthetic values."
    )


# ==========================================================================
# Get All Performance Records
# ==========================================================================

@router.get(
    "",
    response_model=List[PerformanceBase]
)
async def get_performance_records(request: Request):
    """
    Retrieve performance scores, KPI completion rates,
    and promotion recommendations.
    """
    await require_hr_admin(request)
    return await PerformanceService.get_all()


# ==========================================================================
# Get Employee Performance
# ==========================================================================

@router.get(
    "/{emp_id}",
    response_model=PerformanceBase,
    responses={
        404: {
            "description": "Performance metrics not found for the employee"
        }
    }
)
async def get_employee_performance(
    request: Request,
    emp_id: str
):
    """
    Retrieve performance metrics for a specific employee.
    """
    await require_employee_self_or_hr(request, emp_id=emp_id)

    record = await PerformanceService.get_by_emp_id(
        emp_id
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Performance metrics for employee "
                f"'{emp_id}' not found."
            )
        )

    return record


# ==========================================================================
# Update Employee Performance
# ==========================================================================

@router.put(
    "/{emp_id}",
    response_model=PerformanceBase,
    responses={
        404: {
            "description": "Performance metrics not found for the employee"
        }
    }
)
async def update_employee_performance(
    request: Request,
    emp_id: str,
    data: PerformanceUpdate
):
    """This workspace uses the real MongoDB performance collection; update of raw workforce performance records is disabled."""
    await require_hr_admin(request)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Performance records are read-only in this backend. Updates must be performed against the real MongoDB performance collection only."
    )


# ==========================================================================
# Delete Employee Performance
# ==========================================================================

@router.delete(
    "/{emp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "description": "Performance metrics not found for the employee"
        }
    }
)
async def delete_employee_performance(
    request: Request,
    emp_id: str
):
    """This workspace uses the real MongoDB performance collection; delete is disabled to protect the source workforce dataset."""
    await require_hr_admin(request)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Performance records are read-only in this backend. Deletion of source workforce performance records is disabled."
    )