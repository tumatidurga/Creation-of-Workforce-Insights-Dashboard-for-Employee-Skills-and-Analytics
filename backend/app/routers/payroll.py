from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, status, Response
from fastapi.responses import Response
from typing import List, Optional

from backend.app.database import get_database
from backend.app.models.schemas import PayrollBase
from backend.app.models.additional_schemas import MAX_PAYROLL_EXPORT_ROWS
from backend.app.routers.auth import require_authenticated_user, require_employee_self_or_hr, require_hr_admin
from backend.app.services.workforce_services import PayrollService, normalize_payroll, log_export_audit

router = APIRouter(prefix="/payroll", tags=["Payroll & Compensation"])


def _validate_month(month: Optional[str]) -> Optional[str]:
    if month is None or not str(month).strip():
        return None
    normalized = str(month).strip()
    try:
        datetime.strptime(normalized, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payroll month must use YYYY-MM format."
        ) from exc
    return normalized


@router.get("", response_model=List[PayrollBase])
async def get_payroll_records(
    request: Request,
    month: Optional[str] = Query(None, description="Filter by pay month (e.g. 2023-05)"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(50, ge=1, le=1000, description="Page size for pagination")
):
    """Retrieve payroll statements from the real MongoDB payroll collection with pagination."""
    auth_user = await require_authenticated_user(request)
    validated_month = _validate_month(month)

    if auth_user.get("role") == "EMPLOYEE":
        employee_emp_id = str(auth_user.get("empId") or auth_user.get("userId") or "").strip()
        if not employee_emp_id:
            return []
        return await PayrollService.get_all(
            month=validated_month,
            page=page,
            size=size,
            emp_id=employee_emp_id,
        )

    return await PayrollService.get_all(month=validated_month, page=page, size=size)

@router.post("/calculate", response_model=List[PayrollBase])
async def calculate_payroll(request: Request, month: str = Query("2023-05", description="Pay cycle month")):
    """Return the existing payroll records for the requested month without creating synthetic payroll data."""
    await require_hr_admin(request)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB database is not connected.")

    query = {}
    if month:
        query["PayrollMonth"] = {"$regex": f"^{month}$", "$options": "i"}

    items = await db.payroll.find(query, {"_id": 0}).to_list(length=5000)
    return [normalize_payroll(item) for item in items]


@router.get("/export")
async def export_payroll(
    request: Request,
    month: Optional[str] = Query(None, description="Filter by pay month (e.g. 2023-05)"),
    limit: Optional[int] = Query(default=None, ge=1, description="Maximum rows to export."),
):
    """Export payroll records as CSV. Uses real payroll collection data only."""
    auth_user = await require_hr_admin(request)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB database is not connected.")

    validated_month = _validate_month(month)
    final_limit = MAX_PAYROLL_EXPORT_ROWS if limit is None else int(limit)
    if final_limit < 1 or final_limit > MAX_PAYROLL_EXPORT_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payroll export limit must be between 1 and {MAX_PAYROLL_EXPORT_ROWS}.",
        )

    query = {}
    if validated_month:
        query["PayrollMonth"] = {"$regex": f"^{validated_month}$", "$options": "i"}

    cursor = db.payroll.find(query, {"_id": 0})
    records = await cursor.to_list(length=final_limit + 1)
    if len(records) > final_limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payroll export exceeds the maximum of {final_limit} records. Narrow the month or increase the server-side cap.",
        )

    import io, csv, datetime
    si = io.StringIO()
    writer = csv.writer(si)
    header = ["EmpID", "EmployeeName", "BaseSalary", "OvertimePay", "PerformanceBonus", "TaxDeductions", "NetPay", "PayrollMonth"]
    writer.writerow(["Nexus Payroll Export"])
    writer.writerow([f"Generated: {datetime.datetime.now().isoformat()}"])
    writer.writerow([])
    writer.writerow(header)

    for r in records:
        writer.writerow([
            r.get("EmpID", ""),
            r.get("EmployeeName", ""),
            r.get("BasicSalary", ""),
            r.get("OvertimePay", ""),
            r.get("Bonus", ""),
            r.get("Tax", ""),
            r.get("NetSalary", ""),
            r.get("PayrollMonth", "")
        ])

    actor = auth_user.get("userId") or auth_user.get("email") or auth_user.get("empId") or "HR_ADMIN"
    await log_export_audit(
        actor=actor,
        action="Export payroll",
        scope=f"month={validated_month or 'all'}",
        export_format="CSV",
        record_count=len(records),
        ip_address=request.client.host if request.client else None,
    )

    data = si.getvalue().encode('utf-8')
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"Nexus_Payroll_Export_{timestamp}.csv"
    disposition = f'attachment; filename="{filename}"'
    return Response(content=data, media_type="text/csv", headers={"Content-Disposition": disposition})

@router.put("/{payroll_id}/disburse", response_model=PayrollBase)
async def disburse_payroll(request: Request, payroll_id: str):
    """Return the matching payroll record without fabricating or mutating source data."""
    await require_hr_admin(request)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB database is not connected.")

    record = await db.payroll.find_one({"_id": payroll_id})
    if not record:
        record = await db.payroll.find_one({"id": payroll_id})
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll record ID '{payroll_id}' not found."
        )
    return normalize_payroll(record)


@router.get("/{emp_id}/payslip")
async def download_payslip(request: Request, emp_id: str, month: Optional[str] = Query(None, description="Payroll month in YYYY-MM")):
    """Generate a payslip PDF for the specified employee and month.

    If month is omitted, return the most recent payroll record for the employee.
    """
    await require_employee_self_or_hr(request, emp_id=emp_id)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB database is not connected.")

    # Find payroll record for the employee
    query = {"EmpID": emp_id}
    if month:
        query["PayrollMonth"] = {"$regex": f"^{month}$", "$options": "i"}

    # Prefer the most recent payroll month if multiple
    # Use a cursor with sort to reliably get the most recent payroll record when multiple exist
    cursor = db.payroll.find(query, {"_id": 0}).sort([("PayrollMonth", -1)]).limit(1)
    results = await cursor.to_list(length=1)
    record = results[0] if results else None
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payroll record for '{emp_id}'{(f' month {month}' if month else '')} not found.")

    payroll = normalize_payroll(record)

    # Load employee for display
    emp = await db.employees.find_one({"EmpID": emp_id}, {"_id": 0})
    employee = None
    if emp:
        from backend.app.services.workforce_services import normalize_employee
        employee = normalize_employee(emp)

    # Generate PDF using reportlab (local import to avoid stale module-level state)
    try:
        from reportlab.lib.pagesizes import letter as _letter
        from reportlab.pdfgen import canvas as _canvas
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation library import error: {e}")

    import io
    bio = io.BytesIO()
    c = _canvas.Canvas(bio, pagesize=_letter)
    width, height = _letter
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "NEXUS ENTERPRISE PAYSLIP")
    y -= 24
    c.setFont("Helvetica", 10)
    payroll_month = payroll.get("month") or record.get("PayrollMonth") or ""
    c.drawString(50, y, f"Pay Period: {payroll_month}")
    y -= 20

    # Employee header
    emp_display = emp and (emp.get("EmployeeName") or f"{emp.get('firstName','')} {emp.get('lastName','')}")
    c.drawString(50, y, f"Employee: {emp_id}")
    y -= 15
    c.drawString(50, y, f"Designation: {employee.get('designation') if employee else '-'}")
    y -= 20

    # Earnings
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "EARNINGS")
    y -= 16
    c.setFont("Helvetica", 10)
    base = payroll.get("baseSalary", 0)
    overtime = payroll.get("overtimePay", 0)
    bonus = payroll.get("performanceBonus", 0)
    c.drawString(60, y, f"Base Salary: ${int(base):,}") ; y -= 14
    c.drawString(60, y, f"Overtime Pay: ${int(overtime):,}") ; y -= 14
    c.drawString(60, y, f"Performance Bonus: ${int(bonus):,}") ; y -= 18

    # Deductions
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "DEDUCTIONS")
    y -= 16
    c.setFont("Helvetica", 10)
    tax = payroll.get("taxDeductions", 0) or 0
    attendance_ded = payroll.get("attendanceDeductions", 0) or 0
    c.drawString(60, y, f"Income Tax Withholding: -${int(tax):,}") ; y -= 14
    c.drawString(60, y, f"Attendance Unpaid Leave Deductions: -${int(attendance_ded):,}") ; y -= 18

    # Net payout
    net = payroll.get("netPay", 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"TOTAL NET PAYOUT: ${int(net):,}")
    y -= 24

    c.showPage()
    c.save()
    bio.seek(0)

    filename = f"Nexus_Payslip_{emp_id}_{payroll_month}.pdf"
    disposition = f'attachment; filename="{filename}"'
    return Response(content=bio.getvalue(), media_type="application/pdf", headers={"Content-Disposition": disposition})
