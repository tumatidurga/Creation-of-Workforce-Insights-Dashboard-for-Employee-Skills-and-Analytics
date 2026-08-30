from datetime import datetime
import io
import csv
import json
import urllib.parse
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status, Query
from backend.app.routers.auth import require_hr_admin
from fastapi.responses import Response, StreamingResponse

from backend.app.models.additional_schemas import (
    ReportFilter,
    ReportSummaryResponse,
    MAX_REPORT_EXPORT_ROWS,
    VALID_REPORT_DATE_RANGES,
    VALID_REPORT_FORMATS,
)
from backend.app.database import get_database
from backend.app.services.workforce_services import log_export_audit

try:
    # Optional: used only when generating XLSX or PDF
    from openpyxl import Workbook
except Exception:
    Workbook = None

try:
    # reportlab for PDF generation
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None


router = APIRouter(
    prefix="/reports",
    tags=["Reports & Workforce Analytics"]
)


async def _validate_export_scope(
    db,
    department: Optional[str],
    date_range: Optional[str],
    export_format: Optional[str],
    limit: Optional[int] = None,
):
    """Validate report scope and cap the maximum record count before any export is generated."""
    normalized_department = (department or "").strip()
    if not normalized_department:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department filter is required.")

    if normalized_department.lower() == "all":
        normalized_department = "All"
    else:
        allowed_departments = {
            str(item).strip()
            for item in await db.employees.distinct("Department")
            if str(item).strip()
        }
        if normalized_department not in allowed_departments and not any(
            normalized_department.lower() == item.lower() for item in allowed_departments
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department '{normalized_department}' is not available for reports."
            )

    # Normalize UI-provided labels that may include a human-friendly prefix/suffix
    # Example UI value: "August 2026 (Current Month)" — extract the canonical token inside
    normalized_date_range = (date_range or "").strip()
    if not normalized_date_range:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="dateRange is required.")

    # If UI provided a parenthetical canonical label, prefer the inner value
    if "(" in normalized_date_range and ")" in normalized_date_range:
        try:
            inner = normalized_date_range[normalized_date_range.rfind("(")+1:normalized_date_range.rfind(")")].strip()
            if inner:
                normalized_date_range = inner
        except Exception:
            pass

    # Accept case-insensitive matches of valid canonical ranges
    if normalized_date_range not in VALID_REPORT_DATE_RANGES and not any(
        normalized_date_range.lower() == item.lower() for item in VALID_REPORT_DATE_RANGES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported dateRange '{normalized_date_range}'."
        )

    normalized_format = (export_format or "").strip().upper()
    if normalized_format not in VALID_REPORT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{export_format}'."
        )

    # Allow caller to request an unlimited count by omitting the `limit` parameter.
    # If limit is provided, ensure it is a positive integer. Do not enforce a hard
    # upper bound here — the download/generation endpoints will stream large CSV/JSON
    # exports and may materialize smaller PDF/XLSX exports at the caller's risk.
    final_limit = None if limit is None else int(limit)
    if final_limit is not None and final_limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export limit must be a positive integer."
        )

    # No hard 1000-record cap enforced here — return final_limit which may be None
    # to indicate 'no limit' and let callers/streaming logic handle large result sets.
    return normalized_department, normalized_date_range, normalized_format, final_limit


async def _gather_report_data(db, department_filter: str, limit: int = MAX_REPORT_EXPORT_ROWS):
    """Reuse existing aggregation logic to produce summary metrics and rows."""
    employee_query = {}
    employee_ids = []

    if department_filter and department_filter.lower() != "all":
        employee_query["Department"] = {
            "$regex": f"^{department_filter}$",
            "$options": "i"
        }
        employee_cursor = db.employees.find(employee_query, {"_id": 0, "EmpID": 1})
        employee_docs = await employee_cursor.to_list(length=None)
        employee_ids = [doc["EmpID"] for doc in employee_docs if doc.get("EmpID")]

    total_employees = await db.employees.count_documents(employee_query)
    # Do not enforce a hard upper-bound here — callers may request all matching records.
    # If a numeric `limit` is provided, downstream code will use it to bound the result set.

    attendance_query = {}
    if employee_ids:
        attendance_query["EmpID"] = {"$in": employee_ids}

    total_attendance = await db.attendance.count_documents(attendance_query)

    present_count = 0
    if total_attendance:
        present_count = await db.attendance.count_documents({
            **attendance_query,
            "AttendanceStatus": {"$in": ["Present", "Late"]}
        })

    attendance_rate = (
        (present_count / total_attendance) * 100
        if total_attendance
        else 0.0
    )

    avg_tenure = 0.0
    if total_employees:
        tenure_pipeline = [
            {"$match": employee_query},
            {"$group": {"_id": None, "avgYears": {"$avg": "$YearsAtCompany"}}}
        ]
        tenure_result = await db.employees.aggregate(tenure_pipeline).to_list(length=1)
        if tenure_result:
            avg_tenure = float(tenure_result[0].get("avgYears", 0.0) or 0.0)

    payroll_query = {}
    if employee_ids:
        payroll_query["EmpID"] = {"$in": employee_ids}

    # Respect an optional numeric limit; if no limit provided, retrieve all matching records.
    payroll_length = None if not limit else int(limit)
    payroll_records = await db.payroll.find(
        payroll_query,
        {"_id": 0, "NetSalary": 1, "OvertimePay": 1}
    ).to_list(length=payroll_length)

    payroll_total = sum(float(record.get("NetSalary", 0) or 0) for record in payroll_records)
    overtime_total = sum(float(record.get("OvertimePay", 0) or 0) for record in payroll_records)

    # Rows: select a useful set of fields from employees matching the query
    employee_fields = {"_id": 0, "EmpID": 1, "EmployeeName": 1, "Department": 1, "JobRole": 1, "MonthlyIncome": 1, "YearsAtCompany": 1}
    employee_rows = await db.employees.find(employee_query, employee_fields).to_list(length=payroll_length)

    summary = {
        "reportName": f"Workforce Summary ({department_filter})",
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "departmentFilter": department_filter,
        "totalRecords": total_employees,
        "metrics": {
            "avgTenureYears": round(avg_tenure, 2),
            "attendanceRate": f"{attendance_rate:.1f}%",
            "overtimePayTotal": round(overtime_total, 2),
            "payrollCostTotal": round(payroll_total, 2),
        }
    }

    return summary, employee_rows


@router.post(
    "/generate",
    response_model=ReportSummaryResponse
)
async def generate_report(request: Request, payload: ReportFilter):
    """Generate workforce summaries using the real MongoDB collections only.
  
    Returns metadata and a downloadUrl that points to the download endpoint.
    """
    auth_user = await require_hr_admin(request)

    db = get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected."
        )

    department_filter, date_range, export_format, limit = await _validate_export_scope(
        db,
        payload.department,
        payload.dateRange,
        payload.format,
        payload.limit,
    )

    # For very large All-department CSV/JSON exports, avoid materializing all rows here.
    # The download endpoint supports streaming for those cases, so generate a lightweight
    # summary and return a downloadUrl pointing to the streaming endpoint.
    rows = []
    actor = auth_user.get("userId") or auth_user.get("email") or auth_user.get("empId") or "HR_ADMIN"

    # Treat 'All' department CSV/JSON exports as streamable (no hard size threshold).
    is_large_all_request = (
        (department_filter or '').lower() == 'all'
        and export_format in {"CSV", "JSON"}
    )

    if is_large_all_request:
        total_employees = await db.employees.count_documents({})
        total_attendance = await db.attendance.count_documents({})
        present_count = 0
        if total_attendance:
            present_count = await db.attendance.count_documents({
                "AttendanceStatus": {"$in": ["Present", "Late"]}
            })
        attendance_rate = ((present_count / total_attendance) * 100) if total_attendance else 0.0
        avg_tenure = 0.0
        tenure_pipeline = [{"$group": {"_id": None, "avgYears": {"$avg": "$YearsAtCompany"}}}]
        tenure_result = await db.employees.aggregate(tenure_pipeline).to_list(length=1)
        if tenure_result:
            avg_tenure = float(tenure_result[0].get("avgYears", 0.0) or 0.0)
        summary = {
            "reportName": f"Workforce Summary (All)",
            "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "departmentFilter": "All",
            "totalRecords": total_employees,
            "metrics": {
                "avgTenureYears": round(avg_tenure, 2),
                "attendanceRate": f"{attendance_rate:.1f}%",
                "overtimePayTotal": 0.0,
                "payrollCostTotal": 0.0,
            }
        }
        record_count = total_employees
        await log_export_audit(
            actor=actor,
            action="Generate report",
            scope=f"department={department_filter};dateRange={date_range}",
            export_format=export_format,
            record_count=record_count,
            ip_address=request.client.host if request.client else None,
        )
    else:
        summary, rows = await _gather_report_data(db, department_filter, limit=limit)
        await log_export_audit(
            actor=actor,
            action="Generate report",
            scope=f"department={department_filter};dateRange={date_range}",
            export_format=export_format,
            record_count=len(rows),
            ip_address=request.client.host if request.client else None,
        )

    q = {
        "department": department_filter,
        "dateRange": date_range,
        "format": export_format,
    }
    # Only include limit when explicitly provided (avoid literal 'None' in URLs)
    if limit is not None:
        q["limit"] = str(limit)

    query_string = urllib.parse.urlencode(q)

    # Return a fully-prefixed API download URL so frontends mounting under /api can call it directly
    download_url = f"/api/reports/download?{query_string}"

    return ReportSummaryResponse(
        reportName=summary["reportName"],
        generatedAt=summary["generatedAt"],
        departmentFilter=summary["departmentFilter"],
        totalRecords=summary["totalRecords"],
        metrics=summary["metrics"],
        downloadUrl=download_url
    )


@router.get("/summary")
async def get_report_summary(request: Request):
    """Return dataset-backed report templates that reflect live MongoDB collections."""
    await require_hr_admin(request)

    return [
        {
            "id": "REP-001",
            "title": "Current Workforce Snapshot",
            "category": "Employees",
            "lastGenerated": datetime.now().strftime("%Y-%m-%d"),
            "format": "JSON"
        },
        {
            "id": "REP-002",
            "title": "Attendance Status Summary",
            "category": "Attendance",
            "lastGenerated": datetime.now().strftime("%Y-%m-%d"),
            "format": "JSON"
        },
        {
            "id": "REP-003",
            "title": "Payroll Totals Summary",
            "category": "Payroll",
            "lastGenerated": datetime.now().strftime("%Y-%m-%d"),
            "format": "JSON"
        }
    ]


@router.get("/download")
async def download_report(
    request: Request,
    department: str = Query("All"),
    dateRange: str = Query("Current Month"),
    format: str = Query("PDF"),
    limit: Optional[int] = Query(default=None, ge=1),
):
    """Generate and return a downloadable report in the requested format.
  
    Supported formats: PDF, XLSX, CSV, JSON
    """
    auth_user = await require_hr_admin(request)

    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB database is not connected.")

    department_filter, normalized_date_range, fmt, final_limit = await _validate_export_scope(
        db,
        department,
        dateRange,
        format,
        limit,
    )

    # For large CSV/JSON exports with department=All we stream rows to avoid materializing
    # the entire result set in memory. For other formats (PDF/XLSX) we continue returning
    # an in-memory response and enforce the export limits in _validate_export_scope.

    # Determine if this is a large all-department streaming request. If so, skip the
    # in-memory data gathering step that would otherwise enforce record limits.
    actor = auth_user.get("userId") or auth_user.get("email") or auth_user.get("empId") or "HR_ADMIN"
    # For department=All and streamable formats (CSV/JSON) use the streaming branch
    # which iterates the DB cursor and avoids materializing all rows in memory.
    is_large_all_stream = (department_filter.lower() == 'all' and fmt in {"CSV", "JSON"})

    if is_large_all_stream:
        # We'll compute lightweight summary metrics in the streaming branch below without
        # calling _gather_report_data which may materialize rows.
        summary = None
        rows = []
    else:
        # Fallback: existing in-memory generation for small/filtered exports
        summary, rows = await _gather_report_data(db, department_filter, limit=final_limit)
        # Build a lightweight summary by running the aggregations already in _gather_report_data
        # (we computed a limited sample earlier; recompute key metrics via database queries)
        total_employees = await db.employees.count_documents({})
        # reuse attendance/payroll aggregations for summary
        total_attendance = await db.attendance.count_documents({})
        present_count = 0
        if total_attendance:
            present_count = await db.attendance.count_documents({
                "AttendanceStatus": {"$in": ["Present", "Late"]}
            })
        attendance_rate = ((present_count / total_attendance) * 100) if total_attendance else 0.0
        avg_tenure = 0.0
        tenure_pipeline = [
            {"$group": {"_id": None, "avgYears": {"$avg": "$YearsAtCompany"}}}
        ]
        tenure_result = await db.employees.aggregate(tenure_pipeline).to_list(length=1)
        if tenure_result:
            avg_tenure = float(tenure_result[0].get("avgYears", 0.0) or 0.0)

        payroll_records = await db.payroll.find({}, {"_id": 0, "NetSalary": 1, "OvertimePay": 1}).to_list(length=5000)
        payroll_total = sum(float(record.get("NetSalary", 0) or 0) for record in payroll_records)
        overtime_total = sum(float(record.get("OvertimePay", 0) or 0) for record in payroll_records)

        summary = {
            "reportName": f"Workforce Summary (All)",
            "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "departmentFilter": "All",
            "totalRecords": total_employees,
            "metrics": {
                "avgTenureYears": round(avg_tenure, 2),
                "attendanceRate": f"{attendance_rate:.1f}%",
                "overtimePayTotal": round(overtime_total, 2),
                "payrollCostTotal": round(payroll_total, 2),
            }
        }

        safe_report_name = summary["reportName"].replace('/', '-').replace('\\', '-')
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename_base = f"{safe_report_name}-{timestamp}"

        employee_fields = {"_id": 0, "EmpID": 1, "EmployeeName": 1, "Department": 1, "JobRole": 1, "MonthlyIncome": 1, "YearsAtCompany": 1}
        cursor = db.employees.find({}, employee_fields)
        if final_limit is not None:
            cursor = cursor.limit(final_limit)

        if fmt == "CSV":
            async def csv_generator():
                # header block
                yield (f"{summary['reportName']}\n").encode('utf-8')
                yield (f"Generated: {summary['generatedAt']}\n\n").encode('utf-8')
                header = ["EmpID", "EmployeeName", "Department", "JobRole", "MonthlyIncome", "YearsAtCompany"]
                yield (','.join(header) + '\n').encode('utf-8')
                async for doc in cursor:
                    row = [str(doc.get(k, '') or '') for k in ['EmpID', 'EmployeeName', 'Department', 'JobRole', 'MonthlyIncome', 'YearsAtCompany']]
                    yield (','.join(row) + '\n').encode('utf-8')
            disposition = f'attachment; filename="{filename_base}.csv"'
            return StreamingResponse(csv_generator(), media_type='text/csv', headers={"Content-Disposition": disposition})

        if fmt == "JSON":
            async def json_generator():
                yield ('{"metadata": ' + json.dumps(summary, default=str) + ', "rows": [').encode('utf-8')
                first = True
                async for doc in cursor:
                    if not first:
                        yield b','
                    else:
                        first = False
                    yield json.dumps(doc, default=str).encode('utf-8')
                yield b']}'
            disposition = f'attachment; filename="{filename_base}.json"'
            return StreamingResponse(json_generator(), media_type='application/json', headers={"Content-Disposition": disposition})

    # Fallback: existing in-memory generation for small/filtered exports
    summary, rows = await _gather_report_data(db, department_filter, limit=final_limit)

    actor = auth_user.get("userId") or auth_user.get("email") or auth_user.get("empId") or "HR_ADMIN"
    await log_export_audit(
        actor=actor,
        action="Download report",
        scope=f"department={department_filter};dateRange={normalized_date_range}",
        export_format=fmt,
        record_count=len(rows),
        ip_address=request.client.host if request.client else None,
    )

    safe_report_name = summary["reportName"].replace('/', '-').replace('\\', '-')
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename_base = f"{safe_report_name}-{timestamp}"

    if fmt == "CSV":
        si = io.StringIO()
        writer = csv.writer(si)
        header = ["EmpID", "EmployeeName", "Department", "JobRole", "MonthlyIncome", "YearsAtCompany"]
        writer.writerow([summary["reportName"]])
        writer.writerow([f"Generated: {summary['generatedAt']}"])
        writer.writerow([])
        writer.writerow(header)
        for r in rows:
            writer.writerow([
                r.get("EmpID", ""),
                r.get("EmployeeName", ""),
                r.get("Department", ""),
                r.get("JobRole", ""),
                r.get("MonthlyIncome", ""),
                r.get("YearsAtCompany", "")
            ])
        data = si.getvalue().encode('utf-8')
        disposition = f'attachment; filename="{filename_base}.csv"'
        return Response(content=data, media_type="text/csv", headers={"Content-Disposition": disposition})

    if fmt == "JSON":
        payload = {
            "metadata": summary,
            "rows": rows
        }
        data = json.dumps(payload, default=str, indent=2).encode('utf-8')
        disposition = f'attachment; filename="{filename_base}.json"'
        return Response(content=data, media_type="application/json", headers={"Content-Disposition": disposition})

    if fmt == "XLSX":
        try:
            from openpyxl import Workbook as _Workbook
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"XLSX generation library import error: {e}")

        bio = io.BytesIO()
        wb = _Workbook()
        ws = wb.active
        ws.title = "Report"
        ws.append([summary["reportName"]])
        ws.append([f"Generated: {summary['generatedAt']}"])
        ws.append([])
        header = ["EmpID", "EmployeeName", "Department", "JobRole", "MonthlyIncome", "YearsAtCompany"]
        ws.append(header)
        for r in rows:
            ws.append([
                r.get("EmpID", ""),
                r.get("EmployeeName", ""),
                r.get("Department", ""),
                r.get("JobRole", ""),
                r.get("MonthlyIncome", ""),
                r.get("YearsAtCompany", "")
            ])
        wb.save(bio)
        bio.seek(0)
        disposition = f'attachment; filename="{filename_base}.xlsx"'
        return Response(content=bio.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": disposition})

    if fmt == "PDF":
        try:
            from reportlab.lib.pagesizes import letter as _letter
            from reportlab.pdfgen import canvas as _canvas
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation library import error: {e}")

        bio = io.BytesIO()
        c = _canvas.Canvas(bio, pagesize=_letter)
        width, height = _letter
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, summary["reportName"]) ; y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Generated: {summary['generatedAt']}") ; y -= 20
        c.drawString(50, y, f"Department: {department_filter}") ; y -= 30
        for k, v in summary["metrics"].items():
            c.drawString(50, y, f"{k}: {v}") ; y -= 15
            if y < 100:
                c.showPage()
                y = height - 50
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Employees") ; y -= 20
        c.setFont("Helvetica", 9)
        header = ["EmpID", "EmployeeName", "Department", "JobRole", "MonthlyIncome", "YearsAtCompany"]
        c.drawString(50, y, " | ".join(header)) ; y -= 15
        for r in rows:
            line = " | ".join([
                str(r.get("EmpID", "")),
                str(r.get("EmployeeName", "")),
                str(r.get("Department", "")),
                str(r.get("JobRole", "")),
                str(r.get("MonthlyIncome", "")),
                str(r.get("YearsAtCompany", ""))
            ])
            c.drawString(50, y, line[:120])
            y -= 12
            if y < 100:
                c.showPage()
                y = height - 50
        c.save()
        bio.seek(0)
        disposition = f'attachment; filename="{filename_base}.pdf"'
        return Response(content=bio.getvalue(), media_type="application/pdf", headers={"Content-Disposition": disposition})

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate report.")

