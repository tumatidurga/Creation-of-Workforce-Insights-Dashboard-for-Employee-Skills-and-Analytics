import bcrypt
import jwt
import uuid
import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.database import get_database

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=1, description="Employee ID or email")
    password: str = Field(..., min_length=1, description="Password")


class AuthenticatedUser(BaseModel):
    userId: Optional[str] = None
    empId: Optional[str] = None
    managerLoginId: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    # Optional password status metadata: 'default' or 'custom'
    passwordStatus: Optional[str] = None
    mustChangePassword: Optional[bool] = False


class AuthTokenResponse(BaseModel):
    token: str
    user: AuthenticatedUser


def _parse_utc_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def _normalize_password_status(account: Optional[Dict[str, Any]]) -> Optional[str]:
    if not account:
        return None
    existing_status = str(account.get("passwordStatus") or "").strip().lower()
    if existing_status in {"default", "custom"}:
        return existing_status

    emp_id = str(account.get("empId") or "").strip()
    password_hash = str(account.get("passwordHash") or "").strip()
    if emp_id and password_hash:
        try:
            if bcrypt.checkpw(emp_id.encode("utf-8"), password_hash.encode("utf-8")):
                return "default"
        except Exception:
            pass
    return "custom" if password_hash else None


async def ensure_bootstrap_accounts() -> None:
    db = get_database()
    if db is None:
        return

    existing = await db.user_accounts.count_documents({})
    if existing > 0 or not settings.AUTH_BOOTSTRAP_PASSWORD:
        return

    # Avoid depending on a legacy CURRENT_USER placeholder record. Use explicit defaults for
    # the bootstrap HR admin identity instead of reading a non-existent profile by that name.
    employee_doc = await db.employees.find_one({"EmpID": "EMP000001"})

    hr_email = "priya.sharma@enterprise.com"
    hr_name = "Priya Sharma"
    employee_email = (employee_doc.get("Email") if employee_doc else "aarav.sharma.1@company.com").strip().lower()
    employee_name = (employee_doc.get("EmployeeName") if employee_doc else "Aarav A. Sharma").strip()
    employee_emp_id = (employee_doc.get("EmpID") if employee_doc else "EMP000001").strip()

    password_hash = bcrypt.hashpw(settings.AUTH_BOOTSTRAP_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now = datetime.now(timezone.utc).isoformat()

    # Create a single bootstrap administrative account with the provided bootstrap password.
    # For safety, the employee self-service account is created without a usable password and marked INACTIVE.
    # This prevents multiple accounts sharing the same bootstrap password while giving operators a single
    # initial admin account to sign in and perform user provisioning.
    await db.user_accounts.insert_many([
        {
            "userId": "hr-admin",
            "empId": None,
            "name": hr_name,
            "email": hr_email,
            "role": "HR_ADMIN",
            "passwordHash": password_hash,
            "passwordStatus": "custom",
            "mustChangePassword": False,
            "passwordChangedAt": None,
            "status": "ACTIVE",
            "createdAt": now,
            "updatedAt": now,
        },
        {
            "userId": "employee-self-service",
            "empId": employee_emp_id,
            "name": employee_name,
            "email": employee_email,
            "role": "EMPLOYEE",
            # No passwordHash for the seeded employee account. Admin must enable/create a password via a secure flow.
            "status": "INACTIVE",
            "passwordStatus": "custom",
            "mustChangePassword": False,
            "passwordChangedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
    ])


async def ensure_manager_accounts(dry_run: bool = False) -> Dict[str, int]:
    """Create missing MANAGER user_accounts from existing employee records.

    Safety rules:
    - only employees with Role == 'Manager' are eligible
    - existing accounts are never overwritten
    - HR_ADMIN is never touched
    - no employee documents are modified
    - repeated execution is idempotent
    """
    db = get_database()
    if db is None:
        try:
            from backend.app.database import connect_to_mongo
            await connect_to_mongo()
            db = get_database()
        except Exception:
            return {"created": 0, "existing": 0, "missing": 0}
    if db is None:
        return {"created": 0, "existing": 0, "missing": 0}

    manager_docs = await db.employees.find(
        {"Role": "Manager"},
        {
            "_id": 0,
            "EmpID": 1,
            "EmployeeName": 1,
            "Email": 1,
            "email": 1,
            "name": 1,
        },
    ).to_list(length=None)

    existing_accounts = await db.user_accounts.find(
        {},
        {"_id": 1, "empId": 1, "email": 1, "userId": 1, "role": 1, "managerLoginId": 1},
    ).to_list(length=None)

    existing_emp_ids = {str(account.get("empId") or "").strip() for account in existing_accounts if str(account.get("empId") or "").strip()}
    existing_emails = {str(account.get("email") or "").strip().lower() for account in existing_accounts if str(account.get("email") or "").strip()}
    manager_login_map = build_deterministic_manager_login_map([str(doc.get("EmpID") or "").strip() for doc in manager_docs if str(doc.get("EmpID") or "").strip()])

    created = 0
    existing = 0
    missing = 0
    now = datetime.now(timezone.utc).isoformat()

    for doc in manager_docs:
        emp_id = str(doc.get("EmpID") or doc.get("empId") or "").strip()
        if not emp_id:
            missing += 1
            continue

        email = str(doc.get("Email") or doc.get("email") or "").strip().lower()
        account_exists = await db.user_accounts.find_one({"$or": [{"empId": emp_id}, {"userId": emp_id}, {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}]})
        if account_exists:
            if str(account_exists.get("role") or "").upper() == "MANAGER":
                existing += 1
                continue
            if str(account_exists.get("role") or "").upper() == "HR_ADMIN":
                existing += 1
                continue
            if not dry_run:
                update_values = {
                    "role": "MANAGER",
                    "updatedAt": now,
                }
                if not account_exists.get("name"):
                    update_values["name"] = str(doc.get("EmployeeName") or doc.get("name") or emp_id)
                if not account_exists.get("email") and email:
                    update_values["email"] = email
                if not account_exists.get("userId"):
                    update_values["userId"] = emp_id
                if not account_exists.get("empId"):
                    update_values["empId"] = emp_id
                if not account_exists.get("managerLoginId") and emp_id in manager_login_map:
                    update_values["managerLoginId"] = manager_login_map[emp_id]
                await db.user_accounts.update_one({"_id": account_exists["_id"]}, {"$set": update_values})
            existing += 1
            continue

        if emp_id in existing_emp_ids:
            existing += 1
            continue

        if email and email in existing_emails:
            existing += 1
            continue

        if dry_run:
            missing += 1
            continue

        name = str(doc.get("EmployeeName") or doc.get("name") or "").strip() or emp_id
        password_hash = bcrypt.hashpw(emp_id.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        login_id = manager_login_map.get(emp_id, f"MGR{len(manager_login_map):06d}")
        await db.user_accounts.insert_one({
            "userId": emp_id,
            "empId": emp_id,
            "managerLoginId": login_id,
            "email": email or None,
            "name": name,
            "role": "MANAGER",
            "passwordHash": password_hash,
            "passwordStatus": "default",
            "mustChangePassword": False,
            "passwordChangedAt": None,
            "status": "ACTIVE",
            "createdAt": now,
            "updatedAt": now,
        })
        created += 1

    manager_total = len(manager_docs)
    if dry_run:
        missing = max(manager_total - existing, 0)
    else:
        missing = max(manager_total - (existing + created), 0)
    return {
        "total_manager_employees": manager_total,
        "created": created,
        "existing": existing,
        "missing": missing,
    }


async def get_authenticated_user(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("authorization", "")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please sign in again.",
        )

    if not payload.get("empId") and not payload.get("email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Employee profile could not be loaded.",
        )

    # --- REVOCATION CHECK ---
    # Compute token hash and consult auth_revoked_tokens collection.
    try:
        db = get_database()
        # Fail closed: if the revocation database is not available, do not allow authentication.
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication subsystem temporarily unavailable.",
            )

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        query_or = []
        jti = payload.get("jti")
        if jti:
            query_or.append({"jti": jti})
        query_or.append({"token_hash": token_hash})

        revoked_doc = await db.auth_revoked_tokens.find_one({"$or": query_or})
        if revoked_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please sign in again.",
            )

        account_query = {}
        if payload.get("empId"):
            account_query = {"empId": payload.get("empId")}
        elif payload.get("email"):
            account_query = {"email": {"$regex": f"^{payload.get('email')}$", "$options": "i"}}
        else:
            account_query = {"userId": payload.get("sub")}

        account = await db.user_accounts.find_one(account_query)
        if account:
            password_changed_at = account.get("passwordChangedAt")
            if password_changed_at:
                changed_dt = _parse_utc_datetime(password_changed_at)
                if changed_dt is not None:
                    token_iat = payload.get("iat")
                    if token_iat is not None:
                        try:
                            token_iat_value = float(token_iat)
                        except (TypeError, ValueError):
                            token_iat_value = None
                        if token_iat_value is not None and token_iat_value < changed_dt.timestamp():
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Your session has expired. Please sign in again.",
                            )
    except HTTPException:
        raise
    except Exception:
        # If the revocation subsystem is unavailable, fail closed by returning 503 (service degraded)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication subsystem temporarily unavailable.",
        )

    return payload


def _normalize_role(role: Any) -> str:
    return str(role or "").strip().upper()


def build_deterministic_manager_login_map(manager_emp_ids: list[str]) -> Dict[str, str]:
    """Return a stable MGR000001-style login mapping for manager EmpIDs."""
    unique_sorted = []
    seen = set()
    for emp_id in sorted({str(emp_id).strip() for emp_id in manager_emp_ids if str(emp_id).strip()}):
        if emp_id in seen:
            continue
        seen.add(emp_id)
        unique_sorted.append(emp_id)

    mapping: Dict[str, str] = {}
    for index, emp_id in enumerate(unique_sorted, start=1):
        mapping[emp_id] = f"MGR{index:06d}"
    return mapping


async def ensure_manager_login_ids(
    dry_run: bool = True,
    require_confirmation: bool = False,
) -> Dict[str, Any]:
    """Assign deterministic managerLoginId values to MANAGER user_accounts.

    Safety rules:
    - only employee records with Role == 'Manager' are considered
    - existing manager account passwords are never overwritten
    - no employee documents are modified
    - managerLoginId is stored on user_accounts, not employees
    - dry run is default and never writes MongoDB
    - production writes require explicit confirmation
    """
    db = get_database()
    if db is None:
        try:
            from backend.app.database import connect_to_mongo
            await connect_to_mongo()
            db = get_database()
        except Exception:
            return {
                "total_managers_found": 0,
                "manager_ids_already_assigned": 0,
                "manager_ids_missing": 0,
                "mappings_to_create": 0,
                "duplicate_conflicts": 0,
                "records_that_would_be_updated": 0,
                "updated": 0,
                "dry_run": True,
            }
    if db is None:
        return {
            "total_managers_found": 0,
            "manager_ids_already_assigned": 0,
            "manager_ids_missing": 0,
            "mappings_to_create": 0,
            "duplicate_conflicts": 0,
            "records_that_would_be_updated": 0,
            "updated": 0,
            "dry_run": True,
        }

    if not dry_run and not require_confirmation:
        raise RuntimeError(
            "Production manager login ID migration blocked. Pass require_confirmation=True only after confirming the intended database target."
        )

    manager_docs = await db.employees.find(
        {"Role": {"$in": ["Manager", "MANAGER", "manager"]}},
        {"_id": 0, "EmpID": 1},
    ).to_list(length=None)
    manager_emp_ids = [str(doc.get("EmpID") or "").strip() for doc in manager_docs if str(doc.get("EmpID") or "").strip()]
    login_map = build_deterministic_manager_login_map(manager_emp_ids)

    manager_accounts = await db.user_accounts.find(
        {"role": {"$in": ["MANAGER", "Manager", "manager"]}},
        {"_id": 1, "empId": 1, "managerLoginId": 1, "role": 1, "passwordHash": 1, "userId": 1},
    ).to_list(length=None)

    assigned_count = 0
    missing_count = 0
    duplicate_conflicts = 0
    records_to_update = 0
    updated = 0
    seen_login_ids = set()
    assigned_by_emp_id = {}

    for account in manager_accounts:
        emp_id = str(account.get("empId") or "").strip()
        manager_login_id = str(account.get("managerLoginId") or "").strip()
        if emp_id and emp_id in login_map:
            assigned_by_emp_id[emp_id] = manager_login_id
            if manager_login_id:
                if manager_login_id in seen_login_ids:
                    duplicate_conflicts += 1
                else:
                    seen_login_ids.add(manager_login_id)
                assigned_count += 1
                continue
            missing_count += 1

    for emp_id, login_id in login_map.items():
        if emp_id in assigned_by_emp_id and assigned_by_emp_id[emp_id]:
            continue
        if login_id in seen_login_ids:
            duplicate_conflicts += 1
            continue
        seen_login_ids.add(login_id)
        records_to_update += 1

    if dry_run:
        return {
            "total_managers_found": len(manager_emp_ids),
            "manager_ids_already_assigned": assigned_count,
            "manager_ids_missing": records_to_update,
            "mappings_to_create": records_to_update,
            "duplicate_conflicts": duplicate_conflicts,
            "records_that_would_be_updated": records_to_update,
            "updated": 0,
            "dry_run": True,
            "login_map": login_map,
        }

    for account in manager_accounts:
        emp_id = str(account.get("empId") or account.get("userId") or "").strip()
        if not emp_id or emp_id not in login_map:
            continue
        target_login_id = login_map[emp_id]
        current_value = str(account.get("managerLoginId") or "").strip()
        if current_value == target_login_id:
            continue
        if current_value and current_value != target_login_id:
            continue
        await db.user_accounts.update_one(
            {"_id": account["_id"]},
            {"$set": {"managerLoginId": target_login_id, "updatedAt": datetime.now(timezone.utc).isoformat()}},
        )
        updated += 1

    return {
        "total_managers_found": len(manager_emp_ids),
        "manager_ids_already_assigned": assigned_count,
        "manager_ids_missing": max(0, len(manager_emp_ids) - assigned_count),
        "mappings_to_create": records_to_update,
        "duplicate_conflicts": duplicate_conflicts,
        "records_that_would_be_updated": max(0, len(manager_emp_ids) - assigned_count),
        "updated": updated,
        "dry_run": False,
        "login_map": login_map,
    }


async def require_authenticated_user(request: Request) -> Dict[str, Any]:
    return await get_authenticated_user(request)


def require_role(*allowed_roles: str):
    allowed = { _normalize_role(role) for role in allowed_roles if role }

    async def dependency(request: Request):
        user = await get_authenticated_user(request)
        user_role = _normalize_role(user.get("role"))
        if not allowed or user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Insufficient role permissions.",
            )
        return user

    return dependency


async def require_hr_admin(request: Request) -> Dict[str, Any]:
    """Require an HR role. Accepts HR_ADMIN and other HR-prefixed roles (e.g., HR, HR_MANAGER)."""
    auth_user = await get_authenticated_user(request)
    role = _normalize_role(auth_user.get("role"))
    # Allow any role that begins with 'HR' to be considered HR administrative for approval flows.
    if not role.startswith("HR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. HR role required.",
        )
    return auth_user


async def get_manager_team_emp_ids(auth_user: Dict[str, Any]) -> Optional[list[str]]:
    role = _normalize_role(auth_user.get("role"))
    if role.startswith("HR"):
        return None

    emp_id = str(auth_user.get("empId") or "").strip()
    if not emp_id:
        return []

    if role in {"EMPLOYEE", "MANAGER"}:
        team_ids = {emp_id}
        if role == "MANAGER":
            db = get_database()
            if db is not None:
                cursor = db.employees.find(
                    {"$or": [{"managerEmpId": emp_id}, {"managerId": emp_id}, {"ManagerID": emp_id}]},
                    {"_id": 0, "EmpID": 1}
                )
                team_docs = await cursor.to_list(length=5000)
                for doc in team_docs:
                    member_emp_id = str(doc.get("EmpID") or "").strip()
                    if member_emp_id:
                        team_ids.add(member_emp_id)
        return sorted(team_ids)

    return []


async def require_employee_self_or_hr(
    request: Request,
    emp_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    auth_user = await get_authenticated_user(request)
    role = _normalize_role(auth_user.get("role"))
    if role.startswith("HR"):
        return auth_user

    auth_emp_id = str(auth_user.get("empId") or "").strip()
    if role == "MANAGER":
        team_ids = set(await get_manager_team_emp_ids(auth_user) or [])
        if not auth_emp_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager profile could not be loaded.")
        requested_ids = [emp_id, employee_id, user_id, email]
        for value in requested_ids:
            if value is None or not str(value).strip():
                continue
            normalized = str(value).strip()
            if normalized == auth_emp_id:
                continue
            if normalized not in team_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to access this employee record.")
        return auth_user

    if role != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Employee permissions required.",
        )

    identity_values = [
        auth_user.get("empId"),
        auth_user.get("email"),
        auth_user.get("sub"),
        auth_user.get("userId"),
    ]
    auth_identity = {
        str(value).strip().lower()
        for value in identity_values
        if value is not None and str(value).strip()
    }

    provided_values = [emp_id, employee_id, user_id, email]
    for value in provided_values:
        if value is None or not str(value).strip():
            continue
        normalized = str(value).strip().lower()
        if normalized not in auth_identity:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this employee record.",
            )

    return auth_user


def _build_token(user_record: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Generate a unique token identifier (jti) for revocation support
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_record.get("empId") or user_record.get("email"),
        "empId": user_record.get("empId"),
        "managerLoginId": user_record.get("managerLoginId"),
        "email": user_record.get("email"),
        "name": user_record.get("name"),
        "role": user_record.get("role"),
        "department": user_record.get("department"),
        "jti": jti,
        "iat": now.timestamp(),
        "exp": exp.timestamp(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def _lookup_account(identifier: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected.",
        )

    lookup = identifier.strip()
    if not lookup:
        return None

    account = await db.user_accounts.find_one({
        "$or": [
            {"empId": lookup},
            {"userId": lookup},
            {"managerLoginId": lookup},
            {"email": {"$regex": f"^{re.escape(lookup)}$", "$options": "i"}},
        ]
    })
    if account:
        return account

    employee = await db.employees.find_one({
        "$or": [
            {"EmpID": lookup},
            {"Email": {"$regex": f"^{re.escape(lookup)}$", "$options": "i"}},
        ]
    }, {"_id": 0})

    if not employee:
        return None

    return await db.user_accounts.find_one({"empId": employee.get("EmpID")})


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: LoginRequest):
    if not settings.AUTH_BOOTSTRAP_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Please set AUTH_BOOTSTRAP_PASSWORD and restart the backend.",
        )

    await ensure_bootstrap_accounts()
    await ensure_manager_accounts()

    account = await _lookup_account(payload.identifier)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Employee ID or password.",
        )

    if account.get("status") not in (None, "ACTIVE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please contact HR.",
        )

    is_valid = bcrypt.checkpw(payload.password.encode("utf-8"), account.get("passwordHash", "").encode("utf-8"))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Employee ID or password.",
        )

    password_status = _normalize_password_status(account)
    user_result = {
        "userId": account.get("userId"),
        "empId": account.get("empId"),
        "managerLoginId": account.get("managerLoginId"),
        "name": account.get("name"),
        "email": account.get("email"),
        "role": account.get("role"),
        "department": account.get("department"),
        # Expose only non-sensitive status metadata about password lifecycle
        "passwordStatus": password_status,
        "mustChangePassword": bool(account.get("mustChangePassword", False)),
    }

    if not user_result.get("empId"):
        employee = await get_database().employees.find_one({"Email": user_result.get("email")}, {"_id": 0})
        if employee:
            user_result["empId"] = employee.get("EmpID")

    token = _build_token(user_result)
    return AuthTokenResponse(token=token, user=AuthenticatedUser(**user_result))


@router.get("/me", response_model=AuthenticatedUser)
async def get_current_user(request: Request):
    payload = await get_authenticated_user(request)
    # Attempt to enrich with account password status metadata from user_accounts
    db = get_database()
    password_status = None
    must_change = False
    if db is not None:
        query = {}
        if payload.get("empId"):
            query = {"empId": payload.get("empId")}
        elif payload.get("email"):
            query = {"email": {"$regex": f"^{payload.get('email')}$", "$options": "i"}}
        else:
            query = {"userId": payload.get("sub")}
        try:
            acct = await db.user_accounts.find_one(query, {"passwordStatus": 1, "mustChangePassword": 1, "passwordHash": 1, "empId": 1})
            if acct:
                password_status = _normalize_password_status(acct)
                must_change = bool(acct.get("mustChangePassword", False))
        except Exception:
            password_status = None
            must_change = False

    user = AuthenticatedUser(
        userId=payload.get("sub"),
        empId=payload.get("empId"),
        managerLoginId=payload.get("managerLoginId"),
        name=payload.get("name"),
        email=payload.get("email"),
        role=payload.get("role"),
        department=payload.get("department"),
        passwordStatus=password_status,
        mustChangePassword=must_change,
    )
    return user


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=1)
    confirmPassword: str = Field(..., min_length=1)


@router.post("/change-password")
async def change_password(request: Request, payload: ChangePasswordRequest):
    """Allow an authenticated user to change their own password.

    - Verifies the current password
    - Validates the new password and confirmation
    - Updates passwordHash and marks passwordStatus as 'custom'
    - Does NOT expose password hashes or plaintext
    """
    auth_user = await require_authenticated_user(request)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication subsystem temporarily unavailable.")

    # Locate the account for this user
    query = {}
    if auth_user.get("empId"):
        query = {"empId": auth_user.get("empId")}
    elif auth_user.get("email"):
        query = {"email": {"$regex": f"^{auth_user.get('email')}$", "$options": "i"}}
    else:
        query = {"userId": auth_user.get("sub")}

    account = await db.user_accounts.find_one(query)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    # Verify current password
    if not bcrypt.checkpw(payload.currentPassword.encode("utf-8"), account.get("passwordHash", "").encode("utf-8")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")

    # Validate new password
    if payload.newPassword != payload.confirmPassword:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password and confirmation do not match.")

    MIN_PASSWORD_LENGTH = 8
    if len(payload.newPassword) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"New password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    # Hash and update
    new_hash = bcrypt.hashpw(payload.newPassword.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now = datetime.now(timezone.utc)
    password_changed_at = now.isoformat()
    try:
        res = await db.user_accounts.update_one(
            {"_id": account.get("_id")},
            {"$set": {"passwordHash": new_hash, "passwordStatus": "custom", "mustChangePassword": False, "passwordChangedAt": password_changed_at, "updatedAt": password_changed_at}},
            upsert=False,
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password. Please try again.")

    if res.matched_count != 1:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password update did not apply. Please try again.")

    return {"message": "Password updated successfully."}


@router.post("/logout")
async def logout(request: Request):
    """
    Revoke the presented token by recording its jti or token_hash in the auth_revoked_tokens collection.
    This endpoint is idempotent: multiple calls with the same token do not create duplicates.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        # No token presented; treat as successful logout (frontend may still clear session)
        return {"message": "Logged out successfully."}

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return {"message": "Logged out successfully."}

    # Compute token hash always
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db = get_database()
    now = datetime.now(timezone.utc)

    # Attempt to decode to extract exp and jti; do not fail logout if token is expired or malformed
    expires_at = None
    jti = None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM], options={"verify_exp": False})
        exp_ts = payload.get("exp")
        if exp_ts:
            expires_at = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)
        jti = payload.get("jti")
    except Exception:
        # If decode fails, set expires_at to now (revocation record will be short-lived).
        expires_at = now

    if db is None:
        # Fail closed: if the revocation DB is unavailable, report failure so client can retry logout.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to record token revocation. Authentication subsystem unavailable."
        )

    # Build upsert filter; if jti available, prefer jti-based identity otherwise fallback to token_hash
    filters = []
    if jti:
        filters.append({"jti": jti})
    filters.append({"token_hash": token_hash})

    revocation_doc = {
        "jti": jti,
        "token_hash": token_hash,
        "revoked_at": now,
        "expires_at": expires_at or now
    }

    # Idempotent upsert: ensure a single document exists for this token (either jti or token_hash)
    try:
        await db.auth_revoked_tokens.update_one(
            {"$or": filters},
            {"$setOnInsert": revocation_doc},
            upsert=True
        )
    except Exception:
        # If DB write fails, surface an error so client can retry logout (optional)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to record token revocation. Please try again."
        )

    return {"message": "Logged out successfully."}
