#!/usr/bin/env python3
"""Provision missing MANAGER user_accounts from manager employee records.

Read-only safety notes:
- Only employees with Role == 'Manager' are considered.
- Existing user_accounts entries are preserved as-is.
- HR_ADMIN accounts are not touched.
- Employees and MongoDB records are never modified.
- This script is idempotent and can be safely rerun.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings
from backend.app.routers.auth import ensure_manager_accounts


PROVISION_DRY_RUN = os.environ.get("PROVISION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
PRODUCTION_CONFIRMATION = os.environ.get("PROVISION_CONFIRM_PRODUCTION", "").strip().upper()


async def main() -> int:
    print(f"DATABASE_NAME={settings.DATABASE_NAME}")
    print(f"PROVISION_DRY_RUN={'TRUE' if PROVISION_DRY_RUN else 'FALSE'}")

    if not PROVISION_DRY_RUN and PRODUCTION_CONFIRMATION != "YES":
        print("ERROR: Real provisioning is blocked. Set PROVISION_DRY_RUN=true for dry-run, or set PROVISION_CONFIRM_PRODUCTION=YES to confirm production execution.")
        return 2

    result = await ensure_manager_accounts(dry_run=PROVISION_DRY_RUN)
    total_manager_employees = result.get("total_manager_employees", 0)
    created = result.get("created", 0)
    existing = result.get("existing", 0)
    missing_after = result.get("missing", 0)

    print(f"TOTAL_EXISTING_MANAGER_EMPLOYEE_RECORDS={total_manager_employees}")
    print(f"TOTAL_MANAGER_USER_ACCOUNTS_CREATED={created}")
    print(f"TOTAL_MANAGER_USER_ACCOUNTS_ALREADY_EXISTING={existing}")
    print(f"TOTAL_MANAGER_ACCOUNTS_MISSING_AFTER_PROVISIONING={missing_after}")

    if PROVISION_DRY_RUN:
        print("STATUS=DRY_RUN_ONLY")
        return 0

    print("STATUS=SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
