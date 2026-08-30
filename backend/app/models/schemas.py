from pydantic import BaseModel, Field, EmailStr, ConfigDict, AliasChoices
from typing import List, Optional, Any, Dict, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

# --------------------------------------------------------------------------
# Generic Paginated Response Schema
# --------------------------------------------------------------------------
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    summary: Optional[Dict[str, Any]] = None

# --------------------------------------------------------------------------
# Emergency Contact & Employee Schemas
# --------------------------------------------------------------------------
class EmergencyContact(BaseModel):
    name: Optional[str] = Field(default=None, description="Emergency contact full name")
    relationship: Optional[str] = Field(default=None, description="Relationship to employee")
    phone: Optional[str] = Field(default=None, description="Contact phone number")

class EmployeeBase(BaseModel):
    empId: str = Field(..., description="Unique employee ID from MongoDB (for example EMP000001)")
    firstName: Optional[str] = Field(default=None, description="First name derived from EmployeeName when available")
    lastName: Optional[str] = Field(default=None, description="Last name derived from EmployeeName when available")
    email: Optional[EmailStr] = Field(default=None, description="Corporate email")
    phone: Optional[str] = Field(default=None, description="Phone number")
    avatar: Optional[str] = Field(default=None, description="Avatar image URL when present")
    gender: Optional[str] = Field(default=None, description="Gender")
    age: Optional[int] = Field(default=None, ge=18, le=80, description="Age in years")
    department: Optional[str] = Field(default=None, description="Department name")
    jobRole: Optional[str] = Field(default=None, description="Job role title")
    designation: Optional[str] = Field(default=None, description="Designation title when available")
    jobLevel: Optional[int] = Field(default=None, ge=1, le=10, description="Job level")
    managerId: Optional[str] = Field(default=None, description="Reporting manager ID (legacy compatibility)")
    managerEmpId: Optional[str] = Field(default=None, description="Canonical reporting manager employee ID")
    managerName: Optional[str] = Field(default=None, description="Manager name when available")
    location: Optional[str] = Field(default=None, description="Office or work location")
    status: Optional[str] = Field(default=None, description="Employment status")
    monthlyIncome: Optional[float] = Field(default=None, ge=0, description="Monthly base salary")
    yearsAtCompany: Optional[float] = Field(default=None, ge=0, description="Years at company")
    yearsInRole: Optional[float] = Field(default=None, ge=0, description="Years in current role")
    yearsWithManager: Optional[float] = Field(default=None, ge=0, description="Years with current manager")
    workLifeBalanceScore: Optional[int] = Field(default=None, ge=1, le=5, description="Work-life balance score")
    jobSatisfactionScore: Optional[int] = Field(default=None, ge=1, le=5, description="Job satisfaction score")
    environmentSatisfactionScore: Optional[int] = Field(default=None, ge=1, le=5, description="Environment satisfaction score")
    relationshipSatisfactionScore: Optional[int] = Field(default=None, ge=1, le=5, description="Relationship satisfaction score")
    skills: Optional[List[str]] = Field(default=None, description="Skill tags when present")
    education: Optional[str] = Field(default=None, description="Highest education level")
    educationField: Optional[str] = Field(default=None, description="Education field")
    emergencyContact: Optional[EmergencyContact] = Field(default=None, description="Emergency contact information when present")
    address: Optional[str] = Field(default=None, description="Residential address when present")

    # Optional performance & AI fields (enriched by GET /employees/{id})
    performanceScore: Optional[int] = Field(default=None, description="Overall performance score (0-100)")
    productivityScore: Optional[int] = Field(default=None, description="Productivity percentage")
    kpiCompletionRate: Optional[int] = Field(default=None, description="KPI completion percentage")
    goalsCompleted: Optional[int] = Field(default=None, description="Number of goals completed")
    totalGoals: Optional[int] = Field(default=None, description="Total goals assigned")
    promotionRecommended: Optional[bool] = Field(default=None, description="Promotion recommended flag")
    aiFeedback: Optional[str] = Field(default=None, description="AI manager evaluation or recommendation")
    lastPayrollMonth: Optional[str] = Field(default=None, description="Month of the latest payroll record")
    lastNetPay: Optional[float] = Field(default=None, description="Net pay amount of the latest payroll record")
    attritionRisk: Optional[float] = Field(default=None, description="AI-predicted attrition risk (0-1) or risk score")

class EmployeeCreate(EmployeeBase):
    # Allow empId to be optionally omitted during creation so the server can generate one.
    # Keep all other EmployeeBase validations.
    empId: Optional[str] = None

class EmployeeUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    jobRole: Optional[str] = None
    designation: Optional[str] = None
    jobLevel: Optional[int] = None
    managerId: Optional[str] = None
    managerEmpId: Optional[str] = None
    managerName: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    monthlyIncome: Optional[float] = None
    yearsAtCompany: Optional[float] = None
    yearsInRole: Optional[float] = None
    skills: Optional[List[str]] = None
    address: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --------------------------------------------------------------------------
# Attendance Schemas
# --------------------------------------------------------------------------
class AttendanceBase(BaseModel):
    id: Optional[str] = None
    empId: str
    empName: Optional[str] = None
    avatar: Optional[str] = None
    department: Optional[str] = None
    date: Optional[str] = None
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    workingHours: Optional[float] = None
    status: Optional[str] = None
    isAnomaly: Optional[bool] = None
    anomalyReason: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    gpsVerified: Optional[bool] = None
    distanceFromOffice: Optional[float] = None
    geofenceStatus: Optional[str] = None
    workMode: Optional[str] = None
    workContext: Optional[Dict[str, Any]] = None
    allowedVerificationMethods: Optional[List[str]] = None
    verificationMethod: Optional[str] = None
    verificationStatus: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    locationAudit: Optional[Dict[str, Any]] = None
    attendanceException: Optional[Dict[str, Any]] = None
    reviewStatus: Optional[str] = None

class AttendanceCheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    empId: str
    checkInTime: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("checkInTime", "checkIn"),
        description="Attendance check-in time using the current API or legacy payload key",
    )
    date: Optional[str] = Field(default=None, description="Legacy compatibility field for the attendance date")
    checkOut: Optional[str] = Field(default=None, description="Legacy compatibility field; not used for check-in creation")
    workingHours: Optional[float] = Field(default=None, description="Legacy compatibility field; not used for check-in creation")
    status: Optional[str] = Field(default=None, description="Legacy compatibility field; not used to override attendance status")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    verificationMethod: Optional[str] = Field(default=None, description="Selected attendance verification method")
    verificationStatus: Optional[str] = Field(default=None, description="Verification status to persist with the attendance record")
    workMode: Optional[str] = Field(default=None, description="Employee work mode for the day")
    workContext: Optional[Dict[str, Any]] = Field(default=None, description="Context snapshot for policy and work arrangement")
    allowedVerificationMethods: Optional[List[str]] = Field(default=None, description="Allowed verification methods for this policy")
    verification: Optional[Dict[str, Any]] = Field(default=None, description="Arbitrary verification metadata")
    locationAudit: Optional[Dict[str, Any]] = Field(default=None, description="Location GPS audit metadata")

class AttendanceCheckOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    empId: str
    checkOutTime: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("checkOutTime", "checkOut"),
        description="Attendance check-out time using the current API or legacy payload key",
    )
    date: Optional[str] = Field(default=None, description="Legacy compatibility field for the attendance date")
    checkIn: Optional[str] = Field(default=None, description="Legacy compatibility field; not used for check-out creation")
    workingHours: Optional[float] = Field(default=None, description="Legacy compatibility field; not used to override working hours")
    status: Optional[str] = Field(default=None, description="Legacy compatibility field; not used to override attendance status")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    verificationMethod: Optional[str] = None
    verificationStatus: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None

class AttendanceExceptionBase(BaseModel):
    id: Optional[str] = None
    empId: str
    employeeName: Optional[str] = None
    date: Optional[str] = None
    reason: Optional[str] = None
    description: Optional[str] = None
    workMode: Optional[str] = None
    selectedVerificationMethod: Optional[str] = None
    gpsData: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(default="Pending", description="Submission status")
    reviewStatus: Optional[str] = Field(default="Pending", description="HR/manager review status")
    createdAt: Optional[str] = None

class AttendanceExceptionCreate(AttendanceExceptionBase):
    pass

class AttendanceExceptionResponse(AttendanceExceptionBase):
    pass

# --------------------------------------------------------------------------
# Leave Schemas
# --------------------------------------------------------------------------
class LeaveRequestBase(BaseModel):
    id: Optional[str] = None
    empId: str
    empName: Optional[str] = None
    department: Optional[str] = None
    leaveType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    days: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    appliedOn: Optional[str] = None
    approverComments: Optional[str] = None
    leaveBalance: Optional[int] = None
    decisionByUserId: Optional[str] = Field(default=None, description="User ID of the manager or HR approver who made the final decision")
    decisionByEmpId: Optional[str] = Field(default=None, description="Employee ID of the approver when available")
    decisionByName: Optional[str] = Field(default=None, description="Display name of the approver")
    decisionRole: Optional[str] = Field(default=None, description="Role of the approver at decision time")
    decisionAt: Optional[str] = Field(default=None, description="ISO timestamp when final decision was recorded")
    decisionComments: Optional[str] = Field(default=None, description="Final decision comments captured on the request")

class LeaveStatusUpdate(BaseModel):
    status: str
    approverComments: Optional[str] = None

class LeaveBalanceItem(BaseModel):
    total: int
    used: int
    remaining: int

class LeaveBalances(BaseModel):
    casualLeave: LeaveBalanceItem
    sickLeave: LeaveBalanceItem
    earnedLeave: LeaveBalanceItem
    parentalLeave: LeaveBalanceItem

# --------------------------------------------------------------------------
# Shift Schemas
# --------------------------------------------------------------------------

from typing import Optional, Literal
from pydantic import BaseModel


class ShiftRequestBase(BaseModel):
    empId: str
    requestedShift: Optional[str] = None
    requestedDate: Optional[str] = None
    reason: Optional[str] = None
    shiftName: Optional[str] = None
    shiftStart: Optional[str] = None
    shiftEnd: Optional[str] = None
    overtimeHours: Optional[float] = None


class ShiftRequestResponse(BaseModel):
    id: Optional[str] = None
    empId: str
    empName: Optional[str] = None
    department: Optional[str] = None
    requestedShift: Optional[str] = None
    requestedDate: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[Literal["Pending", "Approved", "Rejected", "Not Requested"]] = None
    appliedOn: Optional[str] = None
    approverComments: Optional[str] = None
    approverName: Optional[str] = None
    decisionByUserId: Optional[str] = Field(default=None, description="User ID of the manager or HR approver who made the final decision")
    decisionByEmpId: Optional[str] = Field(default=None, description="Employee ID of the approver when available")
    decisionByName: Optional[str] = Field(default=None, description="Display name of the approver")
    decisionRole: Optional[str] = Field(default=None, description="Role of the approver at decision time")
    decisionAt: Optional[str] = Field(default=None, description="ISO timestamp when final decision was recorded")
    decisionComments: Optional[str] = Field(default=None, description="Final decision comments captured on the request")


class ShiftStatusUpdate(BaseModel):
    status: Literal["Pending", "Approved", "Rejected"]
    approverComments: Optional[str] = None

# --------------------------------------------------------------------------
# Timesheet Schemas
# --------------------------------------------------------------------------
class TimesheetBase(BaseModel):
    id: Optional[str] = None
    empId: str
    empName: Optional[str] = None
    date: Optional[str] = None
    projectName: Optional[str] = None
    taskDescription: Optional[str] = None
    hoursLogged: Optional[float] = None
    isBillable: Optional[bool] = None
    status: Optional[str] = None
    clientBillingHours: Optional[float] = None

# --------------------------------------------------------------------------
# Payroll Schemas
# --------------------------------------------------------------------------
class PayrollBase(BaseModel):
    id: Optional[str] = None
    empId: str
    empName: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    month: Optional[str] = None
    baseSalary: Optional[float] = None
    overtimeHours: Optional[float] = None
    overtimePay: Optional[float] = None
    performanceBonus: Optional[float] = None
    incentives: Optional[float] = None
    grossEarnings: Optional[float] = None
    taxDeductions: Optional[float] = None
    attendanceDeductions: Optional[float] = None
    netPay: Optional[float] = None
    status: Optional[str] = None

# --------------------------------------------------------------------------
# Performance Schemas
# --------------------------------------------------------------------------

class PerformanceBase(BaseModel):
    empId: str
    empName: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    performanceScore: Optional[int] = Field(default=None, ge=0, le=100, description="Overall performance score (0-100) when available")
    productivityScore: Optional[int] = Field(default=None, ge=0, le=100, description="Productivity score (0-100) when available")
    kpiCompletionRate: Optional[int] = Field(default=None, ge=0, le=100, description="KPI completion rate (0-100) when available")
    learningProgress: Optional[int] = Field(default=None, ge=0, le=100, description="Learning progress percentage (0-100) when available")
    goalsCompleted: Optional[int] = Field(default=None, ge=0, description="Number of completed goals when available")
    totalGoals: Optional[int] = Field(default=None, ge=0, description="Total number of goals when available")
    promotionRecommended: Optional[bool] = Field(default=None, description="Whether promotion is recommended when derived from real data")
    aiFeedback: Optional[str] = Field(default=None, description="AI-generated performance feedback when available")


class PerformanceUpdate(BaseModel):
    performanceScore: Optional[int] = Field(default=None, ge=0, le=100, description="Overall performance score (0-100)")
    productivityScore: Optional[int] = Field(default=None, ge=0, le=100, description="Productivity score (0-100)")
    kpiCompletionRate: Optional[int] = Field(default=None, ge=0, le=100, description="KPI completion rate (0-100)")
    learningProgress: Optional[int] = Field(default=None, ge=0, le=100, description="Learning progress percentage (0-100)")
    goalsCompleted: Optional[int] = Field(default=None, ge=0, description="Number of completed goals")
    totalGoals: Optional[int] = Field(default=None, ge=0, description="Total number of goals")
    promotionRecommended: Optional[bool] = Field(default=None, description="Whether promotion is recommended")
    aiFeedback: Optional[str] = Field(default=None, description="AI-generated performance feedback")
# --------------------------------------------------------------------------
# Notification & Audit Log Schemas
# --------------------------------------------------------------------------

class NotificationCreate(BaseModel):
    empId: Optional[str] = Field(default=None, description="Primary employee recipient when the notification is tied to a specific employee")
    recipientEmpId: Optional[str] = Field(default=None, description="Explicit recipient employee ID for recipient-specific notifications")
    recipientUserId: Optional[str] = Field(default=None, description="Explicit user account ID when the recipient is not an employee record")
    recipientRole: Optional[str] = Field(default=None, description="Explicit workflow role target for HR_ADMIN or MANAGER notifications")
    actorUserId: Optional[str] = Field(default=None, description="User account ID of the actor who triggered the notification")
    actorEmpId: Optional[str] = Field(default=None, description="Employee ID of the actor who triggered the notification")
    actorName: Optional[str] = Field(default=None, description="Display name of the actor")
    title: Optional[str] = Field(default=None, description="Notification title")
    message: Optional[str] = Field(default=None, description="Notification message")
    type: Optional[str] = Field(default=None, description="Legacy notification type alias")
    notificationType: Optional[str] = Field(default=None, description="Canonical notification type such as leave_request_submitted")
    relatedEntityType: Optional[str] = Field(default=None, description="Domain entity related to the notification, such as leave or shift")
    relatedEntityId: Optional[str] = Field(default=None, description="Identifier of the related leave or shift request")
    status: Optional[str] = Field(default=None, description="Notification status such as Read or Unread")
    isRead: Optional[bool] = Field(default=False, description="Whether the notification has been read")
    priority: Optional[str] = Field(default=None, description="Notification priority: Low, Medium, High")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional structured notification metadata")


class NotificationBase(BaseModel):
    id: Optional[str] = None
    empId: Optional[str] = None
    recipientEmpId: Optional[str] = None
    recipientUserId: Optional[str] = None
    recipientRole: Optional[str] = None
    actorUserId: Optional[str] = None
    actorEmpId: Optional[str] = None
    actorName: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    type: Optional[str] = None
    notificationType: Optional[str] = None
    relatedEntityType: Optional[str] = None
    relatedEntityId: Optional[str] = None
    isRead: Optional[bool] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogCreate(BaseModel):
    actor: Optional[str] = Field(default=None, description="User or system that performed the action")
    action: Optional[str] = Field(default=None, description="Action that was performed")
    module: Optional[str] = Field(default=None, description="System module where the action occurred")
    ipAddress: Optional[str] = Field(default=None, description="IP address of the actor")
    status: Optional[str] = Field(default=None, description="Audit status such as SUCCESS or FAILED")


class AuditLogBase(BaseModel):
    id: Optional[str] = None
    actor: Optional[str] = None
    action: Optional[str] = None
    module: Optional[str] = None
    timestamp: Optional[str] = None
    ipAddress: Optional[str] = None
    status: Optional[str] = None

# --------------------------------------------------------------------------
# AI Chat & Analytics Schemas
# --------------------------------------------------------------------------
class AIChatRequest(BaseModel):
    message: Optional[str] = None
    prompt: Optional[str] = None
    role: Optional[str] = "HR Administrator"
    context: Optional[Dict[str, Any]] = None

class AIChatResponse(BaseModel):
    reply: str
    text: str
    dataWidget: Optional[Dict[str, Any]] = None
    model: str = "gemini-3.6-flash"

class AIInsightRequest(BaseModel):
    type: Optional[str] = "General"
    department: Optional[str] = "Entire Organization"

class DashboardMetrics(BaseModel):
    totalEmployees: int
    activeEmployees: int
    attendanceRate: str
    productivityScore: Optional[float] = None
    attritionRiskCount: int
    totalMonthlyPayroll: float
    pendingLeaveRequests: int
    pendingShiftRequests: int

# --------------------------------------------------------------------------
# AI Prediction Schemas
# --------------------------------------------------------------------------

class AIPredictionBase(BaseModel):
    empId: str = Field(
        ...,
        description="Unique Employee ID"
    )

    attritionRisk: float = Field(
        ...,
        ge=0,
        le=1,
        description="Predicted employee attrition risk (0-1)"
    )

    skillGapScore: float = Field(
        ...,
        ge=0,
        le=1,
        description="Employee skill gap score (0-1)"
    )

    workforceHealthScore: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall workforce health score (0-100)"
    )

    recommendation: str = Field(
        ...,
        description="AI-generated workforce recommendation"
    )

    predictionDate: str = Field(
        ...,
        description="Date when the prediction was generated"
    )


class AIPredictionResponse(AIPredictionBase):
    id: Optional[str] = None