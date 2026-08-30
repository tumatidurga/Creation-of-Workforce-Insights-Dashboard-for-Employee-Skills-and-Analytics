from fastapi import APIRouter, HTTPException, Request, status

from backend.app.models.additional_schemas import UserProfile
from backend.app.database import get_database
from backend.app.routers.auth import get_authenticated_user, require_authenticated_user


router = APIRouter(
    prefix="/profile",
    tags=["User Profile"]
)


@router.get("", response_model=UserProfile)
async def get_user_profile(request: Request):
    """Return the authenticated user's profile (per-user) and enrich from employees when available.

    Rules:
    - Determine the authenticated account (user_accounts) from JWT payload.
    - Lookup user_profiles by user_accounts.userId.
    - If profile exists, return it (enriched by employee data if empId available).
    - If not, safely synthesize from user_accounts and employees (do not query CURRENT_USER).
    """

    payload = await require_authenticated_user(request)
    db = get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected."
        )

    # Locate the account record to obtain a stable userId
    account_query = {}
    if payload.get("empId"):
        account_query = {"empId": payload.get("empId")}
    elif payload.get("email"):
        account_query = {"email": {"$regex": f"^{payload.get('email')}$", "$options": "i"}}
    else:
        account_query = {"userId": payload.get("sub")}

    account = await db.user_accounts.find_one(account_query, {"_id": 0})
    account_user_id = (account.get("userId") if account else (payload.get("sub") or None))

    # Attempt to return an explicit per-user profile
    profile_doc = None
    if account_user_id:
        profile_doc = await db.user_profiles.find_one({"userId": account_user_id}, {"_id": 0})

    # Helper: enrich from employee doc if available
    emp_doc = None
    emp_id = payload.get("empId") or (account.get("empId") if account else None)
    if emp_id:
        emp_doc = await db.employees.find_one({"EmpID": emp_id})

    # If explicit profile exists, overlay guaranteed fields and prefer a valid local avatarId.
    if profile_doc:
        profile_doc = dict(profile_doc)  # copy
        profile_doc["userId"] = account_user_id
        profile_doc["empId"] = emp_id
        profile_doc["role"] = payload.get("role") or (account.get("role") if account else profile_doc.get("role"))
        profile_doc["name"] = profile_doc.get("name") or payload.get("name") or (emp_doc.get("EmployeeName") if emp_doc else None)
        profile_doc["email"] = profile_doc.get("email") or payload.get("email") or (emp_doc.get("Email") if emp_doc else None)
        profile_doc["phone"] = profile_doc.get("phone") or profile_doc.get("Phone") or None
        profile_doc["personalEmail"] = profile_doc.get("personalEmail") or profile_doc.get("personal_email") or None
        profile_doc["jobRole"] = profile_doc.get("jobRole") or profile_doc.get("JobRole") or (emp_doc.get("JobRole") if emp_doc else None)
        profile_doc["department"] = profile_doc.get("department") or profile_doc.get("Department") or (emp_doc.get("Department") if emp_doc else None)

        avatar_id = profile_doc.get("avatarId") or profile_doc.get("avatar")
        if isinstance(avatar_id, str):
            normalized_avatar = avatar_id.strip().lower()
            if normalized_avatar in {"avatar-01", "avatar-02", "avatar-03", "avatar-04", "avatar-05", "avatar-06", "avatar-07", "avatar-08"}:
                profile_doc["avatarId"] = normalized_avatar
                profile_doc["avatar"] = None
            else:
                profile_doc["avatarId"] = None
                profile_doc["avatar"] = None
        else:
            profile_doc["avatarId"] = None
            profile_doc["avatar"] = None

        profile_doc.setdefault("mfaEnabled", True)
        profile_doc.setdefault("lastLogin", None)
        profile_doc.setdefault("phone", None)
        profile_doc.setdefault("personalEmail", None)
        profile_doc.setdefault("dateOfBirth", None)
        profile_doc.setdefault("gender", None)
        profile_doc.setdefault("address", None)
        profile_doc.setdefault("city", None)
        profile_doc.setdefault("state", None)
        profile_doc.setdefault("country", None)
        profile_doc.setdefault("postalCode", None)
        profile_doc.setdefault("emergencyContactName", None)
        profile_doc.setdefault("emergencyContactRelationship", None)
        profile_doc.setdefault("emergencyContactPhone", None)
        profile_doc.setdefault("skills", None)
        profile_doc.setdefault("education", None)
        profile_doc.setdefault("qualifications", None)
        return UserProfile(**profile_doc)

    # No per-user profile found: synthesize safely from account and employee.
    # The app uses local avatar IDs rather than external URLs.
    synthesized = {
        "userId": account_user_id or payload.get("sub"),
        "empId": emp_id,
        "name": None,
        "email": payload.get("email") or (account.get("email") if account else None),
        "phone": None,
        "personalEmail": None,
        "role": payload.get("role") or (account.get("role") if account else None),
        "department": None,
        "jobRole": None,
        "dateOfBirth": None,
        "gender": None,
        "address": None,
        "city": None,
        "state": None,
        "country": None,
        "postalCode": None,
        "emergencyContactName": None,
        "emergencyContactRelationship": None,
        "emergencyContactPhone": None,
        "skills": None,
        "education": None,
        "qualifications": None,
        "avatarId": None,
        "avatar": None,
        "mfaEnabled": True,
        "lastLogin": None,
    }

    if emp_doc:
        synthesized["name"] = emp_doc.get("EmployeeName") or payload.get("name")
        synthesized["email"] = synthesized.get("email") or emp_doc.get("Email")
        synthesized["department"] = emp_doc.get("Department")
        synthesized["jobRole"] = emp_doc.get("JobRole")
        synthesized["phone"] = emp_doc.get("Phone") or None
    else:
        synthesized["name"] = (account.get("name") if account else payload.get("name"))

    return UserProfile(**synthesized)


@router.put("", response_model=UserProfile)
async def update_user_profile(request: Request, profile: UserProfile):
    """Update the authenticated user's profile only. Do not allow changing account-owned or workforce-owned fields.

    Rules:
    - Determine authenticated account and userId from JWT payload + user_accounts lookup.
    - Only accept profile updates for the authenticated user's userId.
    - Allowed updatable fields belong to user_profiles: name, avatar, department (presentation), mfaEnabled, lastLogin (if used), etc.
    - Forbidden: userId, empId, role, passwordHash, status.
    - Create the profile document if missing (upsert) for the authenticated user.
    """

    payload = await require_authenticated_user(request)
    db = get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB database is not connected."
        )

    # Resolve account to find stable userId
    account_query = {}
    if payload.get("empId"):
        account_query = {"empId": payload.get("empId")}
    elif payload.get("email"):
        account_query = {"email": {"$regex": f"^{payload.get('email')}$", "$options": "i"}}
    else:
        account_query = {"userId": payload.get("sub")}

    account = await db.user_accounts.find_one(account_query, {"_id": 0})
    account_user_id = (account.get("userId") if account else (payload.get("sub") or None))

    if not account_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to determine account userId for profile update.")

    # Build profile document to save, excluding forbidden fields.
    # Only genuinely profile-owned presentation fields are accepted here; account and
    # workforce metadata are resolved server-side from the authenticated account.
    incoming = profile.model_dump(exclude_none=True)
    forbidden = {
        "userId",
        "empId",
        "role",
        "email",
        "department",
        "jobRole",
        "status",
        "passwordHash",
        "passwordStatus",
        "mustChangePassword",
    }
    save_doc = {k: v for k, v in incoming.items() if k not in forbidden and k != "avatar"}

    if isinstance(save_doc.get("skills"), list):
        save_doc["skills"] = [str(item).strip() for item in save_doc["skills"] if str(item).strip()]
        save_doc["skills"] = list(dict.fromkeys(save_doc["skills"]))

    avatar_id = incoming.get("avatarId")
    if avatar_id is not None:
        normalized = str(avatar_id).strip().lower()
        if normalized not in {"avatar-01", "avatar-02", "avatar-03", "avatar-04", "avatar-05", "avatar-06", "avatar-07", "avatar-08"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid avatar selection.")
        save_doc["avatarId"] = normalized
        save_doc["avatar"] = None
    else:
        save_doc["avatarId"] = None
        save_doc["avatar"] = None

    # Ensure user-controlled contact details remain separate from company-managed work records.
    if "personalEmail" in save_doc and isinstance(save_doc["personalEmail"], str):
        save_doc["personalEmail"] = save_doc["personalEmail"].strip() or None
    if "phone" in save_doc and isinstance(save_doc["phone"], str):
        save_doc["phone"] = save_doc["phone"].strip() or None
    if "emergencyContactPhone" in save_doc and isinstance(save_doc["emergencyContactPhone"], str):
        save_doc["emergencyContactPhone"] = save_doc["emergencyContactPhone"].strip() or None
    if "postalCode" in save_doc and isinstance(save_doc["postalCode"], str):
        save_doc["postalCode"] = save_doc["postalCode"].strip() or None

    # Enforce authoritative fields.
    save_doc["userId"] = account_user_id
    if account and account.get("empId"):
        save_doc["empId"] = account.get("empId")

    # Upsert the profile for the authenticated user
    await db.user_profiles.update_one({"userId": account_user_id}, {"$set": save_doc}, upsert=True)

    # Return the merged profile as saved (and enriched from employee if applicable)
    # Reuse GET logic: call get_user_profile to return canonical shape
    return await get_user_profile(request)