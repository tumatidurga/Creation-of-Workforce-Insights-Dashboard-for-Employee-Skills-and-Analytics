from fastapi import APIRouter, Request
from backend.app.routers.auth import require_hr_admin
from backend.app.models.schemas import DashboardMetrics
from backend.app.services.workforce_services import (
    EmployeeService,
    LeaveService,
    ShiftService,
    PayrollService,
    AttendanceService,
    AIPredictionService,
    PerformanceService
)
router = APIRouter(prefix="/analytics", tags=["Executive Analytics & KPIs"])

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(request: Request):
    """Compute dashboard KPIs from the live MongoDB workforce collections using DB-side counts/aggregations."""
    await require_hr_admin(request)

    # Total employees and active employees
    total_emp = await EmployeeService.count_total()
    active_emp = await EmployeeService.count_active()

    # Pending leaves
    pending_leaves = await LeaveService.count_pending() if hasattr(LeaveService, 'count_pending') else await LeaveService.get_all(status='Pending', page=1, size=1) and 0

    # Pending shifts
    pending_shifts = await ShiftService.count_pending() if hasattr(ShiftService, 'count_pending') else await ShiftService.get_all(status='Pending', page=1, size=1) and 0

    # Total payroll (sum of NetSalary)
    total_payroll = await PayrollService.sum_net_salary_for_month(None)

    # Attendance rate computed by DB counts
    attendance_total, present_count = await AttendanceService.count_total_and_present()
    attendance_rate = (
        f"{(present_count / attendance_total * 100):.1f}%"
        if attendance_total else "N/A"
    )

    # Average productivity score from performance records
    productivity_score = (
        await PerformanceService.get_average_productivity_score()
    )

    # Attrition risk count from AI predictions
    attrition_risk_count = await AIPredictionService.count_attrition_above(0.7)

    return DashboardMetrics(
        totalEmployees=total_emp,
        activeEmployees=active_emp,
        attendanceRate=attendance_rate,
        productivityScore=productivity_score,
        attritionRiskCount=attrition_risk_count,
        totalMonthlyPayroll=total_payroll,
        pendingLeaveRequests=pending_leaves,
        pendingShiftRequests=pending_shifts
    )
