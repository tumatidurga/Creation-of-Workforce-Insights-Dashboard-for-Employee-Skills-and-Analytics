import re
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List

ALLOWED_AVATAR_IDS = {f"avatar-{i:02d}" for i in range(1, 9)}

MAX_REPORT_EXPORT_ROWS = 1000
MAX_PAYROLL_EXPORT_ROWS = 1000
VALID_REPORT_FORMATS = {"PDF", "XLSX", "CSV", "JSON"}
VALID_REPORT_DATE_RANGES = {
    "Current Month",
    "Current Quarter",
    "Last 30 Days",
    "Year to Date",
    "All Time",
    "Current Week",
}

# --------------------------------------------------------------------------
# Reports Schemas
# --------------------------------------------------------------------------
class ReportFilter(BaseModel):
    department: Optional[str] = "All"
    dateRange: Optional[str] = "Current Month"
    format: Optional[str] = "PDF"
    limit: Optional[int] = Field(default=None, ge=1)

class ReportSummaryResponse(BaseModel):
    reportName: str
    generatedAt: str
    departmentFilter: str
    totalRecords: int
    metrics: Dict[str, Any]
    downloadUrl: str

# --------------------------------------------------------------------------
# Settings Schemas
# --------------------------------------------------------------------------
class SystemSettings(BaseModel):
    companyName: Optional[str] = None
    timeZone: Optional[str] = None
    currency: Optional[str] = None
    biometricSyncEnabled: Optional[bool] = None
    aiModel: Optional[str] = None
    attritionAlertThreshold: Optional[float] = None
    autoApproveLeavesUnderDays: Optional[int] = None
    sessionTimeoutMinutes: Optional[int] = None

# --------------------------------------------------------------------------
# User Profile Schemas
# --------------------------------------------------------------------------
class UserProfile(BaseModel):
    userId: Optional[str] = None
    empId: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    personalEmail: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    jobRole: Optional[str] = None
    dateOfBirth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    emergencyContactName: Optional[str] = None
    emergencyContactRelationship: Optional[str] = None
    emergencyContactPhone: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[str] = None
    qualifications: Optional[str] = None
    avatarId: Optional[str] = None
    avatar: Optional[str] = None
    mfaEnabled: Optional[bool] = None
    lastLogin: Optional[str] = None

    @field_validator("phone", "emergencyContactPhone")
    @classmethod
    def validate_phone_value(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        if not re.match(r"^\+?[0-9\s\-()]{7,20}$", cleaned):
            raise ValueError("Phone number must contain 7 to 20 digits, spaces, parentheses, or dashes.")
        return cleaned

    @field_validator("personalEmail")
    @classmethod
    def validate_personal_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
            raise ValueError("Personal email must be a valid email address.")
        return cleaned

    @field_validator("dateOfBirth")
    @classmethod
    def validate_birth_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        parsed = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(cleaned, fmt).date()
                break
            except ValueError:
                pass
        if parsed is None:
            try:
                parsed = date.fromisoformat(cleaned)
            except ValueError as exc:
                raise ValueError("Date of birth must be a valid ISO date or yyyy-mm-dd value.") from exc
        if parsed > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return parsed.isoformat()

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        cleaned = []
        seen = set()
        for item in value:
            if item is None:
                continue
            normalized = str(item).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(normalized)
        return cleaned or None

    @field_validator("avatarId")
    @classmethod
    def validate_avatar_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        normalized = cleaned.lower()
        if normalized not in ALLOWED_AVATAR_IDS:
            raise ValueError("avatarId must be one of the approved local avatar IDs.")
        return normalized

    @field_validator("avatar")
    @classmethod
    def validate_avatar_value(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        normalized = cleaned.lower()
        if normalized in ALLOWED_AVATAR_IDS:
            return normalized
        if normalized.startswith("http://") or normalized.startswith("https://"):
            raise ValueError("External avatar URLs are not allowed. Use avatarId instead.")
        raise ValueError("Avatar must be a valid local avatarId.")
