import math
import re
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone

from backend.app.database import get_database
from backend.app.config import settings
from backend.app.models.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    AttendanceCheckIn,
    AttendanceCheckOut,
    LeaveRequestBase,
    LeaveStatusUpdate,
    ShiftRequestBase,
    ShiftStatusUpdate,
    TimesheetBase,
    AuditLogBase,
    AuditLogCreate,
    PerformanceBase,
    PerformanceUpdate,
    NotificationCreate,
    AIPredictionBase
)

logger = logging.getLogger("uvicorn.error")


# ==========================================================================
# Document Normalizers
# ==========================================================================

def normalize_employee(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]

    if "employeeId" in d and "empId" not in d:
        d["empId"] = d["employeeId"]

    if "EmployeeName" in d:
        full_name = str(d["EmployeeName"]).strip()
        parts = full_name.split()
        if parts:
            d["firstName"] = parts[0]
            d["lastName"] = " ".join(parts[1:]) if len(parts) > 1 else None

    if "Email" in d and "email" not in d:
        d["email"] = d["Email"]

    if "Phone" in d and "phone" not in d:
        d["phone"] = d["Phone"]

    if "Age" in d and "age" not in d:
        d["age"] = d["Age"]

    if "Gender" in d and "gender" not in d:
        d["gender"] = d["Gender"]

    if "Department" in d and "department" not in d:
        d["department"] = d["Department"]

    if "JobRole" in d and "jobRole" not in d:
        d["jobRole"] = d["JobRole"]

    if "JobLevel" in d and "jobLevel" not in d:
        d["jobLevel"] = d["JobLevel"]

    if "ManagerID" in d and "managerId" not in d:
        d["managerId"] = d["ManagerID"]
    if "managerId" in d and "managerEmpId" not in d:
        d["managerEmpId"] = d["managerId"]
    if "ManagerID" in d and "managerEmpId" not in d:
        d["managerEmpId"] = d["ManagerID"]
    if "managerEmpId" in d and "managerId" not in d:
        d["managerId"] = d["managerEmpId"]

    if "Location" in d and "location" not in d:
        d["location"] = d["Location"]

    if "EmploymentStatus" in d and "status" not in d:
        d["status"] = d["EmploymentStatus"]

    if "MonthlyIncome" in d and "monthlyIncome" not in d:
        d["monthlyIncome"] = d["MonthlyIncome"]
    elif "salary" in d and "monthlyIncome" not in d:
        d["monthlyIncome"] = d["salary"]

    if "YearsAtCompany" in d and "yearsAtCompany" not in d:
        d["yearsAtCompany"] = d["YearsAtCompany"]

    if "YearsWithCurrManager" in d and "yearsWithManager" not in d:
        d["yearsWithManager"] = d["YearsWithCurrManager"]

    if "WorkLifeBalance" in d and "workLifeBalanceScore" not in d:
        d["workLifeBalanceScore"] = d["WorkLifeBalance"]

    if "JobSatisfaction" in d and "jobSatisfactionScore" not in d:
        d["jobSatisfactionScore"] = d["JobSatisfaction"]

    if "EnvironmentSatisfaction" in d and "environmentSatisfactionScore" not in d:
        d["environmentSatisfactionScore"] = d["EnvironmentSatisfaction"]

    if "RelationshipSatisfaction" in d and "relationshipSatisfactionScore" not in d:
        d["relationshipSatisfactionScore"] = d["RelationshipSatisfaction"]

    if "Education" in d and "education" not in d:
        d["education"] = str(d["Education"])

    if "EducationField" in d and "educationField" not in d:
        d["educationField"] = d["EducationField"]

    if "Designation" in d and "designation" not in d:
        d["designation"] = d["Designation"]
    elif "JobRole" in d and "designation" not in d:
        d["designation"] = d["JobRole"]

    # Ensure skills is always represented as a list in API responses
    # Convert null -> empty list, and coerce comma-separated strings into lists
    skills_val = d.get("skills", None)
    if skills_val is None:
        d["skills"] = []
    elif isinstance(skills_val, str):
        d["skills"] = [s.strip() for s in skills_val.split(",") if s.strip()]

    return d


def normalize_attendance(
    doc: Dict[str, Any],
    employee: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]
    elif "employeeId" in d and "empId" not in d:
        d["empId"] = d["employeeId"]

    if "Date" in d and "date" not in d:
        d["date"] = d["Date"]

    if "CheckIn" in d and "checkIn" not in d:
        d["checkIn"] = d["CheckIn"]

    if "CheckOut" in d and "checkOut" not in d:
        d["checkOut"] = d["CheckOut"]

    if "WorkingHours" in d and "workingHours" not in d:
        d["workingHours"] = d["WorkingHours"]

    if "AttendanceStatus" in d and "status" not in d:
        d["status"] = d["AttendanceStatus"]

    if "LateArrival" in d:
        d["isAnomaly"] = bool(d["LateArrival"])
        d["anomalyReason"] = "Late arrival" if d["LateArrival"] else None

    if "GPSVerified" in d and "gpsVerified" not in d:
        d["gpsVerified"] = d["GPSVerified"]
    if "DistanceFromOffice" in d and "distanceFromOffice" not in d:
        d["distanceFromOffice"] = d["DistanceFromOffice"]
    if "GeofenceStatus" in d and "geofenceStatus" not in d:
        d["geofenceStatus"] = d["GeofenceStatus"]
    if "Latitude" in d and "latitude" not in d:
        d["latitude"] = d["Latitude"]
    if "Longitude" in d and "longitude" not in d:
        d["longitude"] = d["Longitude"]
    if "WorkMode" in d and "workMode" not in d:
        d["workMode"] = d["WorkMode"]
    if "WorkContext" in d and "workContext" not in d:
        d["workContext"] = d["WorkContext"]
    if "AllowedVerificationMethods" in d and "allowedVerificationMethods" not in d:
        d["allowedVerificationMethods"] = d["AllowedVerificationMethods"]
    if "VerificationMethod" in d and "verificationMethod" not in d:
        d["verificationMethod"] = d["VerificationMethod"]
    if "VerificationStatus" in d and "verificationStatus" not in d:
        d["verificationStatus"] = d["VerificationStatus"]
    if "Verification" in d and "verification" not in d:
        d["verification"] = d["Verification"]
    if "LocationAudit" in d and "locationAudit" not in d:
        d["locationAudit"] = d["LocationAudit"]
    if "AttendanceException" in d and "attendanceException" not in d:
        d["attendanceException"] = d["AttendanceException"]
    if "ReviewStatus" in d and "reviewStatus" not in d:
        d["reviewStatus"] = d["ReviewStatus"]

    if employee:
        first_name = employee.get("firstName")
        last_name = employee.get("lastName")
        full_name = " ".join(part for part in [first_name, last_name] if part)
        if full_name:
            d["empName"] = full_name

        if "department" in employee and employee.get("department") is not None:
            d["department"] = employee["department"]

        if "avatar" in employee and employee.get("avatar") is not None:
            d["avatar"] = employee["avatar"]

    if "id" not in d and "_id" in d:
        d["id"] = str(d["_id"])

    return d


def normalize_leave(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]
    elif "employeeId" in d and "empId" not in d:
        d["empId"] = d["employeeId"]

    if "LeaveType" in d and "leaveType" not in d:
        d["leaveType"] = d["LeaveType"]

    if "StartDate" in d and "startDate" not in d:
        d["startDate"] = d["StartDate"]

    if "EndDate" in d and "endDate" not in d:
        d["endDate"] = d["EndDate"]

    if "Status" in d and "status" not in d:
        d["status"] = d["Status"]

    if "LeaveBalance" in d and "leaveBalance" not in d:
        d["leaveBalance"] = d["LeaveBalance"]

    if "days" not in d and d.get("StartDate") and d.get("EndDate"):
        try:
            start = datetime.strptime(d["StartDate"], "%Y-%m-%d")
            end = datetime.strptime(d["EndDate"], "%Y-%m-%d")
            d["days"] = (end - start).days + 1
        except Exception:
            d["days"] = None

    # Ensure a stable canonical API-facing id for leave records.
    # Prefer the MongoDB _id when available (canonical identifier). Expose any legacy RequestID
    # separately as `requestId` for display-only purposes. This guarantees the frontend always
    # receives `id` as the canonical identifier to use for update/delete operations.
    if "id" not in d:
        if d.get("_id"):
            d["id"] = str(d.get("_id"))
        elif d.get("RequestID"):
            # Fallback to legacy RequestID only when _id is missing (rare)
            d["id"] = str(d.get("RequestID"))

    # Always expose the legacy RequestID (if present) as requestId for UI/display but do not
    # treat it as the canonical route identifier.
    if "requestId" not in d and d.get("RequestID"):
        d["requestId"] = str(d.get("RequestID"))

    # Map Reason (DB) -> reason (API)
    if "reason" not in d and d.get("Reason") is not None:
        d["reason"] = d.get("Reason")

    # AppliedOn / AppliedDate -> appliedOn (prefer AppliedOn)
    if "appliedOn" not in d:
        applied_on = d.get("AppliedOn") or d.get("AppliedDate")
        if applied_on:
            d["appliedOn"] = applied_on

    # Expose appliedDate explicitly when present
    if "appliedDate" not in d and d.get("AppliedDate") is not None:
        d["appliedDate"] = d.get("AppliedDate")

    # ManagerComments -> approverComments
    if "approverComments" not in d and d.get("ManagerComments") is not None:
        d["approverComments"] = d.get("ManagerComments")

    for field_name, legacy_name in {
        "decisionByUserId": "decisionByUserId",
        "decisionByEmpId": "decisionByEmpId",
        "decisionByName": "decisionByName",
        "decisionRole": "decisionRole",
        "decisionAt": "decisionAt",
        "decisionComments": "decisionComments",
    }.items():
        if field_name not in d and legacy_name in d and d.get(legacy_name) is not None:
            d[field_name] = d[legacy_name]

    return d


def normalize_shift(
    doc: Dict[str, Any],
    employee: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]

    if "ShiftName" in d and "shiftName" not in d:
        d["shiftName"] = d["ShiftName"]

    if "ShiftStart" in d and "shiftStart" not in d:
        d["shiftStart"] = d["ShiftStart"]

    if "ShiftEnd" in d and "shiftEnd" not in d:
        d["shiftEnd"] = d["ShiftEnd"]

    if "OvertimeHours" in d and "overtimeHours" not in d:
        d["overtimeHours"] = d["OvertimeHours"]

    if "ShiftDate" in d and "requestedDate" not in d:
        d["requestedDate"] = d["ShiftDate"]
    if "RequestedDate" in d and "requestedDate" not in d:
        d["requestedDate"] = d["RequestedDate"]

    if "status" not in d:
        raw_status = d.get("ShiftSwapStatus")
        if raw_status is not None:
            val = str(raw_status).strip().title()
            if val in ShiftService.VALID_STATUSES:
                d["status"] = val
            else:
                d["status"] = val
        elif "ShiftSwapApproved" in d:
            d["status"] = "Approved" if d["ShiftSwapApproved"] else "Pending"

    reason_aliases = ["Reason", "RequestReason", "ShiftReason", "EmployeeReason", "Comments", "Remarks"]
    for alias in reason_aliases:
        if alias in d and "reason" not in d and d.get(alias) is not None:
            d["reason"] = d[alias]
            break

    if "AppliedOn" in d and "appliedOn" not in d:
        d["appliedOn"] = d["AppliedOn"]

    if "ShiftID" in d and "id" not in d:
        d["id"] = d["ShiftID"]
    if "RequestID" in d and "id" not in d:
        d["id"] = d["RequestID"]

    if "ManagerComments" in d and "approverComments" not in d:
        d["approverComments"] = d["ManagerComments"]
    if "ApproverComments" in d and "approverComments" not in d:
        d["approverComments"] = d["ApproverComments"]

    for field_name, legacy_name in {
        "decisionByUserId": "decisionByUserId",
        "decisionByEmpId": "decisionByEmpId",
        "decisionByName": "decisionByName",
        "decisionRole": "decisionRole",
        "decisionAt": "decisionAt",
        "decisionComments": "decisionComments",
    }.items():
        if field_name not in d and legacy_name in d and d.get(legacy_name) is not None:
            d[field_name] = d[legacy_name]

    if "Approver" in d and "approverName" not in d:
        d["approverName"] = d["Approver"]
    if "Manager" in d and "approverName" not in d:
        d["approverName"] = d["Manager"]

    if employee:
        first_name = employee.get("firstName")
        last_name = employee.get("lastName")
        full_name = " ".join(part for part in [first_name, last_name] if part)
        if full_name:
            d["empName"] = full_name
        if "department" in employee and employee.get("department") is not None:
            d["department"] = employee["department"]

    if "requestedShift" not in d and d.get("shiftName"):
        start = d.get("shiftStart", "")
        end = d.get("shiftEnd", "")
        if start or end:
            d["requestedShift"] = f"{d['shiftName']} ({start} - {end})".strip()
        else:
            d["requestedShift"] = d["shiftName"]
    if "RequestedShift" in d and "requestedShift" not in d:
        d["requestedShift"] = d["RequestedShift"]

    return d


def normalize_timesheet(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]

    if "Date" in d and "date" not in d:
        d["date"] = d["Date"]

    if "Project" in d and "projectName" not in d:
        d["projectName"] = d["Project"]

    if "HoursWorked" in d and "hoursLogged" not in d:
        d["hoursLogged"] = d["HoursWorked"]

    if "ClientBillingHours" in d and "clientBillingHours" not in d:
        d["clientBillingHours"] = d["ClientBillingHours"]

    if "Status" in d and "status" not in d:
        d["status"] = d["Status"]

    if "isBillable" not in d and "clientBillingHours" in d:
        d["isBillable"] = bool(d["clientBillingHours"] > 0)

    if "id" not in d and "_id" in d:
        d["id"] = str(d["_id"])

    return d


def normalize_payroll(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]

    if "BasicSalary" in d and "baseSalary" not in d:
        d["baseSalary"] = d["BasicSalary"]

    if "OvertimePay" in d and "overtimePay" not in d:
        d["overtimePay"] = d["OvertimePay"]

    if "Bonus" in d and "performanceBonus" not in d:
        d["performanceBonus"] = d["Bonus"]

    if "Tax" in d and "taxDeductions" not in d:
        d["taxDeductions"] = d["Tax"]

    if "NetSalary" in d and "netPay" not in d:
        d["netPay"] = d["NetSalary"]

    if "PayrollMonth" in d and "month" not in d:
        d["month"] = d["PayrollMonth"]

    if "grossEarnings" not in d:
        base = float(d.get("baseSalary", 0) or 0)
        overtime = float(d.get("overtimePay", 0) or 0)
        bonus = float(d.get("performanceBonus", 0) or 0)
        d["grossEarnings"] = base + overtime + bonus

    if "incentives" not in d:
        d["incentives"] = None

    if "attendanceDeductions" not in d:
        d["attendanceDeductions"] = None

    if "id" not in d and "_id" in d:
        d["id"] = str(d["_id"])

    return d


def normalize_performance(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]

    if "KPI" in d and "performanceScore" not in d:
        d["performanceScore"] = d["KPI"]

    if "GoalCompletion" in d and "kpiCompletionRate" not in d:
        d["kpiCompletionRate"] = d["GoalCompletion"]

    if "ProductivityScore" in d and "productivityScore" not in d:
        d["productivityScore"] = d["ProductivityScore"]

    if "PerformanceRating" in d and "performanceRating" not in d:
        d["performanceRating"] = d["PerformanceRating"]

    if "ReviewDate" in d and "reviewDate" not in d:
        d["reviewDate"] = d["ReviewDate"]

    if "promotionRecommended" not in d and "performanceRating" in d:
        d["promotionRecommended"] = d["performanceRating"] >= 4

    if "id" not in d and "_id" in d:
        d["id"] = str(d["_id"])

    return d


def normalize_notification(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    if "EmpID" in d and "empId" not in d:
        d["empId"] = d["EmpID"]

    if "Title" in d and "title" not in d:
        d["title"] = d["Title"]

    if "Type" in d and "type" not in d:
        d["type"] = d["Type"]

    if "notificationType" not in d and "Type" in d:
        d["notificationType"] = d["Type"]

    if "Message" in d and "message" not in d:
        d["message"] = d["Message"]

    if "Status" in d and "status" not in d:
        d["status"] = d["Status"]

    if "Status" in d and "isRead" not in d:
        d["isRead"] = str(d["Status"]).lower() == "read"
    elif "isRead" in d and "status" not in d:
        d["status"] = "Read" if bool(d["isRead"]) else "Unread"

    if "NotificationDate" in d and "timestamp" not in d:
        d["timestamp"] = d["NotificationDate"]

    if "relatedEntityType" not in d and "relatedEntityType" in d:
        d["relatedEntityType"] = d["relatedEntityType"]
    if "relatedEntityId" not in d and "relatedEntityId" in d:
        d["relatedEntityId"] = d["relatedEntityId"]

    if "title" not in d and "type" in d:
        d["title"] = d["type"]

    if "priority" not in d:
        d["priority"] = None

    if "metadata" not in d:
        d["metadata"] = {}

    if "id" not in d and "_id" in d:
        d["id"] = str(d["_id"])
        d.pop("_id", None)

    return d


def normalize_audit_log(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc

    d = dict(doc)

    # Backwards-compat: older audit records may use userId/userRole
    # while newer ones use actor. Synthesize a readable actor string.
    if "userId" in d and "actor" not in d:
        role = d.get("userRole", "User")
        d["actor"] = f"{d['userId']} ({role})"

    # Ensure a stable API-facing id exists and is usable.
    # Accept an explicit 'id' only when it contains a meaningful value
    # (non-null, non-empty string). If the id is missing/None/empty,
    # fall back to the MongoDB _id for stability. After deriving the
    # public id, remove the raw MongoDB _id to avoid leaking internal
    # identifiers. Only generate a random fallback id when neither an
    # explicit id nor a MongoDB _id exists (rare legacy case).

    raw_id = d.get("id") if "id" in d else None
    usable_id = None
    if raw_id is not None:
        # Treat non-empty strings as usable; other falsy values are not usable
        if isinstance(raw_id, str):
            if raw_id.strip() != "":
                usable_id = raw_id.strip()
        else:
            # Non-string but present (e.g., numeric) — convert to string
            usable_id = str(raw_id)

    if usable_id:
        d["id"] = usable_id
        # Remove internal _id if present to avoid leaking it
        d.pop("_id", None)
    else:
        # id missing or null/empty — prefer stable MongoDB _id when available
        if "_id" in d and d.get("_id") is not None:
            d["id"] = str(d["_id"])
            d.pop("_id", None)
        else:
            # Very rare legacy record without any identifier: synthesize a short stable id
            d["id"] = f"AUD-{uuid.uuid4().hex[:6].upper()}"

    return d


async def log_export_audit(
    actor: str,
    action: str,
    scope: str,
    export_format: str,
    record_count: int,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist a minimal audit record for exports without storing any payroll contents."""
    from backend.app.models.schemas import AuditLogCreate

    audit_action = (
        f"{action} scope={scope} format={export_format} count={record_count}"
    )
    log = AuditLogCreate(
        actor=actor,
        action=audit_action,
        module="Exports",
        ipAddress=ip_address or "unknown",
        status="SUCCESS",
    )
    return await AuditService.create(log)


def normalize_ai_prediction(    doc: Dict[str, Any]
) -> Dict[str, Any]:

    if not doc:
        return doc

    d = dict(doc)

    # ---------------------------------------------------------
    # Employee ID
    # ---------------------------------------------------------

    if "EmpID" in d:
        d["empId"] = d["EmpID"]

    elif "employeeId" in d and "empId" not in d:
        d["empId"] = d["employeeId"]

    # ---------------------------------------------------------
    # AI Prediction fields
    # ---------------------------------------------------------

    if "AttritionRisk" in d:
        d["attritionRisk"] = d["AttritionRisk"]

    if "SkillGapScore" in d:
        d["skillGapScore"] = d["SkillGapScore"]

    if "WorkforceHealthScore" in d:
        d["workforceHealthScore"] = (
            d["WorkforceHealthScore"]
        )

    if "Recommendation" in d:
        d["recommendation"] = d["Recommendation"]

    if "PredictionDate" in d:
        d["predictionDate"] = d["PredictionDate"]

    # ---------------------------------------------------------
    # Stable API ID
    # ---------------------------------------------------------

    if "id" not in d:

        if "_id" in d:
            d["id"] = str(d["_id"])

        else:
            d["id"] = (
                f"AI-{d.get('empId', 'UNKNOWN')}-"
                f"{d.get('predictionDate', 'UNKNOWN')}"
            )

    return d


# ==========================================================================
# 1. Employee Service
# ==========================================================================

class MissingEmployeeCounterError(RuntimeError):
    """Raised when the counters.employee_id document is missing.

    This is a specific subclass so callers can distinguish an uninitialized
    employee counter from other RuntimeError conditions (like DB connection).
    """


class EmployeeService:
    @staticmethod
    async def count_total() -> int:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        return await db.employees.count_documents({})

    @staticmethod
    async def count_active() -> int:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        return await db.employees.count_documents({"EmploymentStatus": {"$regex": r"^active$", "$options": "i"}})


    # MongoDB field names -> API field names
    SORT_FIELD_MAP = {
        "empId": "EmpID",
        "firstName": "EmployeeName",
        "lastName": "EmployeeName",
        "department": "Department",
        "jobRole": "JobRole",
        "monthlyIncome": "MonthlyIncome",
        "status": "EmploymentStatus",
        "age": "Age",
        "jobLevel": "JobLevel",
        "location": "Location",
        "yearsAtCompany": "YearsAtCompany"
    }

    # API field names -> MongoDB field names
    FIELD_MAP = {
        "empId": "EmpID",
        "email": "Email",
        "phone": "Phone",
        "age": "Age",
        "gender": "Gender",
        "department": "Department",
        "jobRole": "JobRole",
        "education": "Education",
        "educationField": "EducationField",
        "monthlyIncome": "MonthlyIncome",
        "jobLevel": "JobLevel",
        "yearsAtCompany": "YearsAtCompany",
        "workLifeBalanceScore": "WorkLifeBalance",
        "jobSatisfactionScore": "JobSatisfaction",
        "environmentSatisfactionScore": "EnvironmentSatisfaction",
        "relationshipSatisfactionScore": "RelationshipSatisfaction",
        "yearsWithManager": "YearsWithCurrManager",
        "status": "EmploymentStatus",
        "managerId": "ManagerID",
        "location": "Location"
    }

    # ----------------------------------------------------------------------
    # GET ALL EMPLOYEES
    # ----------------------------------------------------------------------

    @staticmethod
    async def get_all(
        department: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "empId",
        sort_order: str = "asc",
        page: int = 1,
        size: int = 50,
        emp_id: Optional[str] = None,
        emp_ids: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Build MongoDB query
        # ---------------------------------------------------------

        query: Dict[str, Any] = {}

        # ---------------------------------------------------------
        # Department filter
        # ---------------------------------------------------------

        if department and department.lower() != "all":
            query["Department"] = {
                "$regex": f"^{department}$",
                "$options": "i"
            }

        # ---------------------------------------------------------
        # Employment status filter
        # ---------------------------------------------------------

        if status and status.lower() != "all":
            query["EmploymentStatus"] = {
                "$regex": f"^{status}$",
                "$options": "i"
            }

        if emp_ids:
            query["EmpID"] = {"$in": [str(item).strip() for item in emp_ids if str(item).strip()]}
        elif emp_id and str(emp_id).strip():
            query["EmpID"] = str(emp_id).strip()

        # ---------------------------------------------------------
        # Search
        # ---------------------------------------------------------

        if search:
            query["$or"] = [
                {
                    "EmpID": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "EmployeeName": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "Email": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "Department": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "JobRole": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "Location": {
                        "$regex": search,
                        "$options": "i"
                    }
                }
            ]

        # ---------------------------------------------------------
        # Count matching employees
        # ---------------------------------------------------------

        total = await db.employees.count_documents(
            query
        )

        # ---------------------------------------------------------
        # Sorting
        # ---------------------------------------------------------

        order_val = (
            1
            if sort_order.lower() == "asc"
            else -1
        )

        mongo_sort_field = EmployeeService.SORT_FIELD_MAP.get(
            sort_by,
            "EmpID"
        )

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------

        skip = (page - 1) * size

        cursor = (
            db.employees
            .find(
                query,
                {"_id": 0}
            )
            .sort(
                mongo_sort_field,
                order_val
            )
            .skip(skip)
            .limit(size)
        )

        items = await cursor.to_list(
            length=size
        )

        # ---------------------------------------------------------
        # Normalize MongoDB documents -> API format
        # ---------------------------------------------------------

        normalized_items = [
            normalize_employee(item)
            for item in items
        ]

        # ---------------------------------------------------------
        # Batch enrichment: performance, AI predictions, payroll
        # Use a single batched query per related collection to avoid N+1
        # ---------------------------------------------------------
        emp_ids = [e.get('empId') for e in normalized_items if e.get('empId')]
        if emp_ids:
            try:
                # Performance documents for these employees
                perf_docs = await db.performance.find({"EmpID": {"$in": emp_ids}}, {"_id": 0}).to_list(length=len(emp_ids))
                perf_raw_map = {d.get('EmpID'): d for d in perf_docs if d and d.get('EmpID')}
                perf_norm_map = {normalize_performance(d).get('empId'): normalize_performance(d) for d in perf_docs if d}

                # AI prediction documents
                ai_docs = await db.ai_predictions.find({"EmpID": {"$in": emp_ids}}, {"_id": 0}).to_list(length=len(emp_ids))
                ai_norm_map = {normalize_ai_prediction(d).get('empId'): normalize_ai_prediction(d) for d in ai_docs if d}

                # Payroll documents: fetch recent entries and pick the latest per employee
                payroll_docs = await db.payroll.find({"EmpID": {"$in": emp_ids}}, {"_id": 0}).to_list(length=max(50, len(emp_ids)*3))
                payroll_map = {}
                for doc in payroll_docs:
                    if not doc:
                        continue
                    empid = doc.get('EmpID')
                    norm = normalize_payroll(doc)
                    if empid in payroll_map:
                        # choose latest by month string (expects YYYY-MM or lexicographically comparable)
                        existing_month = payroll_map[empid].get('month') or ''
                        this_month = norm.get('month') or ''
                        if this_month and this_month > existing_month:
                            payroll_map[empid] = norm
                    else:
                        payroll_map[empid] = norm

                # Merge normalized related fields into employee responses
                for emp in normalized_items:
                    eid = emp.get('empId')
                    if not eid:
                        continue

                    # Performance
                    pnorm = perf_norm_map.get(eid)
                    praw = perf_raw_map.get(eid)
                    if pnorm:
                        for key in [
                            'performanceScore',
                            'productivityScore',
                            'kpiCompletionRate',
                            'performanceRating',
                            'reviewDate'
                        ]:
                            if key in pnorm:
                                emp[key] = pnorm.get(key)

                        # goalsCompleted/totalGoals come from raw document fields when present
                        if praw and praw.get('GoalCompletion') is not None:
                            emp['goalsCompleted'] = praw.get('GoalCompletion')
                        if praw and praw.get('TotalGoals') is not None:
                            emp['totalGoals'] = praw.get('TotalGoals')
                        else:
                            emp.setdefault('totalGoals', None)

                        if 'promotionRecommended' in pnorm:
                            emp['promotionRecommended'] = pnorm.get('promotionRecommended')

                    # AI prediction
                    a = ai_norm_map.get(eid)
                    if a:
                        if a.get('recommendation'):
                            emp['aiFeedback'] = a.get('recommendation')
                        if a.get('attritionRisk') is not None:
                            emp['attritionRisk'] = a.get('attritionRisk')

                    # Payroll (latest)
                    pay = payroll_map.get(eid)
                    if pay:
                        if 'month' in pay:
                            emp['lastPayrollMonth'] = pay.get('month')
                        if 'netPay' in pay:
                            emp['lastNetPay'] = pay.get('netPay')

            except Exception as _e:
                logger.warning(f"Failed to batch-enrich employees: {_e}")

        return normalized_items, total

    # ----------------------------------------------------------------------
    # GET EMPLOYEE BY ID
    # ----------------------------------------------------------------------

    @staticmethod
    async def get_by_id(
        emp_id: str
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        emp = await db.employees.find_one(
            {
                "EmpID": emp_id
            },
            {"_id": 0}
        )

        if emp:
            return normalize_employee(emp)

        return None

    # ----------------------------------------------------------------------
    # CREATE EMPLOYEE
    # ----------------------------------------------------------------------

    @staticmethod
    async def create(
        data: EmployeeCreate
    ) -> Dict[str, Any]:

        from pymongo.errors import DuplicateKeyError

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Determine EmpID: use client-supplied if present, else
        # generate server-side using counters.employee_id.
        # Note: upsert is intentionally False to avoid creating
        # the counter document automatically. The deployment
        # operator should initialize counters.employee_id to
        # the current max (e.g., seq=10000) before enabling generation.
        # ---------------------------------------------------------

        emp_id = getattr(data, 'empId', None)

        if not emp_id:
            # Attempt to atomically get the next sequence without upsert
            from pymongo import ReturnDocument

            counter = await db.counters.find_one_and_update(
                {"_id": "employee_id"},
                {"$inc": {"seq": 1}},
                upsert=False,
                return_document=ReturnDocument.AFTER
            )

            if not counter or 'seq' not in counter:
                # Raise a specific exception so the router can return 503
                raise MissingEmployeeCounterError(
                    "Employee ID counter is not initialized. "
                    "Please initialize counters.employee_id with the current sequence before enabling server-side EmpID generation."
                )

            sequence = counter['seq']
            emp_id = f"EMP{sequence:06d}"

        # ---------------------------------------------------------
        # Convert API format -> MongoDB format
        # ---------------------------------------------------------

        doc = {
            "EmpID": emp_id,
            "EmployeeName": (
                f"{data.firstName} {data.lastName}"
            ).strip(),
            "Email": str(data.email) if data.email is not None else None,
            "Phone": data.phone,
            "Age": data.age,
            "Gender": data.gender,
            "Department": data.department,
            "JobRole": data.jobRole,
            "Education": data.education,
            "EducationField": data.educationField,
            "MonthlyIncome": data.monthlyIncome,
            "JobLevel": data.jobLevel,
            "ManagerID": data.managerId,
            "Location": data.location,
            "EmploymentStatus": data.status,
            "YearsAtCompany": data.yearsAtCompany,
            "YearsWithCurrManager": data.yearsWithManager,
            "WorkLifeBalance": data.workLifeBalanceScore,
            "JobSatisfaction": data.jobSatisfactionScore,
            "EnvironmentSatisfaction": (
                data.environmentSatisfactionScore
            ),
            "RelationshipSatisfaction": (
                data.relationshipSatisfactionScore
            ),
            "EmploymentType": "Full-Time",
            "Role": "Employee",
            "Attrition": "No",
            "JoiningDate": "",
            "ExitDate": "N/A"
        }

        # ---------------------------------------------------------
        # Insert into MongoDB with explicit DuplicateKeyError handling
        # ---------------------------------------------------------
        try:
            await db.employees.insert_one(doc)
        except DuplicateKeyError as exc:
            # Do not overwrite existing employees; surface a clear error
            raise ValueError(f"Employee ID '{emp_id}' already exists.") from exc

        # ---------------------------------------------------------
        # Return API format
        # ---------------------------------------------------------

        return normalize_employee(
            doc
        )

    # ----------------------------------------------------------------------
    # UPDATE EMPLOYEE
    # ----------------------------------------------------------------------

    @staticmethod
    async def update(
        emp_id: str,
        data: EmployeeUpdate
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Get API fields supplied by client
        # ---------------------------------------------------------

        incoming = {
            key: value
            for key, value in data.model_dump().items()
            if value is not None
        }

        if not incoming:
            return await EmployeeService.get_by_id(
                emp_id
            )

        # ---------------------------------------------------------
        # Convert API field names -> MongoDB field names
        # ---------------------------------------------------------

        update_fields: Dict[str, Any] = {}

        for api_field, value in incoming.items():

            mongo_field = EmployeeService.FIELD_MAP.get(
                api_field
            )

            if mongo_field:
                update_fields[mongo_field] = value

        # ---------------------------------------------------------
        # Handle firstName / lastName
        #
        # MongoDB stores complete name in EmployeeName.
        # ---------------------------------------------------------

        if (
            "firstName" in incoming
            or "lastName" in incoming
        ):

            existing = await db.employees.find_one(
                {
                    "EmpID": emp_id
                },
                {
                    "_id": 0,
                    "EmployeeName": 1
                }
            )

            if not existing:
                return None

            current_name = existing.get(
                "EmployeeName",
                ""
            )

            name_parts = current_name.split(
                " ",
                1
            )

            current_first_name = (
                name_parts[0]
                if name_parts
                else ""
            )

            current_last_name = (
                name_parts[1]
                if len(name_parts) > 1
                else ""
            )

            first_name = incoming.get(
                "firstName",
                current_first_name
            )

            last_name = incoming.get(
                "lastName",
                current_last_name
            )

            update_fields["EmployeeName"] = (
                f"{first_name} {last_name}"
            ).strip()

        # ---------------------------------------------------------
        # Employee ID must not be changed
        # ---------------------------------------------------------

        update_fields.pop(
            "EmpID",
            None
        )

        # ---------------------------------------------------------
        # Nothing to update
        # ---------------------------------------------------------

        if not update_fields:
            return await EmployeeService.get_by_id(
                emp_id
            )

        # ---------------------------------------------------------
        # Perform MongoDB update
        # ---------------------------------------------------------

        result = await db.employees.find_one_and_update(
            {
                "EmpID": emp_id
            },
            {
                "$set": update_fields
            },
            return_document=True,
            projection={
                "_id": 0
            }
        )

        if result:
            return normalize_employee(
                result
            )

        return None

    # ----------------------------------------------------------------------
    # DELETE EMPLOYEE
    # ----------------------------------------------------------------------

    @staticmethod
    async def delete(
        emp_id: str
    ) -> bool:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        result = await db.employees.delete_one(
            {
                "EmpID": emp_id
            }
        )

        return result.deleted_count > 0


def _holiday_date_set() -> set[str]:
    holiday_file = Path(__file__).resolve().parents[1] / "data" / "holidays.json"
    try:
        if not holiday_file.exists():
            return set()
        payload = __import__("json").loads(holiday_file.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            return set()
        dates: set[str] = set()
        for item in payload:
            if not isinstance(item, dict):
                continue
            value = item.get("date") or item.get("Date") or item.get("holidayDate") or item.get("day")
            if value:
                text = str(value).strip()[:10]
                if text:
                    dates.add(text)
        return dates
    except Exception:
        return set()


class AttendanceBusinessDayService:
    @staticmethod
    def _normalize_iso_date(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            try:
                datetime.strptime(text[:10], "%Y-%m-%d")
                return text[:10]
            except ValueError:
                pass
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt.date().isoformat()
        except ValueError:
            return None

    @staticmethod
    def is_holiday(date_value: Optional[str]) -> bool:
        normalized = AttendanceBusinessDayService._normalize_iso_date(date_value)
        if not normalized:
            return False
        return normalized in _holiday_date_set()

    @staticmethod
    def is_weekly_off(date_value: Optional[str]) -> bool:
        normalized = AttendanceBusinessDayService._normalize_iso_date(date_value)
        if not normalized:
            return False
        try:
            return datetime.strptime(normalized, "%Y-%m-%d").weekday() == 6
        except ValueError:
            return False

    @staticmethod
    def is_working_day(date_value: Optional[str]) -> bool:
        normalized = AttendanceBusinessDayService._normalize_iso_date(date_value)
        if not normalized:
            return False
        return not AttendanceBusinessDayService.is_holiday(normalized) and not AttendanceBusinessDayService.is_weekly_off(normalized)

    @staticmethod
    def get_business_day_range(start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        start = AttendanceBusinessDayService._normalize_iso_date(start_date)
        end = AttendanceBusinessDayService._normalize_iso_date(end_date)
        if not start and not end:
            return {
                "startDate": None,
                "endDate": None,
                "workingDays": 0,
                "holidayCount": 0,
                "weeklyOffCount": 0,
                "totalDays": 0,
            }
        if not start:
            start = end
        if not end:
            end = start
        if start and end and start > end:
            start, end = end, start
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            total_days = 0
            working_days = 0
            holiday_count = 0
            weekly_off_count = 0
            current = start_dt
            while current <= end_dt:
                iso = current.strftime("%Y-%m-%d")
                total_days += 1
                if AttendanceBusinessDayService.is_holiday(iso):
                    holiday_count += 1
                if AttendanceBusinessDayService.is_weekly_off(iso):
                    weekly_off_count += 1
                if AttendanceBusinessDayService.is_working_day(iso):
                    working_days += 1
                current = current + __import__("datetime").timedelta(days=1)
            return {
                "startDate": start,
                "endDate": end,
                "workingDays": working_days,
                "holidayCount": holiday_count,
                "weeklyOffCount": weekly_off_count,
                "totalDays": total_days,
            }
        except ValueError:
            return {
                "startDate": start,
                "endDate": end,
                "workingDays": 0,
                "holidayCount": 0,
                "weeklyOffCount": 0,
                "totalDays": 0,
            }


# ==========================================================================
# 2. Attendance Service
# ==========================================================================

class AttendanceService:
    @staticmethod
    async def count_total_and_present() -> (int, int):
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        total = await db.attendance.count_documents({})
        present = await db.attendance.count_documents({"AttendanceStatus": {"$regex": r"^present$", "$options": "i"}})
        return total, present


    @staticmethod
    async def get_all(
        department: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50,
        employee_emp_id: Optional[str] = None,
        employee_emp_ids: Optional[List[str]] = None,
        employee_id: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_summary: bool = False,
    ) -> Union[
        Tuple[List[Dict[str, Any]], int],
        Tuple[List[Dict[str, Any]], int, Dict[str, Any]],
    ]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        employee_query: Dict[str, Any] = {}

        if employee_emp_ids:
            normalized_emp_ids = [str(item).strip() for item in employee_emp_ids if str(item).strip()]
            if normalized_emp_ids:
                employee_query["EmpID"] = {"$in": normalized_emp_ids}
        elif employee_emp_id:
            employee_query["EmpID"] = employee_emp_id

        if employee_id:
            normalized_employee_id = str(employee_id).strip()
            if normalized_employee_id:
                if employee_query.get("EmpID") is None:
                    employee_query["EmpID"] = normalized_employee_id
                elif isinstance(employee_query.get("EmpID"), dict):
                    employee_query["EmpID"]["$in"] = [normalized_employee_id] if normalized_employee_id not in employee_query["EmpID"].get("$in", []) else employee_query["EmpID"]["$in"]
                else:
                    employee_query["EmpID"] = normalized_employee_id

        if department and department.lower() != "all":
            employee_query["Department"] = {
                "$regex": f"^{department}$",
                "$options": "i"
            }

        total_employees = await db.employees.count_documents(employee_query)

        # Attendance history must be driven by actual MongoDB attendance documents.
        # Do not create synthetic absent rows: the attendance page is a record of
        # days an employee actually attended.
        employee_cursor = db.employees.find(employee_query, {"_id": 0})
        employee_docs = await employee_cursor.to_list(length=None)

        if not employee_docs:
            empty_summary = AttendanceService._build_summary([], total_employees, start_date, end_date, date)
            if include_summary:
                return [], total_employees, empty_summary
            return [], total_employees

        employee_lookup: Dict[str, Dict[str, Any]] = {}
        emp_ids: List[str] = []
        for emp in employee_docs:
            emp_id = emp.get("EmpID")
            if emp_id:
                employee_lookup[emp_id] = normalize_employee(emp)
                emp_ids.append(emp_id)

        attendance_query: Dict[str, Any] = {
            "EmpID": {"$in": emp_ids},
            "$or": [
                {"CheckIn": {"$exists": True, "$ne": None}},
                {"CheckInTime": {"$exists": True, "$ne": None}},
                {"checkIn": {"$exists": True, "$ne": None}},
            ],
        }
        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = AttendanceBusinessDayService._normalize_iso_date(start_date) or str(start_date)
            if end_date:
                date_filter["$lte"] = AttendanceBusinessDayService._normalize_iso_date(end_date) or str(end_date)
            if date_filter:
                attendance_query["Date"] = date_filter
        elif date:
            normalized_date = AttendanceBusinessDayService._normalize_iso_date(date) or str(date)
            attendance_query["Date"] = normalized_date

        if status and status.lower() != "all":
            if status.lower() != "absent":
                attendance_query["AttendanceStatus"] = {
                    "$regex": f"^{status}$",
                    "$options": "i"
                }

        cursor = db.attendance.find(attendance_query, {"_id": 0})
        attendance_documents = await cursor.to_list(length=None)

        # Keep every attendance day and sort newest-first. Mongo documents can use
        # either Date or date depending on when they were created.
        def attendance_sort_key(document: Dict[str, Any]) -> str:
            return str(document.get("Date") or document.get("date") or "")[:10]

        attendance_documents.sort(key=attendance_sort_key, reverse=True)
        merged_items = [
            normalize_attendance(document, employee_lookup.get(document.get("EmpID")))
            for document in attendance_documents
        ]

        if status and status.lower() != "all":
            merged_items = [
                item for item in merged_items
                if str(item.get("status") or item.get("AttendanceStatus") or "").strip().lower() == status.lower()
            ]

        total_records = len(merged_items)
        summary_items = merged_items
        skip = (page - 1) * size
        merged_items = merged_items[skip:skip + size]

        summary = AttendanceService._build_summary(summary_items, total_employees, start_date, end_date, date)
        if include_summary:
            return merged_items, total_records, summary
        return merged_items, total_records

    @staticmethod
    def _build_summary(
        merged_items: List[Dict[str, Any]],
        total_employees: int,
        start_date: Optional[str],
        end_date: Optional[str],
        date: Optional[str],
    ) -> Dict[str, Any]:
        effective_start = AttendanceBusinessDayService._normalize_iso_date(start_date) or AttendanceBusinessDayService._normalize_iso_date(date)
        effective_end = AttendanceBusinessDayService._normalize_iso_date(end_date) or AttendanceBusinessDayService._normalize_iso_date(date)
        if not effective_start and not effective_end:
            effective_start = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            effective_end = effective_start
        if effective_start and effective_end and effective_start > effective_end:
            effective_start, effective_end = effective_end, effective_start

        business = AttendanceBusinessDayService.get_business_day_range(effective_start, effective_end)
        working_days = int(business.get("workingDays") or 0)
        holiday_count = int(business.get("holidayCount") or 0)
        weekly_off_count = int(business.get("weeklyOffCount") or 0)

        present_count = 0
        late_count = 0
        currently_working = 0
        checked_out = 0

        # Per-day, per-department and today rollups are built from the FULL filtered result set,
        # not the requested page. The page is 50 rows by default, which is less than a single day
        # for a mid-sized team, so anything derived from the page alone under-reports badly.
        # Ranked so a duplicate same-day record resolves to its most actionable status.
        status_rank = {"present": 1, "working": 2, "currently working": 2, "late": 3}
        daily: Dict[str, Dict[str, int]] = {}
        department_counts: Dict[str, int] = {}
        # datetime.now() (server local), not UTC: that is what check_in stamps into Date, so the
        # comparison has to use the same clock or today's records never match.
        today_key = datetime.now().strftime("%Y-%m-%d")
        today_by_employee: Dict[str, str] = {}

        for item in merged_items:
            item_status = str(item.get("status") or item.get("AttendanceStatus") or "").strip().lower()
            check_in = item.get("checkIn") or item.get("CheckIn")
            check_out = item.get("checkOut") or item.get("CheckOut")
            if item_status == "late":
                late_count += 1
                present_count += 1
            elif item_status == "present":
                present_count += 1
            elif item_status in {"working", "currently working"}:
                currently_working += 1
            elif check_in and not check_out:
                currently_working += 1
            if check_out:
                checked_out += 1

            # Mirror the status aliases the attendance table resolves on the client, including the
            # LateArrival flag, so the rollups can never disagree with the rows they summarise.
            if item.get("LateArrival") is True or item.get("lateArrival") is True or item_status == "late":
                effective = "late"
            elif item_status in {"present", "checked out", "day completed", "complete"}:
                effective = "present"
            elif item_status in {"working", "currently working", "in progress"}:
                effective = "working"
            elif item_status in {"absent", "not checked in", "no show", "no-show"}:
                effective = ""
            elif check_in:
                effective = "present" if check_out else "working"
            else:
                effective = ""
            if not effective:
                continue

            day = str(item.get("date") or item.get("Date") or "")[:10]
            if day:
                bucket = daily.setdefault(day, {"present": 0, "late": 0, "working": 0, "attended": 0})
                if effective == "late":
                    bucket["late"] += 1
                    bucket["present"] += 1
                elif effective == "present":
                    bucket["present"] += 1
                else:
                    bucket["working"] += 1
                bucket["attended"] += 1

            department = str(item.get("department") or item.get("Department") or "").strip()
            if department and department.lower() != "unassigned":
                department_counts[department] = department_counts.get(department, 0) + 1

            if day == today_key:
                emp_key = str(item.get("empId") or item.get("EmpID") or "").strip()
                if emp_key:
                    previous = today_by_employee.get(emp_key)
                    if previous is None or status_rank[effective] > status_rank[previous]:
                        today_by_employee[emp_key] = effective

        daily_trend = [
            {
                "date": day,
                "present": values["present"],
                "late": values["late"],
                "working": values["working"],
                "attended": values["attended"],
            }
            for day, values in sorted(daily.items())
        ]

        department_breakdown = [
            {"department": name, "count": count}
            for name, count in sorted(department_counts.items(), key=lambda pair: (-pair[1], pair[0]))
        ]

        today_statuses = list(today_by_employee.values())
        today_attended = len(today_statuses)
        today_present = sum(1 for value in today_statuses if value in {"present", "late"})
        today_late = sum(1 for value in today_statuses if value == "late")
        today_working = sum(1 for value in today_statuses if value in {"working", "currently working"})
        today_headcount = max(total_employees, 0)

        total_working_opportunities = working_days * max(total_employees, 0)
        if total_working_opportunities <= 0 and (date or start_date or end_date):
            total_working_opportunities = max(total_employees, 0)

        absent_count = max(0, total_working_opportunities - present_count)
        attendance_rate = (present_count / total_working_opportunities * 100.0) if total_working_opportunities else 0.0

        return {
            "totalActiveEmployees": max(total_employees, 0),
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "currentlyWorking": currently_working,
            "checkedOut": checked_out,
            "totalWorkingDays": working_days,
            "holidayCount": holiday_count,
            "weeklyOffCount": weekly_off_count,
            "attendanceRate": round(attendance_rate, 2),
            # Last 30 attendance days across the whole filtered set, oldest first.
            "dailyTrend": daily_trend[-30:],
            "departmentBreakdown": department_breakdown,
            # Live snapshot for the current date, deduplicated per employee: one employee checked
            # in means attended == 1, which is what the dashboard cards read.
            "today": {
                "date": today_key,
                "attended": today_attended,
                "present": today_present,
                "late": today_late,
                "currentlyWorking": today_working,
                "absent": max(0, today_headcount - today_attended),
                "totalActiveEmployees": today_headcount,
                "attendanceRate": round(today_attended / today_headcount * 100.0, 2) if today_headcount else 0.0,
            },
        }

    # ----------------------------------------------------------------------
    # GET ATTENDANCE ANOMALIES
    # ----------------------------------------------------------------------

    @staticmethod
    async def get_anomalies() -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Dataset uses LateArrival = True for attendance anomalies
        # ---------------------------------------------------------

        cursor = db.attendance.find(
            {
                "LateArrival": True
            },
            {
                "_id": 0
            }
        )

        items = await cursor.to_list(
            length=100
        )

        employee_ids = {
            item.get("EmpID")
            for item in items
            if item.get("EmpID")
        }

        employee_lookup: Dict[str, Dict[str, Any]] = {}
        if employee_ids:
            employee_cursor = db.employees.find(
                {"EmpID": {"$in": list(employee_ids)}},
                {"_id": 0}
            )
            employee_documents = await employee_cursor.to_list(length=None)
            for employee_document in employee_documents:
                employee_id = employee_document.get("EmpID")
                if employee_id:
                    employee_lookup[employee_id] = normalize_employee(employee_document)

        normalized_items = []

        for item in items:
            emp_id = item.get("EmpID")
            normalized_items.append(
                normalize_attendance(
                    item,
                    employee_lookup.get(emp_id)
                )
            )

        return normalized_items

    # ----------------------------------------------------------------------
    # CHECK IN
    # ----------------------------------------------------------------------

    @staticmethod
    def _is_late_checkin(time_value: Optional[str]) -> bool:
        if not time_value:
            return False

        raw_value = str(time_value).strip()
        if raw_value in {"", "N/A", "--:--", "None", "null"}:
            return False

        try:
            if "T" in raw_value or raw_value.endswith("Z"):
                parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
                actual_time = parsed.time()
            else:
                if ":" in raw_value:
                    parts = raw_value.split(":")
                    if len(parts) == 2:
                        actual_time = datetime.strptime(raw_value, "%H:%M").time()
                    else:
                        actual_time = datetime.strptime(raw_value, "%H:%M:%S").time()
                else:
                    return False

            threshold = datetime.strptime("09:15", "%H:%M").time()
            return actual_time > threshold
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _calculate_gps_distance_meters(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
        radius_km = 6371.0
        lat_a = math.radians(latitude_a)
        lon_a = math.radians(longitude_a)
        lat_b = math.radians(latitude_b)
        lon_b = math.radians(longitude_b)

        delta_lat = lat_b - lat_a
        delta_lon = lon_b - lon_a
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c * 1000.0

    @staticmethod
    def _resolve_office_geofence() -> Tuple[float, float, float]:
        office_latitude = float(getattr(settings, "OFFICE_LATITUDE", 0.0) or 0.0)
        office_longitude = float(getattr(settings, "OFFICE_LONGITUDE", 0.0) or 0.0)
        radius_meters = float(getattr(settings, "OFFICE_GEOFENCE_RADIUS_METERS", 200.0) or 200.0)
        return office_latitude, office_longitude, radius_meters

    @staticmethod
    def _normalize_verification_method(value: Optional[str]) -> str:
        if value is None:
            return ""
        method = str(value).strip()
        if not method:
            return ""
        normalized = re.sub(r"[^A-Z0-9]+", "_", method.upper()).strip("_")
        aliases = {
            "DIRECT_CHECK_IN_CHECK_OUT": "DIRECT",
            "DIRECT_CHECK_IN": "DIRECT",
            "DIRECT_CHECK_OUT": "DIRECT",
            "DIRECT_ATTENDANCE": "DIRECT",
            "DIRECT_CHECKIN": "DIRECT",
            "DIRECT_CHECKOUT": "DIRECT",
            "QR_KIOSK": "QR",
            "LOCATION_VERIFICATION": "GPS",
            "FACIAL_RECOGNITION": "FACIAL",
            "BIOMETRIC_VERIFICATION": "BIOMETRIC",
            "REMOTE_CHECK_IN": "REMOTE",
            "STANDARD_CHECK_IN": "STANDARD",
            "MOBILE_FIELD_GPS": "MOBILE",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _evaluate_attendance_policy(employee: Dict[str, Any], date_str: str) -> Dict[str, Any]:
        """Determine today's effective attendance policy for the given employee.

        Returns a policy dict with keys:
          - work_mode
          - geofence_required (bool)
          - gps_audit_required (bool)
          - allowed_methods (list)
          - primary_method
          - requires_manager_approval (bool)
          - policy_message
        """
        # Resolve work mode from employee record; default to OFFICE when missing or invalid
        raw_mode = (employee or {}).get("work_mode") or employee.get("WorkMode") if employee else None
        if raw_mode is None:
            work_mode = "OFFICE"
        else:
            work_mode = str(raw_mode).strip().upper()
            if not work_mode:
                work_mode = "OFFICE"

        # Default policy values
        policy = {
            "work_mode": work_mode,
            "geofence_required": False,
            "gps_audit_required": False,
            "allowed_methods": ["STANDARD", "DIRECT"],
            "primary_method": "STANDARD",
            "requires_manager_approval": False,
            "policy_message": "Default attendance policy applied.",
        }

        if work_mode == "OFFICE":
            policy.update({
                "geofence_required": True,
                "gps_audit_required": True,
                "allowed_methods": ["GPS", "FACIAL", "BIOMETRIC", "QR", "DIRECT"],
                "primary_method": "GPS",
                "requires_manager_approval": False,
                "policy_message": "Office attendance requires geofence verification (GPS) unless the employee explicitly selects the direct attendance option.",
            })
        elif work_mode in {"REMOTE", "WFH"}:
            policy.update({
                "geofence_required": False,
                "gps_audit_required": True,
                "allowed_methods": ["REMOTE", "FACIAL", "STANDARD", "DIRECT"],
                "primary_method": "REMOTE",
                "requires_manager_approval": False,
                "policy_message": "Remote/Work-from-home attendance allowed. GPS may be captured for audit but will not be validated against the office geofence unless GPS is explicitly chosen.",
            })
        elif work_mode == "FIELD":
            policy.update({
                "geofence_required": False,
                "gps_audit_required": True,
                "allowed_methods": ["MOBILE", "GPS", "STANDARD", "DIRECT"],
                "primary_method": "MOBILE",
                "requires_manager_approval": False,
                "policy_message": "Field/mobile attendance allowed. Office geofence is not required for field employees unless the employee chooses GPS verification.",
            })
        elif work_mode == "HYBRID":
            policy.update({
                "geofence_required": False,
                "gps_audit_required": True,
                "allowed_methods": ["HYBRID", "GPS", "REMOTE", "FACIAL", "DIRECT"],
                "primary_method": "HYBRID",
                "requires_manager_approval": False,
                "policy_message": "Hybrid work mode: office or remote attendance allowed depending on schedule. Direct attendance remains available when the employee intentionally chooses it.",
            })
        elif work_mode == "FLEXIBLE":
            policy.update({
                "geofence_required": False,
                "gps_audit_required": False,
                "allowed_methods": ["STANDARD", "REMOTE", "GPS", "DIRECT"],
                "primary_method": "STANDARD",
                "requires_manager_approval": False,
                "policy_message": "Flexible work mode: standard or remote attendance allowed, with direct attendance available for explicit workday start/end actions.",
            })
        else:
            # Unknown modes fall back to OFFICE behavior conservatively
            policy.update({
                "geofence_required": True,
                "gps_audit_required": True,
                "allowed_methods": ["GPS", "FACIAL", "BIOMETRIC", "DIRECT"],
                "primary_method": "GPS",
                "requires_manager_approval": False,
                "policy_message": "Unrecognized work mode. Falling back to office attendance policy while still allowing direct attendance when explicitly selected.",
            })

        return policy

    @staticmethod
    def _verify_gps_payload(latitude: Optional[float], longitude: Optional[float], *, require_location: bool) -> Dict[str, Any]:
        if latitude is None or longitude is None:
            if require_location:
                raise ValueError("Location permission is required to check in.")
            return {
                "gpsVerified": None,
                "distanceFromOffice": None,
                "geofenceStatus": None,
                "latitude": None,
                "longitude": None,
            }

        try:
            lat_value = float(latitude)
            lon_value = float(longitude)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid latitude or longitude provided.") from exc

        if not (-90 <= lat_value <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if not (-180 <= lon_value <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees.")

        office_latitude, office_longitude, radius_meters = AttendanceService._resolve_office_geofence()
        distance = AttendanceService._calculate_gps_distance_meters(
            lat_value,
            lon_value,
            office_latitude,
            office_longitude,
        )

        gps_verified = distance <= max(radius_meters, 0.0)
        status = "INSIDE" if gps_verified else "OUTSIDE"
        return {
            "gpsVerified": gps_verified,
            "distanceFromOffice": round(distance, 2),
            "geofenceStatus": status,
            "latitude": lat_value,
            "longitude": lon_value,
        }

    @staticmethod
    async def check_in(
        payload: AttendanceCheckIn
    ) -> Dict[str, Any]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        if not payload.empId or not str(payload.empId).strip():
            raise ValueError("Invalid employee ID.")

        employee = await EmployeeService.get_by_id(
            payload.empId
        )

        if not employee:
            raise ValueError(
                f"Employee '{payload.empId}' was not found."
            )

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        raw_check_in = payload.checkInTime or now.strftime("%H:%M")
        raw_check_in = str(raw_check_in).strip()

        try:
            if "T" in raw_check_in or raw_check_in.endswith("Z"):
                check_in_dt = datetime.fromisoformat(raw_check_in.replace("Z", "+00:00"))
                time_str = check_in_dt.strftime("%H:%M")
            elif ":" in raw_check_in:
                if len(raw_check_in.split(":")) == 2:
                    time_str = datetime.strptime(raw_check_in, "%H:%M").strftime("%H:%M")
                else:
                    time_str = datetime.strptime(raw_check_in, "%H:%M:%S").strftime("%H:%M")
            else:
                raise ValueError("invalid check-in time format")
        except ValueError as exc:
            raise ValueError("Invalid check-in time supplied.") from exc

        # Evaluate today's attendance policy and decide how to treat GPS/geofence
        policy = AttendanceService._evaluate_attendance_policy(employee, today_str)
        allowed_methods = [
            AttendanceService._normalize_verification_method(item)
            for item in (policy.get("allowed_methods") or [])
            if str(item).strip()
        ]
        selected_method = AttendanceService._normalize_verification_method(
            payload.verificationMethod or policy.get("primary_method") or "STANDARD"
        )
        if selected_method and allowed_methods and not any(str(item).upper() == str(selected_method).upper() for item in allowed_methods):
            raise ValueError(f"Verification method '{selected_method}' is not allowed for the current work policy.")

        direct_bypass = selected_method in {"DIRECT", "DIRECT_ATTENDANCE"}
        require_location = bool(policy.get("geofence_required") and not direct_bypass)

        # If geofence is required by policy, GPS location is mandatory and must be inside geofence
        if require_location:
            gps_info = AttendanceService._verify_gps_payload(
                payload.latitude,
                payload.longitude,
                require_location=True,
            )
            if not gps_info["gpsVerified"]:
                raise ValueError("You are outside the permitted attendance area. " + policy.get("policy_message", ""))
        else:
            # Policy does not require being inside office geofence. Capture GPS if provided for audit (not mandatory).
            gps_info = AttendanceService._verify_gps_payload(
                payload.latitude,
                payload.longitude,
                require_location=not direct_bypass,
            )

        if direct_bypass:
            verification_status = "Directly Approved"
            gps_info.setdefault("geofenceStatus", "DIRECT")
            gps_info.setdefault("gpsVerified", None)
        else:
            verification_status = "Verified" if (gps_info.get("gpsVerified") is not False or selected_method in {"STANDARD", "REMOTE", "FACIAL", "BIOMETRIC", "QR", "MOBILE"}) else "Review Required"

        existing = await db.attendance.find_one(
            {
                "EmpID": payload.empId,
                "Date": today_str
            }
        )

        if existing:
            current_check_in = existing.get("CheckIn")
            if current_check_in not in (None, "", "N/A", "--:--"):
                raise ValueError(
                    f"Employee '{payload.empId}' has already checked in today."
                )

            late_arrival = AttendanceService._is_late_checkin(time_str)
            update_payload = {
                "CheckIn": time_str,
                "AttendanceStatus": "Late" if late_arrival else "Present",
                "LateArrival": late_arrival,
                "CheckOut": None,
                "WorkingHours": 0.0,
                "GPSVerified": gps_info.get("gpsVerified"),
                "Latitude": gps_info.get("latitude"),
                "Longitude": gps_info.get("longitude"),
                "DistanceFromOffice": gps_info.get("distanceFromOffice"),
                "GeofenceStatus": gps_info.get("geofenceStatus"),
                "WorkMode": policy.get("work_mode"),
                "WorkContext": {"workMode": policy.get("work_mode"), "policyMessage": policy.get("policy_message"), "assignedSite": employee.get("Location") or employee.get("AssignedSite") or None},
                "AllowedVerificationMethods": allowed_methods,
                "VerificationMethod": selected_method,
                "VerificationStatus": verification_status,
                "Verification": {
                    "method": selected_method,
                    "status": "APPROVED" if direct_bypass else verification_status,
                    "mode": "DIRECT_ATTENDANCE" if direct_bypass else selected_method,
                    "requiresManagerApproval": bool(policy.get("requires_manager_approval")),
                },
                "LocationAudit": {"gpsAuditRequired": bool(policy.get("gps_audit_required")), "distanceFromOffice": gps_info.get("distanceFromOffice"), "geofenceStatus": gps_info.get("geofenceStatus")},
                "AttendanceException": None,
                "ReviewStatus": "Approved" if verification_status in {"Verified", "Directly Approved"} else "Pending",
            }
            await db.attendance.update_one(
                {"_id": existing["_id"]},
                {"$set": update_payload}
            )
            merged_record = {**existing, **update_payload}
            return normalize_attendance(merged_record, employee)

        late_arrival = AttendanceService._is_late_checkin(time_str)
        record = {
            "EmpID": payload.empId,
            "Date": today_str,
            "CheckIn": time_str,
            "CheckOut": None,
            "WorkingHours": 0.0,
            "AttendanceStatus": "Late" if late_arrival else "Present",
            "LateArrival": late_arrival,
            "GPSVerified": gps_info.get("gpsVerified"),
            "Latitude": gps_info.get("latitude"),
            "Longitude": gps_info.get("longitude"),
            "DistanceFromOffice": gps_info.get("distanceFromOffice"),
            "GeofenceStatus": gps_info.get("geofenceStatus"),
            "WorkMode": policy.get("work_mode"),
            "WorkContext": {"workMode": policy.get("work_mode"), "policyMessage": policy.get("policy_message"), "assignedSite": employee.get("Location") or employee.get("AssignedSite") or None},
            "AllowedVerificationMethods": allowed_methods,
            "VerificationMethod": selected_method,
            "VerificationStatus": verification_status,
            "Verification": {
                "method": selected_method,
                "status": "APPROVED" if direct_bypass else verification_status,
                "mode": "DIRECT_ATTENDANCE" if direct_bypass else selected_method,
                "requiresManagerApproval": bool(policy.get("requires_manager_approval")),
            },
            "LocationAudit": {"gpsAuditRequired": bool(policy.get("gps_audit_required")), "distanceFromOffice": gps_info.get("distanceFromOffice"), "geofenceStatus": gps_info.get("geofenceStatus")},
            "AttendanceException": None,
            "ReviewStatus": "Approved" if verification_status in {"Verified", "Directly Approved"} else "Pending",
        }

        await db.attendance.insert_one(record)
        return normalize_attendance(record, employee)

    # ----------------------------------------------------------------------
    # CHECK OUT
    # ----------------------------------------------------------------------

    @staticmethod
    async def get_today_context(emp_id: str) -> Dict[str, Any]:
        """Return today's attendance policy context and basic shift/site info for the employee.

        This is a lightweight API-friendly representation intended for frontend consumption.
        """
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        if not emp_id or not str(emp_id).strip():
            raise ValueError("Invalid employee ID for context request.")

        employee = await EmployeeService.get_by_id(emp_id)
        if not employee:
            raise ValueError(f"Employee '{emp_id}' was not found.")

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        policy = AttendanceService._evaluate_attendance_policy(employee, today_str)

        # Assigned site/location (best-effort)
        assigned_site = employee.get("Location") or employee.get("AssignedSite") or "Not assigned"

        # Try to resolve a shift for today
        shift_info = None
        try:
            shift_doc = await db.shifts.find_one({"EmpID": emp_id, "ShiftDate": today_str}, {"_id": 0})
            if shift_doc:
                shift_info = {
                    "shiftName": shift_doc.get("ShiftName"),
                    "start": shift_doc.get("ShiftStart"),
                    "end": shift_doc.get("ShiftEnd"),
                    "shiftId": shift_doc.get("ShiftID") or shift_doc.get("ShiftId"),
                }
        except Exception:
            shift_info = None

        context = {
            "empId": emp_id,
            "work_mode": policy.get("work_mode"),
            "assigned_site": assigned_site,
            "shift": shift_info,
            "geofence_required": policy.get("geofence_required"),
            "gps_audit_required": policy.get("gps_audit_required"),
            "allowed_methods": policy.get("allowed_methods"),
            "primary_method": policy.get("primary_method"),
            "requires_manager_approval": policy.get("requires_manager_approval"),
            "policy_message": policy.get("policy_message"),
            "policy_status": "OK",
        }

        return context


    @staticmethod
    async def check_out(
        payload: AttendanceCheckOut
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        if not payload.empId or not str(payload.empId).strip():
            raise ValueError("Invalid employee ID.")

        employee = await EmployeeService.get_by_id(
            payload.empId
        )

        if not employee:
            raise ValueError(
                f"Employee '{payload.empId}' was not found."
            )

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        raw_check_out = payload.checkOutTime or now.strftime("%H:%M")
        raw_check_out = str(raw_check_out).strip()

        try:
            if "T" in raw_check_out or raw_check_out.endswith("Z"):
                check_out_dt = datetime.fromisoformat(raw_check_out.replace("Z", "+00:00"))
                time_str = check_out_dt.strftime("%H:%M")
            elif ":" in raw_check_out:
                if len(raw_check_out.split(":")) == 2:
                    time_str = datetime.strptime(raw_check_out, "%H:%M").strftime("%H:%M")
                else:
                    time_str = datetime.strptime(raw_check_out, "%H:%M:%S").strftime("%H:%M")
            else:
                raise ValueError("invalid check-out time format")
        except ValueError as exc:
            raise ValueError("Invalid check-out time supplied.") from exc

        record = await db.attendance.find_one(
            {
                "EmpID": payload.empId,
                "Date": today_str
            }
        )

        if not record:
            raise ValueError(
                "Attendance record not found for today. Employee must check in before checking out."
            )

        if record.get("CheckIn") in (None, "", "N/A", "--:--"):
            raise ValueError(
                "Employee has not checked in today."
            )

        current_check_out = record.get("CheckOut")
        if current_check_out not in (None, "", "N/A", "--:--"):
            raise ValueError(
                "Employee has already checked out today."
            )

        in_time_value = record.get("CheckIn")
        in_dt = None
        out_dt = None

        try:
            in_dt = datetime.strptime(str(in_time_value), "%H:%M")
            out_dt = datetime.strptime(time_str, "%H:%M")
        except ValueError as exc:
            raise ValueError("Invalid check-in/check-out time found in attendance record.") from exc

        if out_dt <= in_dt:
            raise ValueError("Check-out time must be later than check-in time.")

        working_hours = round((out_dt - in_dt).total_seconds() / 3600.0, 2)
        late_arrival = AttendanceService._is_late_checkin(in_time_value)
        attendance_status = "Late" if late_arrival else "Present"

        selected_method = AttendanceService._normalize_verification_method(
            payload.verificationMethod or record.get("VerificationMethod") or record.get("Verification", {}).get("method") or "STANDARD"
        )
        direct_bypass = selected_method in {"DIRECT", "DIRECT_ATTENDANCE"}

        gps_update = {}
        if payload.latitude is not None or payload.longitude is not None:
            gps_info = AttendanceService._verify_gps_payload(
                payload.latitude,
                payload.longitude,
                require_location=False,
            )
            if gps_info["gpsVerified"] is False:
                gps_update["GPSVerified"] = False
                gps_update["GeofenceStatus"] = "OUTSIDE"
                gps_update["DistanceFromOffice"] = gps_info["distanceFromOffice"]
                gps_update["Latitude"] = gps_info["latitude"]
                gps_update["Longitude"] = gps_info["longitude"]
            elif gps_info["gpsVerified"] is True:
                gps_update["GPSVerified"] = True
                gps_update["GeofenceStatus"] = "INSIDE"
                gps_update["DistanceFromOffice"] = gps_info["distanceFromOffice"]
                gps_update["Latitude"] = gps_info["latitude"]
                gps_update["Longitude"] = gps_info["longitude"]

        if direct_bypass:
            gps_update.setdefault("GPSVerified", record.get("GPSVerified") or None)
            gps_update.setdefault("GeofenceStatus", record.get("GeofenceStatus") or "DIRECT")
            gps_update.setdefault("DistanceFromOffice", record.get("DistanceFromOffice"))
            gps_update.setdefault("Latitude", record.get("Latitude"))
            gps_update.setdefault("Longitude", record.get("Longitude"))

        update_payload = {
            "CheckOut": time_str,
            "WorkingHours": working_hours,
            "AttendanceStatus": attendance_status,
            "LateArrival": late_arrival,
            "VerificationMethod": selected_method,
            "VerificationStatus": "Directly Approved" if direct_bypass else (record.get("VerificationStatus") or "Verified"),
            "Verification": {
                "method": selected_method,
                "status": "APPROVED" if direct_bypass else (record.get("Verification", {}).get("status") or "APPROVED"),
                "mode": "DIRECT_ATTENDANCE" if direct_bypass else (record.get("Verification", {}).get("mode") or selected_method),
                "requiresManagerApproval": bool(record.get("Verification", {}).get("requiresManagerApproval", False)),
            },
            **gps_update,
        }

        updated_record = await db.attendance.find_one_and_update(
            {
                "_id": record["_id"]
            },
            {
                "$set": update_payload
            },
            return_document=True,
            projection={
                "_id": 0
            }
        )

        if updated_record:
            return normalize_attendance(updated_record, employee)

        return None

    @staticmethod
    async def create_attendance_exception(payload: Any) -> Dict[str, Any]:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        if not getattr(payload, "empId", None) or not str(payload.empId).strip():
            raise ValueError("Invalid employee ID for exception request.")

        emp_id = str(payload.empId).strip()
        employee = await EmployeeService.get_by_id(emp_id)
        if not employee:
            raise ValueError(f"Employee '{emp_id}' was not found.")

        created_at = datetime.now().isoformat(timespec="seconds")
        doc = {
            "EmpID": emp_id,
            "EmployeeName": payload.employeeName or " ".join(filter(None, [employee.get("firstName"), employee.get("lastName")])) or employee.get("EmployeeName") or emp_id,
            "Date": payload.date or datetime.now().strftime("%Y-%m-%d"),
            "Reason": payload.reason or "Other",
            "Description": payload.description or "",
            "WorkMode": payload.workMode or "OFFICE",
            "SelectedVerificationMethod": payload.selectedVerificationMethod or "STANDARD",
            "GPSData": payload.gpsData or {},
            "Status": "Pending",
            "ReviewStatus": "Pending",
            "CreatedAt": created_at,
        }
        result = await db.attendance_exceptions.insert_one(doc)
        inserted = {**doc, "_id": result.inserted_id, "id": str(result.inserted_id)}
        return {
            "id": str(result.inserted_id),
            "empId": emp_id,
            "employeeName": inserted.get("EmployeeName"),
            "date": inserted.get("Date"),
            "reason": inserted.get("Reason"),
            "description": inserted.get("Description"),
            "workMode": inserted.get("WorkMode"),
            "selectedVerificationMethod": inserted.get("SelectedVerificationMethod"),
            "gpsData": inserted.get("GPSData"),
            "status": inserted.get("Status"),
            "reviewStatus": inserted.get("ReviewStatus"),
            "createdAt": inserted.get("CreatedAt"),
        }


# ==========================================================================
# 3. Leave Service
# ==========================================================================

class LeaveService:

    VALID_STATUSES = {"Pending", "Approved", "Rejected"}

    @staticmethod
    def _normalize_status(raw_status: Optional[str]) -> str:
        if raw_status is None:
            return "Pending"
        value = str(raw_status).strip()
        if not value:
            return "Pending"
        normalized = value.title()
        if normalized not in LeaveService.VALID_STATUSES:
            raise ValueError("Leave status must be one of: Pending, Approved, Rejected.")
        return normalized

    @staticmethod
    async def _has_overlapping_leave(
        emp_id: str,
        start_date: str,
        end_date: str,
        exclude_leave_id: Optional[str] = None
    ) -> bool:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        try:
            start = datetime.strptime(str(start_date), "%Y-%m-%d")
            end = datetime.strptime(str(end_date), "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Invalid leave date provided.") from exc

        if end < start:
            raise ValueError("Leave end date cannot be earlier than the start date.")

        query: Dict[str, Any] = {"EmpID": emp_id}
        if exclude_leave_id:
            try:
                from bson import ObjectId
                query["_id"] = {"$ne": ObjectId(exclude_leave_id)}
            except Exception:
                query["id"] = {"$ne": exclude_leave_id}

        items = await db.leaves.find(query, {"_id": 0}).to_list(length=5000)
        for item in items:
            existing_status = str(item.get("Status") or "").strip()
            if existing_status.lower() == "rejected":
                continue
            existing_start = item.get("StartDate")
            existing_end = item.get("EndDate")
            if not existing_start or not existing_end:
                continue
            try:
                existing_start_dt = datetime.strptime(str(existing_start), "%Y-%m-%d")
                existing_end_dt = datetime.strptime(str(existing_end), "%Y-%m-%d")
            except ValueError:
                continue
            if start <= existing_end_dt and end >= existing_start_dt:
                return True
        return False

    @staticmethod
    async def count_pending() -> int:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        return await db.leaves.count_documents({"Status": {"$regex": r"^pending$", "$options": "i"}})


    @staticmethod
    async def get_all(
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50,
        emp_id: Optional[str] = None,
        emp_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Build query using ACTUAL MongoDB field names
        # ---------------------------------------------------------

        query: Dict[str, Any] = {}

        if emp_ids:
            query["EmpID"] = {"$in": [str(item).strip() for item in emp_ids if str(item).strip()]}
        elif emp_id and str(emp_id).strip():
            query["EmpID"] = str(emp_id).strip()

        if status and status.lower() != "all":
            query["Status"] = {
                "$regex": f"^{status}$",
                "$options": "i"
            }

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------
        skip = (page - 1) * size

        # Include MongoDB _id in results so normalize_leave can emit a canonical `id` field.
        # Sort newest-first: ObjectIds increase monotonically with insertion time, so newly
        # submitted requests land on page 1 instead of being buried at the end of natural order.
        cursor = db.leaves.find(query).sort("_id", -1).skip(skip).limit(size)

        items = await cursor.to_list(
            length=size
        )

        # ---------------------------------------------------------
        # Convert MongoDB documents to API format
        # ---------------------------------------------------------

        return [
            normalize_leave(item)
            for item in items
        ]

    @staticmethod
    async def submit(
        request: LeaveRequestBase,
        actor_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        if not request.empId or not str(request.empId).strip():
            raise ValueError("Invalid employee ID.")

        if request.status is not None and str(request.status).strip():
            normalized_status = LeaveService._normalize_status(request.status)
            if normalized_status != "Pending":
                raise ValueError("Leave status is HR-controlled. Employees can only submit Pending leave requests.")

        if not request.startDate or not str(request.startDate).strip():
            raise ValueError("Leave start date is required.")
        if not request.endDate or not str(request.endDate).strip():
            raise ValueError("Leave end date is required.")

        try:
            start = datetime.strptime(str(request.startDate), "%Y-%m-%d")
            end = datetime.strptime(str(request.endDate), "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Leave dates must use YYYY-MM-DD format.") from exc

        if end < start:
            raise ValueError("Leave end date cannot be earlier than the start date.")

        days = (end - start).days + 1
        if days <= 0:
            raise ValueError("Leave duration must be at least one day.")

        if await LeaveService._has_overlapping_leave(str(request.empId).strip(), str(request.startDate), str(request.endDate)):
            raise ValueError("This leave request overlaps with another leave period for the same employee.")

        data = {
            "EmpID": str(request.empId).strip(),
            "LeaveType": request.leaveType,
            "StartDate": request.startDate,
            "EndDate": request.endDate,
            "Status": "Pending",
            "LeaveBalance": request.leaveBalance,
            "days": days,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "Reason": request.reason,
            "EmployeeName": request.empName,
        }

        insert_result = await db.leaves.insert_one(data)
        created = dict(data)
        created["_id"] = insert_result.inserted_id
        created["id"] = str(insert_result.inserted_id)
        normalized = normalize_leave(created)
        await NotificationService.create_leave_request_notifications(normalized, actor_user=actor_user)
        return normalized

    @staticmethod
    async def update_status(
        leave_id: str,
        update: LeaveStatusUpdate,
        actor_user: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        normalized_status = LeaveService._normalize_status(update.status)
        query: Dict[str, Any] = {"_id": leave_id}
        try:
            from bson import ObjectId
            query = {"_id": ObjectId(leave_id)}
        except Exception:
            query = {"id": leave_id}

        update_payload = {
            "$set": {
                "Status": normalized_status
            }
        }
        comment = str(getattr(update, "approverComments", "") or "").strip()
        if comment:
            update_payload["$set"]["ManagerComments"] = comment

        actor_name = ""
        actor_user_id = ""
        actor_emp_id = ""
        actor_role = ""
        if actor_user:
            actor_name = str(actor_user.get("name") or actor_user.get("email") or actor_user.get("userId") or "System").strip()
            actor_user_id = str(actor_user.get("userId") or "").strip()
            actor_emp_id = str(actor_user.get("empId") or "").strip()
            actor_role = str(actor_user.get("role") or "MANAGER").strip().upper()

        if actor_name:
            update_payload["$set"]["decisionByName"] = actor_name
        if actor_user_id:
            update_payload["$set"]["decisionByUserId"] = actor_user_id
        if actor_emp_id:
            update_payload["$set"]["decisionByEmpId"] = actor_emp_id
        if actor_role:
            update_payload["$set"]["decisionRole"] = actor_role
        update_payload["$set"]["decisionAt"] = datetime.now(timezone.utc).isoformat()
        if comment:
            update_payload["$set"]["decisionComments"] = comment

        result = await db.leaves.find_one_and_update(
            query,
            update_payload,
            return_document=True
        )

        if result:
            normalized = normalize_leave(result)
            await NotificationService.create_leave_decision_notifications(normalized, actor_user=actor_user)
            return normalized

        return None


# ==========================================================================
# 4. Shift Service
# ==========================================================================

class ShiftService:

    VALID_STATUSES = {"Pending", "Approved", "Rejected", "Not Requested"}

    @staticmethod
    def _normalize_status(raw_status: Optional[str]) -> str:
        if raw_status is None:
            return "Pending"
        value = str(raw_status).strip()
        if not value:
            return "Pending"
        normalized = value.title()
        if normalized not in ShiftService.VALID_STATUSES:
            raise ValueError("Shift status must be one of: Pending, Approved, Rejected, Not Requested.")
        return normalized

    @staticmethod
    async def count_pending() -> int:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        return await db.shifts.count_documents({"ShiftSwapStatus": {"$regex": r"^pending$", "$options": "i"}})


    # ----------------------------------------------------------------------
    # GET ALL SHIFT REQUESTS
    # ----------------------------------------------------------------------

    @staticmethod
    async def get_all(
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50,
        emp_id: Optional[str] = None,
        emp_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Build query
        # ---------------------------------------------------------

        query: Dict[str, Any] = {}

        if emp_ids:
            query["EmpID"] = {"$in": [str(item).strip() for item in emp_ids if str(item).strip()]}
        elif emp_id and str(emp_id).strip():
            query["EmpID"] = str(emp_id).strip()

        if status and status.lower() != "all":

            normalized_status = status.strip().title()

            if normalized_status not in ShiftService.VALID_STATUSES:
                return []

            query["ShiftSwapStatus"] = normalized_status

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------
        skip = (page - 1) * size

        # Sort newest-first so freshly submitted swap requests land on page 1.
        # _id is valid as a sort key even though it is projected out of the result.
        cursor = db.shifts.find(
            query,
            {"_id": 0}
        ).sort("_id", -1).skip(skip).limit(size)

        items = await cursor.to_list(
            length=size
        )

        # ---------------------------------------------------------
        # Enrich employee information
        # ---------------------------------------------------------

        employee_ids = {
            item.get("EmpID")
            for item in items
            if item.get("EmpID")
        }

        employee_lookup: Dict[str, Dict[str, Any]] = {}
        if employee_ids:
            employee_cursor = db.employees.find(
                {"EmpID": {"$in": list(employee_ids)}},
                {"_id": 0}
            )
            employee_documents = await employee_cursor.to_list(length=None)
            for employee_document in employee_documents:
                employee_id = employee_document.get("EmpID")
                if employee_id:
                    employee_lookup[employee_id] = normalize_employee(employee_document)

        normalized_items = []

        for item in items:
            emp_id_val = item.get("EmpID")
            normalized_items.append(
                normalize_shift(
                    item,
                    employee_lookup.get(emp_id_val)
                )
            )

        return normalized_items

    # ----------------------------------------------------------------------
    # CREATE SHIFT REQUEST
    # ----------------------------------------------------------------------

    @staticmethod
    async def submit(
        request: ShiftRequestBase,
        actor_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        if not request.empId or not str(request.empId).strip():
            raise ValueError("Invalid employee ID.")

        # ---------------------------------------------------------
        # Verify employee exists
        # ---------------------------------------------------------

        employee = await EmployeeService.get_by_id(
            str(request.empId).strip()
        )

        if not employee:
            raise ValueError(
                f"Employee '{request.empId}' was not found."
            )

        if not request.requestedShift or not str(request.requestedShift).strip():
            raise ValueError("requestedShift is required.")

        if not request.requestedDate or not str(request.requestedDate).strip():
            raise ValueError("requestedDate is required.")

        requested_shift = str(request.requestedShift).strip()

        if "(" not in requested_shift or ")" not in requested_shift:
            raise ValueError(
                "requestedShift must use the format "
                "'ShiftName (HH:MM - HH:MM)'."
            )

        try:

            shift_name = requested_shift.split(
                "(",
                1
            )[0].strip()

            time_part = requested_shift.split(
                "(",
                1
            )[1].rsplit(
                ")",
                1
            )[0].strip()

            shift_start, shift_end = [
                value.strip()
                for value in time_part.split(
                    "-",
                    1
                )
            ]

            if not shift_name:
                raise ValueError

            if not shift_start or not shift_end:
                raise ValueError

        except Exception:

            raise ValueError(
                "Invalid requestedShift format. "
                "Use 'Night (22:00 - 07:00)'."
            )

        try:

            datetime.strptime(
                str(request.requestedDate),
                "%Y-%m-%d"
            )

        except ValueError as exc:

            raise ValueError(
                "requestedDate must use YYYY-MM-DD format."
            ) from exc

        counter = await db.counters.find_one_and_update(
            {
                "_id": "shift_id"
            },
            {
                "$inc": {
                    "seq": 1
                }
            },
            upsert=True,
            return_document=True
        )

        sequence = counter["seq"]
        shift_id = f"SH-{sequence:06d}"

        applied_on = datetime.now().strftime("%Y-%m-%d")

        record = {
            "EmpID": str(request.empId).strip(),
            "ShiftName": shift_name,
            "ShiftStart": shift_start,
            "ShiftEnd": shift_end,
            "OvertimeHours": 0.0,
            "ShiftSwapApproved": False,
            "ShiftDate": str(request.requestedDate),
            "ShiftID": shift_id,
            "ShiftSwapStatus": "Pending",
            "Reason": request.reason,
            "AppliedOn": applied_on,
            "empName": employee.get("EmployeeName") or employee.get("firstName"),
        }

        await db.shifts.insert_one(record)
        normalized = normalize_shift(record, employee)
        await NotificationService.create_shift_request_notifications(normalized, actor_user=actor_user)
        return normalized

    # ----------------------------------------------------------------------
    # UPDATE SHIFT STATUS
    # ----------------------------------------------------------------------

    @staticmethod
    async def update_status(
        shift_id: str,
        update: ShiftStatusUpdate,
        actor_user: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        current = await db.shifts.find_one(
            {"ShiftID": shift_id},
            projection={"_id": 0}
        )

        if not current:
            return None

        current_status = ShiftService._normalize_status(current.get("ShiftSwapStatus"))
        if current_status != "Pending":
            raise ValueError("Only pending shift requests can be approved or rejected.")

        emp_id = current.get("EmpID")
        if not emp_id:
            raise ValueError("Shift request is missing an employee ID.")

        employee = await EmployeeService.get_by_id(str(emp_id).strip())
        if not employee:
            raise ValueError(f"Employee '{emp_id}' was not found.")

        requested_shift_name = str(current.get("ShiftName") or "").strip()
        requested_shift_start = str(current.get("ShiftStart") or "").strip()
        requested_shift_end = str(current.get("ShiftEnd") or "").strip()
        if not requested_shift_name or not requested_shift_start or not requested_shift_end:
            raise ValueError("Requested shift data is incomplete and cannot be approved.")

        requested_date = str(current.get("ShiftDate") or "").strip()
        if requested_date:
            try:
                datetime.strptime(requested_date, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("Requested date is invalid; use YYYY-MM-DD.") from exc

        new_status = ShiftService._normalize_status(update.status)
        approved = (new_status == "Approved")

        update_payload = {
            "$set": {
                "ShiftSwapStatus": new_status,
                "ShiftSwapApproved": approved,
            }
        }

        comment = str(getattr(update, "approverComments", "") or "").strip()
        if comment:
            update_payload["$set"]["ManagerComments"] = comment

        actor_name = ""
        actor_user_id = ""
        actor_emp_id = ""
        actor_role = ""
        if actor_user:
            actor_name = str(actor_user.get("name") or actor_user.get("email") or actor_user.get("userId") or "System").strip()
            actor_user_id = str(actor_user.get("userId") or "").strip()
            actor_emp_id = str(actor_user.get("empId") or "").strip()
            actor_role = str(actor_user.get("role") or "MANAGER").strip().upper()

        if actor_name:
            update_payload["$set"]["decisionByName"] = actor_name
        if actor_user_id:
            update_payload["$set"]["decisionByUserId"] = actor_user_id
        if actor_emp_id:
            update_payload["$set"]["decisionByEmpId"] = actor_emp_id
        if actor_role:
            update_payload["$set"]["decisionRole"] = actor_role
        update_payload["$set"]["decisionAt"] = datetime.now(timezone.utc).isoformat()
        if comment:
            update_payload["$set"]["decisionComments"] = comment

        result = await db.shifts.find_one_and_update(
            {
                "ShiftID": shift_id
            },
            update_payload,
            return_document=True,
            projection={
                "_id": 0
            }
        )

        if not result:
            return None

        employee = await EmployeeService.get_by_id(str(emp_id).strip())
        normalized = normalize_shift(result, employee)
        normalized["status"] = new_status
        await NotificationService.create_shift_decision_notifications(normalized, actor_user=actor_user)
        return normalized


# ==========================================================================
# 5. Timesheet Service
# ==========================================================================

class TimesheetService:

    @staticmethod
    async def get_all(
        emp_id: Optional[str] = None,
        emp_ids: Optional[List[str]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Build query using ACTUAL MongoDB field names
        # ---------------------------------------------------------

        query: Dict[str, Any] = {}

        if emp_ids:
            query["EmpID"] = {"$in": [str(item).strip() for item in emp_ids if str(item).strip()]}
        elif emp_id:
            query["EmpID"] = emp_id

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------
        skip = (page - 1) * size

        cursor = db.timesheets.find(
            query,
            {"_id": 0}
        ).skip(skip).limit(size)

        items = await cursor.to_list(
            length=size
        )

        # ---------------------------------------------------------
        # Convert MongoDB documents to API format
        # ---------------------------------------------------------

        return [
            normalize_timesheet(item)
            for item in items
        ]

    @staticmethod
    async def submit(
        timesheet: TimesheetBase
    ) -> Dict[str, Any]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        if not timesheet.empId or not str(timesheet.empId).strip():
            raise ValueError("Invalid employee ID.")

        data = {
            "EmpID": timesheet.empId,
            "Date": timesheet.date,
            "Project": timesheet.projectName,
            "HoursWorked": timesheet.hoursLogged,
            "ClientBillingHours": timesheet.clientBillingHours,
            "Status": timesheet.status or "Pending",
        }

        await db.timesheets.insert_one(data)
        return normalize_timesheet(data)

    @staticmethod
    async def update_status(
        timesheet_id: str,
        new_status: str
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        query: Dict[str, Any] = {"_id": timesheet_id}
        try:
            from bson import ObjectId
            query = {"_id": ObjectId(timesheet_id)}
        except Exception:
            query = {"id": timesheet_id}

        result = await db.timesheets.find_one_and_update(
            query,
            {
                "$set": {
                    "Status": new_status
                }
            },
            return_document=True
        )

        if result:
            return normalize_timesheet(result)

        return None


# ==========================================================================
# 6. Payroll Service
# ==========================================================================

class PayrollService:

    @staticmethod
    async def get_all(
        month: Optional[str] = None,
        page: int = 1,
        size: int = 50,
        emp_id: Optional[str] = None,
        emp_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Build query using ACTUAL MongoDB field names
        # ---------------------------------------------------------

        query: Dict[str, Any] = {}

        if emp_ids:
            query["EmpID"] = {"$in": [str(item).strip() for item in emp_ids if str(item).strip()]}
        elif emp_id and str(emp_id).strip():
            query["EmpID"] = str(emp_id).strip()

        if month:
            query["PayrollMonth"] = {
                "$regex": f"^{month}$",
                "$options": "i"
            }

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------
        skip = (page - 1) * size

        cursor = db.payroll.find(
            query,
            {"_id": 0}
        ).skip(skip).limit(size)

        items = await cursor.to_list(
            length=size
        )

        # ---------------------------------------------------------
        # Convert MongoDB documents to API format
        # ---------------------------------------------------------

        return [
            normalize_payroll(item)
            for item in items
        ]

    @staticmethod
    async def sum_net_salary_for_month(month: Optional[str] = None) -> float:
        """Return the total NetSalary for the provided PayrollMonth. If month is None, sum across all documents."""
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        match_stage = { }
        if month:
            match_stage = {"$match": {"PayrollMonth": {"$regex": f"^{month}$", "$options": "i"}}}

        pipeline = []
        if match_stage:
            pipeline.append(match_stage)

        pipeline.append({
            "$group": {
                "_id": None,
                "total": {"$sum": {"$ifNull": ["$NetSalary", 0]}}
            }
        })

        cursor = db.payroll.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if result:
            return float(result[0].get("total", 0.0) or 0.0)
        return 0.0

    @staticmethod
    async def calculate(
        month: str = "2023-05"
    ) -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        query = {}
        if month:
            query["PayrollMonth"] = {"$regex": f"^{month}$", "$options": "i"}

        items = await db.payroll.find(query, {"_id": 0}).to_list(length=5000)
        return [normalize_payroll(item) for item in items]

    @staticmethod
    async def disburse(
        payroll_id: str
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        result = await db.payroll.find_one({"_id": payroll_id})
        if not result:
            result = await db.payroll.find_one({"id": payroll_id})

        if result:
            return normalize_payroll(result)

        return None


# ==========================================================================
# 7. Performance Service
# ==========================================================================

class PerformanceService:

    @staticmethod
    async def create(
        data: PerformanceBase
    ) -> Dict[str, Any]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Check if performance record already exists
        # ---------------------------------------------------------

        existing = await db.performance.find_one(
            {"EmpID": data.empId}
        )

        if existing:
            raise ValueError(
                f"Performance record for employee "
                f"'{data.empId}' already exists."
            )

        # ---------------------------------------------------------
        # Convert API fields to MongoDB fields
        #
        # MongoDB dataset uses:
        # EmpID
        # KPI
        # GoalCompletion
        # ProductivityScore
        # PerformanceRating
        # ReviewDate
        #
        # ---------------------------------------------------------

        doc = {
            "EmpID": data.empId,
            "KPI": data.performanceScore,
            "GoalCompletion": data.kpiCompletionRate,
            "ProductivityScore": data.productivityScore,
            "PerformanceRating": (
                5
                if data.performanceScore >= 90
                else 4
                if data.performanceScore >= 75
                else 3
                if data.performanceScore >= 60
                else 2
                if data.performanceScore >= 40
                else 1
            ),
            "ReviewDate": datetime.now().strftime(
                "%Y-%m-%d"
            )
        }

        await db.performance.insert_one(doc)

        return normalize_performance(doc)

    @staticmethod
    async def get_all() -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        cursor = db.performance.find(
            {},
            {"_id": 0}
        )

        items = await cursor.to_list(
            length=None
        )

        return [
            normalize_performance(item)
            for item in items
        ]
    
    @staticmethod
    async def get_average_productivity_score() -> Optional[float]:
        """
        Calculate the average productivity score across all employees
        with a valid ProductivityScore value.
        """

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        pipeline = [
            {
                "$match": {
                    "ProductivityScore": {
                        "$exists": True,
                        "$ne": None
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "averageProductivity": {
                        "$avg": "$ProductivityScore"
                    }
                }
            }
        ]

        results = await db.performance.aggregate(
            pipeline
        ).to_list(length=1)

        if not results:
            return None

        average_score = results[0].get(
            "averageProductivity"
        )

        if average_score is None:
            return None

        return round(float(average_score), 1)

    @staticmethod
    async def get_by_emp_id(
        emp_id: str
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # IMPORTANT:
        # MongoDB uses EmpID, not empId.

        result = await db.performance.find_one(
            {
                "EmpID": emp_id
            },
            {"_id": 0}
        )

        if result:
            return normalize_performance(result)

        return None

    @staticmethod
    async def update(
        emp_id: str,
        data: PerformanceUpdate
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Convert API field names to MongoDB field names
        # ---------------------------------------------------------

        update_fields: Dict[str, Any] = {}

        if data.performanceScore is not None:
            update_fields["KPI"] = data.performanceScore

        if data.kpiCompletionRate is not None:
            update_fields["GoalCompletion"] = (
                data.kpiCompletionRate
            )

        if data.productivityScore is not None:
            update_fields["ProductivityScore"] = (
                data.productivityScore
            )

        # ---------------------------------------------------------
        # PerformanceRating is not directly exposed in
        # PerformanceUpdate, so it is derived from
        # performanceScore if performanceScore is updated.
        # ---------------------------------------------------------

        if data.performanceScore is not None:

            score = data.performanceScore

            if score >= 90:
                rating = 5
            elif score >= 75:
                rating = 4
            elif score >= 60:
                rating = 3
            elif score >= 40:
                rating = 2
            else:
                rating = 1

            update_fields["PerformanceRating"] = rating

        if not update_fields:
            return await PerformanceService.get_by_emp_id(
                emp_id
            )

        # ---------------------------------------------------------
        # Update actual MongoDB fields
        # ---------------------------------------------------------

        result = await db.performance.find_one_and_update(
            {
                "EmpID": emp_id
            },
            {
                "$set": update_fields
            },
            return_document=True,
            projection={"_id": 0}
        )

        if result:
            return normalize_performance(result)

        return None

    @staticmethod
    async def delete(
        emp_id: str
    ) -> bool:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        result = await db.performance.delete_one(
            {
                "EmpID": emp_id
            }
        )

        return result.deleted_count > 0

# ==========================================================================
# 8. Notification Service
# ==========================================================================

class NotificationService:

    @staticmethod
    def _notification_match_query(notif_id: str) -> Dict[str, Any]:
        or_clauses = [
            {"id": notif_id},
            {"_id": notif_id}
        ]

        try:
            from bson import ObjectId
            oid = ObjectId(notif_id)
            or_clauses.insert(0, {"_id": oid})
        except Exception:
            pass

        return {"$or": or_clauses}

    @staticmethod
    def _normalize_status(raw_status: Optional[str]) -> str:
        if raw_status is None:
            return "Unread"
        status = str(raw_status).strip()
        if not status:
            return "Unread"
        normalized = status.lower()
        if normalized in {"read", "readable"}:
            return "Read"
        return "Unread"

    @staticmethod
    def _generate_notification_id(recipient_key: Optional[str], notification_type: Optional[str]) -> str:
        prefix = "NOTIF"
        suffix = str(uuid.uuid4().hex[:8]).upper()
        recipient_segment = str(recipient_key or "SYSTEM").strip().upper().replace(" ", "-")
        type_segment = str(notification_type or "SYSTEM").strip().upper().replace(" ", "-")
        return f"{prefix}-{recipient_segment}-{type_segment}-{suffix}"

    @staticmethod
    def _normalize_role_name(role_name: Optional[str]) -> str:
        return str(role_name or "").strip().upper()

    @staticmethod
    def _scope_query_for_user(emp_id: Optional[str], user_id: Optional[str], role: Optional[str]) -> Dict[str, Any]:
        user_emp_id = str(emp_id or "").strip()
        user_account_id = str(user_id or "").strip()
        normalized_role = NotificationService._normalize_role_name(role)
        clauses: List[Dict[str, Any]] = []

        if user_emp_id:
            clauses.append({"EmpID": user_emp_id})
        if user_account_id:
            clauses.append({"recipientUserId": user_account_id})
        # Allow any HR-prefixed role to match HR notifications (e.g. HR, HR_ADMIN, HR_MANAGER)
        if normalized_role.startswith("HR"):
            clauses.append({"recipientRole": {"$regex": r"^HR", "$options": "i"}})
        elif normalized_role == "MANAGER":
            clauses.append({"recipientRole": normalized_role})

        if not clauses:
            return {}
        return {"$or": clauses}

    @staticmethod
    def user_can_access_notification(
        notification: Optional[Dict[str, Any]],
        *,
        emp_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> bool:
        if not notification:
            return False

        current_emp_id = str(emp_id or "").strip()
        current_user_id = str(user_id or "").strip()
        current_role = NotificationService._normalize_role_name(role)
        recipient_role = NotificationService._normalize_role_name(notification.get("recipientRole"))

        # HR-prefixed roles (HR, HR_ADMIN, HR_MANAGER, etc.) can access HR notifications
        if (current_role.startswith("HR") and recipient_role.startswith("HR")) or (current_role == "MANAGER" and recipient_role == "MANAGER"):
            return True

        existing_emp_id = str(notification.get("EmpID") or notification.get("empId") or "").strip()
        existing_user_id = str(notification.get("recipientUserId") or "").strip()

        if current_user_id and existing_user_id and current_user_id == existing_user_id:
            return True
        if current_emp_id and existing_emp_id and current_emp_id == existing_emp_id:
            return True

        return False

    @staticmethod
    async def _resolve_user_accounts_by_role(role_name: str) -> List[Dict[str, Any]]:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        normalized = NotificationService._normalize_role_name(role_name)
        if normalized.startswith("HR"):
            # Match any HR-prefixed role in a case-insensitive way (HR, HR_ADMIN, HR_MANAGER...)
            query = {"role": {"$regex": r"^HR", "$options": "i"}}
        else:
            query = {"role": {"$in": [role_name, role_name.upper(), role_name.lower(), str(role_name).title()]}}
        return await db.user_accounts.find(
            query,
            {"_id": 0, "userId": 1, "empId": 1, "name": 1, "email": 1, "role": 1}
        ).to_list(length=None)

    @staticmethod
    async def _lookup_employee_name(emp_id: Optional[str]) -> str:
        if not emp_id:
            return "Employee"
        db = get_database()
        if db is None:
            return "Employee"
        employee = await db.employees.find_one({"EmpID": str(emp_id).strip()}, {"_id": 0, "EmployeeName": 1, "firstName": 1, "lastName": 1})
        if not employee:
            return "Employee"
        full_name = str(employee.get("EmployeeName") or "").strip()
        if full_name:
            return full_name
        first_name = str(employee.get("firstName") or "").strip()
        last_name = str(employee.get("lastName") or "").strip()
        return " ".join(part for part in [first_name, last_name] if part) or "Employee"

    @staticmethod
    async def _resolve_manager_recipients(emp_id: str) -> List[Dict[str, Any]]:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        recipient_map: Dict[str, Dict[str, Any]] = {}
        employee = await db.employees.find_one({"EmpID": str(emp_id).strip()}, {"_id": 0, "ManagerID": 1, "managerId": 1, "managerEmpId": 1})
        if employee:
            for candidate in (employee.get("ManagerID"), employee.get("managerId"), employee.get("managerEmpId")):
                manager_id = str(candidate or "").strip()
                if manager_id:
                    recipient_map[manager_id] = {"empId": manager_id, "role": "MANAGER"}

        for manager_id in sorted(recipient_map.keys()):
            manager = await db.employees.find_one({"EmpID": manager_id}, {"_id": 0, "EmployeeName": 1, "Email": 1})
            if manager:
                recipient_map[manager_id]["name"] = manager.get("EmployeeName") or manager.get("name")
                recipient_map[manager_id]["email"] = manager.get("Email") or manager.get("email")

        return sorted(recipient_map.values(), key=lambda item: str(item.get("empId") or ""))

    @staticmethod
    async def _resolve_hr_recipients() -> List[Dict[str, Any]]:
        records = await NotificationService._resolve_user_accounts_by_role("HR_ADMIN")
        recipients: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for record in records:
            user_id = str(record.get("userId") or "").strip()
            emp_id = str(record.get("empId") or "").strip()
            key = user_id or emp_id or str(record.get("email") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            recipient = {"role": "HR_ADMIN", "name": record.get("name") or record.get("email")}
            if user_id:
                recipient["userId"] = user_id
            if emp_id:
                recipient["empId"] = emp_id
            recipients.append(recipient)
        return recipients

    @staticmethod
    async def _create_notification_batch(
        *,
        recipients: List[Dict[str, Any]],
        notification_type: str,
        related_entity_type: str,
        related_entity_id: str,
        title: str,
        message: str,
        actor_user: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not recipients or not related_entity_id:
            return []

        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        created: List[Dict[str, Any]] = []
        seen_keys: set[str] = set()
        now = datetime.now(timezone.utc)

        for recipient in recipients:
            recipient_emp_id = str(recipient.get("empId") or "").strip()
            recipient_user_id = str(recipient.get("userId") or "").strip()
            recipient_key = recipient_user_id or recipient_emp_id or str(recipient.get("role") or "unassigned")
            duplicate_key = (recipient_key, notification_type, related_entity_type, related_entity_id)
            if duplicate_key in seen_keys:
                continue
            seen_keys.add(duplicate_key)

            doc = {
                "id": NotificationService._generate_notification_id(recipient_key, notification_type),
                "Title": title,
                "Message": message,
                "Type": notification_type,
                "notificationType": notification_type,
                "relatedEntityType": related_entity_type,
                "relatedEntityId": str(related_entity_id),
                "Status": "Unread",
                "isRead": False,
                "NotificationDate": now.strftime("%Y-%m-%d"),
                "createdAt": now.isoformat(),
                "metadata": metadata or {},
                "priority": "Medium",
                "recipientRole": recipient.get("role") or "SYSTEM",
            }

            actor_name = str(actor_user.get("name") or actor_user.get("email") or "System").strip() if actor_user else "System"
            actor_user_id = str(actor_user.get("userId") or "").strip() if actor_user else ""
            actor_emp_id = str(actor_user.get("empId") or "").strip() if actor_user else ""
            if actor_user_id:
                doc["actorUserId"] = actor_user_id
            if actor_emp_id:
                doc["actorEmpId"] = actor_emp_id
            if actor_name:
                doc["actorName"] = actor_name

            if recipient_emp_id:
                doc["EmpID"] = recipient_emp_id
            if recipient_user_id:
                doc["recipientUserId"] = recipient_user_id

            existing_filter = {
                "notificationType": notification_type,
                "relatedEntityType": related_entity_type,
                "relatedEntityId": str(related_entity_id),
            }
            if recipient_emp_id:
                existing_filter["EmpID"] = recipient_emp_id
            elif recipient_user_id:
                existing_filter["recipientUserId"] = recipient_user_id
            if await db.notifications.count_documents(existing_filter):
                continue

            await db.notifications.insert_one(doc)
            created.append(normalize_notification(doc))

        return created

    @staticmethod
    async def create_leave_request_notifications(leave_doc: Dict[str, Any], actor_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        emp_id = str(leave_doc.get("empId") or leave_doc.get("EmpID") or "").strip()
        if not emp_id:
            return []

        employee_name = str(leave_doc.get("empName") or await NotificationService._lookup_employee_name(emp_id)).strip() or "Employee"
        leave_type = str(leave_doc.get("leaveType") or leave_doc.get("LeaveType") or "Leave").strip() or "Leave"
        start_date = str(leave_doc.get("startDate") or leave_doc.get("StartDate") or "").strip()
        end_date = str(leave_doc.get("endDate") or leave_doc.get("EndDate") or "").strip()
        reason = str(leave_doc.get("reason") or leave_doc.get("Reason") or "Not provided").strip() or "Not provided"
        # Prefer the UI-friendly RequestID label when present for display, but use the canonical
        # id (d['id']) as the related_entity identifier so notification actions can reliably
        # resolve the underlying leave record.
        request_label = str(leave_doc.get("requestId") or leave_doc.get("RequestID") or "").strip()
        if not request_label:
            request_label = f"leave-{emp_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        canonical_id = str(leave_doc.get("id") or leave_doc.get("_id") or request_label).strip()

        title = f"{employee_name} has submitted a new leave request."
        message = (
            f"{employee_name} submitted a {leave_type} leave request from {start_date} to {end_date}. "
            f"Reason: {reason}. Status: Pending. Request ID: {request_label}."
        )
        metadata = {
            "employeeId": emp_id,
            "employeeName": employee_name,
            "leaveType": leave_type,
            "startDate": start_date,
            "endDate": end_date,
            "reason": reason,
            "status": "Pending",
            "requestId": request_label,
        }

        recipients = []
        recipients.extend(await NotificationService._resolve_hr_recipients())
        recipients.extend(await NotificationService._resolve_manager_recipients(emp_id))

        return await NotificationService._create_notification_batch(
            recipients=recipients,
            notification_type="leave_request_submitted",
            related_entity_type="leave",
            related_entity_id=canonical_id,
            title=title,
            message=message,
            actor_user=actor_user,
            metadata=metadata,
        )

    @staticmethod
    async def create_leave_decision_notifications(leave_doc: Dict[str, Any], actor_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        emp_id = str(leave_doc.get("empId") or leave_doc.get("EmpID") or "").strip()
        if not emp_id:
            return []

        employee_name = str(leave_doc.get("empName") or await NotificationService._lookup_employee_name(emp_id)).strip() or "Employee"
        final_status = str(leave_doc.get("status") or leave_doc.get("Status") or "Pending").strip().title()
        leave_type = str(leave_doc.get("leaveType") or leave_doc.get("LeaveType") or "Leave").strip() or "Leave"
        start_date = str(leave_doc.get("startDate") or leave_doc.get("StartDate") or "").strip()
        end_date = str(leave_doc.get("endDate") or leave_doc.get("EndDate") or "").strip()
        # Preserve the display RequestID separately and use the canonical id for related_entity linkage
        request_label = str(leave_doc.get("requestId") or leave_doc.get("RequestID") or "").strip()
        canonical_id = str(leave_doc.get("id") or leave_doc.get("_id") or request_label).strip()
        approver_name = str(actor_user.get("name") or actor_user.get("email") or "HR/Manager").strip() if actor_user else "HR/Manager"
        comment = str(leave_doc.get("approverComments") or leave_doc.get("ManagerComments") or "").strip()

        if final_status == "Approved":
            title = "Your leave request has been approved."
            message = f"Your {leave_type} leave request from {start_date} to {end_date} has been approved by {approver_name}. Request ID: {request_label}."
            notification_type = "leave_request_approved"
        else:
            title = "Your leave request has been rejected."
            message = f"Your {leave_type} leave request from {start_date} to {end_date} has been rejected by {approver_name}. Request ID: {request_label}."
            if comment:
                message = f"{message} Reason: {comment}."
            notification_type = "leave_request_rejected"

        metadata = {
            "employeeId": emp_id,
            "employeeName": employee_name,
            "leaveType": leave_type,
            "startDate": start_date,
            "endDate": end_date,
            "status": final_status,
            "requestId": request_label,
            "approverName": approver_name,
            "approverComments": comment,
        }

        return await NotificationService._create_notification_batch(
            recipients=[{"empId": emp_id, "role": "EMPLOYEE"}],
            notification_type=notification_type,
            related_entity_type="leave",
            related_entity_id=canonical_id,
            title=title,
            message=message,
            actor_user=actor_user,
            metadata=metadata,
        )

    @staticmethod
    async def create_shift_request_notifications(shift_doc: Dict[str, Any], actor_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        emp_id = str(shift_doc.get("empId") or shift_doc.get("EmpID") or "").strip()
        if not emp_id:
            return []

        employee_name = str(shift_doc.get("empName") or await NotificationService._lookup_employee_name(emp_id)).strip() or "Employee"
        shift_name = str(shift_doc.get("shiftName") or shift_doc.get("ShiftName") or "Shift").strip() or "Shift"
        requested_date = str(shift_doc.get("requestedDate") or shift_doc.get("ShiftDate") or "").strip()
        reason = str(shift_doc.get("reason") or shift_doc.get("Reason") or "Not provided").strip() or "Not provided"
        request_id = str(shift_doc.get("id") or shift_doc.get("ShiftID") or shift_doc.get("_id") or "").strip()
        if not request_id:
            request_id = f"shift-{emp_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        title = f"{employee_name} has submitted a shift request."
        message = f"{employee_name} submitted a shift request for {shift_name} on {requested_date}. Reason: {reason}. Status: Pending. Request ID: {request_id}."
        metadata = {
            "employeeId": emp_id,
            "employeeName": employee_name,
            "shiftName": shift_name,
            "requestedDate": requested_date,
            "reason": reason,
            "status": "Pending",
            "requestId": request_id,
        }

        recipients = []
        recipients.extend(await NotificationService._resolve_hr_recipients())
        recipients.extend(await NotificationService._resolve_manager_recipients(emp_id))

        return await NotificationService._create_notification_batch(
            recipients=recipients,
            notification_type="shift_request_submitted",
            related_entity_type="shift",
            related_entity_id=request_id,
            title=title,
            message=message,
            actor_user=actor_user,
            metadata=metadata,
        )

    @staticmethod
    async def create_shift_decision_notifications(shift_doc: Dict[str, Any], actor_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        emp_id = str(shift_doc.get("empId") or shift_doc.get("EmpID") or "").strip()
        if not emp_id:
            return []

        employee_name = str(shift_doc.get("empName") or await NotificationService._lookup_employee_name(emp_id)).strip() or "Employee"
        final_status = str(shift_doc.get("status") or shift_doc.get("ShiftSwapStatus") or "Pending").strip().title()
        shift_name = str(shift_doc.get("shiftName") or shift_doc.get("ShiftName") or "Shift").strip() or "Shift"
        requested_date = str(shift_doc.get("requestedDate") or shift_doc.get("ShiftDate") or "").strip()
        request_id = str(shift_doc.get("id") or shift_doc.get("ShiftID") or shift_doc.get("_id") or "").strip()
        approver_name = str(actor_user.get("name") or actor_user.get("email") or "HR/Manager").strip() if actor_user else "HR/Manager"
        comment = str(shift_doc.get("approverComments") or shift_doc.get("ManagerComments") or "").strip()

        if final_status == "Approved":
            title = "Your shift request has been approved."
            message = f"Your shift request for {shift_name} on {requested_date} has been approved by {approver_name}. Request ID: {request_id}."
            notification_type = "shift_request_approved"
        else:
            title = "Your shift request has been rejected."
            message = f"Your shift request for {shift_name} on {requested_date} has been rejected by {approver_name}. Request ID: {request_id}."
            if comment:
                message = f"{message} Reason: {comment}."
            notification_type = "shift_request_rejected"

        metadata = {
            "employeeId": emp_id,
            "employeeName": employee_name,
            "shiftName": shift_name,
            "requestedDate": requested_date,
            "status": final_status,
            "requestId": request_id,
            "approverName": approver_name,
            "approverComments": comment,
        }

        return await NotificationService._create_notification_batch(
            recipients=[{"empId": emp_id, "role": "EMPLOYEE"}],
            notification_type=notification_type,
            related_entity_type="shift",
            related_entity_id=request_id,
            title=title,
            message=message,
            actor_user=actor_user,
            metadata=metadata,
        )

    @staticmethod
    async def create(
        data: NotificationCreate
    ) -> Dict[str, Any]:
        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        status_value = NotificationService._normalize_status(data.status)
        notification_type = str(data.notificationType or data.type or "System").strip() or "System"
        title = str(data.title or data.message or notification_type).strip() or "Notification"
        message = str(data.message or data.title or title).strip() or "Notification"

        notification = {
            "id": NotificationService._generate_notification_id(
                str(data.recipientEmpId or data.empId or data.recipientUserId or data.actorUserId or "SYSTEM"),
                notification_type,
            ),
            "Title": title,
            "Message": message,
            "Type": notification_type,
            "notificationType": notification_type,
            "Status": status_value,
            "isRead": bool(data.isRead or status_value == "Read"),
            "NotificationDate": datetime.now().strftime("%Y-%m-%d"),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "priority": data.priority or "Medium",
            "metadata": data.metadata or {},
        }

        if data.empId:
            notification["EmpID"] = str(data.empId).strip()
        if data.recipientEmpId:
            notification["EmpID"] = str(data.recipientEmpId).strip()
        if data.recipientUserId:
            notification["recipientUserId"] = str(data.recipientUserId).strip()
        if data.recipientRole:
            notification["recipientRole"] = NotificationService._normalize_role_name(data.recipientRole)
        if data.actorUserId:
            notification["actorUserId"] = str(data.actorUserId).strip()
        if data.actorEmpId:
            notification["actorEmpId"] = str(data.actorEmpId).strip()
        if data.actorName:
            notification["actorName"] = str(data.actorName).strip()
        if data.relatedEntityType:
            notification["relatedEntityType"] = data.relatedEntityType
        if data.relatedEntityId:
            notification["relatedEntityId"] = str(data.relatedEntityId)

        await db.notifications.insert_one(notification)

        return normalize_notification(notification)

    @staticmethod
    async def get_by_id(notif_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        existing = await db.notifications.find_one(NotificationService._notification_match_query(notif_id))
        if not existing:
            return None
        return normalize_notification(existing)

    @staticmethod
    async def get_all(
        page: int = 1,
        size: int = 50,
        emp_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        query = NotificationService._scope_query_for_user(emp_id, user_id, role)
        if not query:
            return []

        skip = (page - 1) * size
        cursor = db.notifications.find(
            query,
            {"_id": 1, "id": 1, "EmpID": 1, "Title": 1, "Message": 1, "Type": 1, "notificationType": 1, "relatedEntityType": 1, "relatedEntityId": 1, "Status": 1, "isRead": 1, "NotificationDate": 1, "priority": 1, "metadata": 1, "recipientUserId": 1, "recipientRole": 1, "actorUserId": 1, "actorEmpId": 1, "actorName": 1}
        ).sort("_id", -1).skip(skip).limit(size)

        items = await cursor.to_list(length=size)

        return [
            normalize_notification(item)
            for item in items
        ]

    @staticmethod
    async def count_unread(
        emp_id: Optional[str] = None,
        user_id: Optional[str] = None,
        *,
        role: Optional[str] = None,
    ) -> int:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")

        status_query: Dict[str, Any] = {"$or": [{"Status": {"$in": ["Unread", "UNREAD", "unread"]}}, {"isRead": False}]}
        scope_query = NotificationService._scope_query_for_user(emp_id, user_id, role)

        if not scope_query:
            return 0

        query = {"$and": [scope_query, status_query]}
        return await db.notifications.count_documents(query)

    @staticmethod
    async def mark_read(
        notif_id: str,
        emp_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> bool:
        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        existing = await db.notifications.find_one(NotificationService._notification_match_query(notif_id))
        if not existing:
            return False

        if emp_id and str(emp_id).strip() or user_id and str(user_id).strip():
            if not NotificationService.user_can_access_notification(
                existing,
                emp_id=emp_id,
                user_id=user_id,
                role=role,
            ):
                return False

        result = await db.notifications.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "Status": "Read",
                    "isRead": True,
                    "readAt": datetime.now(timezone.utc).isoformat(),
                }
            }
        )

        return result.modified_count > 0 or result.matched_count > 0

    @staticmethod
    async def mark_all_read(
        emp_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> bool:
        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        query = NotificationService._scope_query_for_user(emp_id, user_id, role)
        if not query:
            return False

        await db.notifications.update_many(
            query,
            {
                "$set": {
                    "Status": "Read",
                    "isRead": True,
                    "readAt": datetime.now(timezone.utc).isoformat(),
                }
            }
        )

        return True


# ==========================================================================
# 9. Audit Service
# ==========================================================================

class AuditService:

    @staticmethod
    async def get_all() -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # Include MongoDB _id so older audit records that lack an explicit
        # 'id' can be synthesized by normalize_audit_log. Returning full
        # documents is acceptable for audit logs (sensitive fields are
        # already API-oriented in this collection).
        cursor = db.audit_logs.find()

        items = await cursor.to_list(
            length=None
        )

        return [
            normalize_audit_log(item)
            for item in items
        ]

    @staticmethod
    async def create(
        data: AuditLogCreate
    ) -> Dict[str, Any]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        # ---------------------------------------------------------
        # Audit collection already uses API-friendly field names:
        #
        # actor
        # action
        # module
        # ipAddress
        # status
        # id
        # timestamp
        #
        # Therefore no raw-field conversion is required.
        # ---------------------------------------------------------

        doc = data.model_dump()

        # ---------------------------------------------------------
        # Generate unique audit log ID
        # ---------------------------------------------------------

        doc["id"] = (
            f"AUD-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        # ---------------------------------------------------------
        # Generate timestamp
        # ---------------------------------------------------------

        doc["timestamp"] = datetime.now().isoformat()

        # ---------------------------------------------------------
        # Insert into MongoDB
        # ---------------------------------------------------------

        await db.audit_logs.insert_one(doc)

        return normalize_audit_log(doc)

# ==========================================================================
# 10. AI Prediction Service
# ==========================================================================

class AIPredictionService:
    @staticmethod
    async def count_attrition_above(threshold: float = 0.7) -> int:
        db = get_database()
        if db is None:
            raise RuntimeError("MongoDB database is not connected.")
        return await db.ai_predictions.count_documents({"AttritionRisk": {"$gt": threshold}})


    @staticmethod
    async def get_all(
        emp_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        query: Dict[str, Any] = {}

        # ---------------------------------------------------------
        # Filter by employee
        # ---------------------------------------------------------

        if emp_id:
            query["EmpID"] = emp_id

        # ---------------------------------------------------------
        # Read AI prediction records
        # ---------------------------------------------------------

        cursor = db.ai_predictions.find(
            query,
            {"_id": 0}
        )

        items = await cursor.to_list(
            length=None
        )

        return [
            normalize_ai_prediction(item)
            for item in items
        ]

    @staticmethod
    async def get_by_emp_id(
        emp_id: str
    ) -> Optional[Dict[str, Any]]:

        db = get_database()

        if db is None:
            raise RuntimeError(
                "MongoDB database is not connected."
            )

        prediction = await db.ai_predictions.find_one(
            {
                "EmpID": emp_id
            },
            {
                "_id": 0
            }
        )

        if prediction:
            return normalize_ai_prediction(
                prediction
            )

        return None