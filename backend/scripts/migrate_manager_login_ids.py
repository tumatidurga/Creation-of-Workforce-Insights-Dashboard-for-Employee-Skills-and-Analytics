#!/usr/bin/env python3
"""Deterministically assign managerLoginId values to manager user_accounts.

Safety:
- Never edits the employees collection or ManagerID hierarchy.
- Stores the login identity on user_accounts only.
- Dry-run by default.
- Requires explicit production confirmation before write operations.
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
from backend.app.routers.auth import ensure_manager_login_ids


PROVISION_DRY_RUN = os.environ.get("MIGRATE_MANAGER_LOGIN_IDS_DRY_RUN", "true").lower() in {"1", "true", "yes"}
PRODUCTION_CONFIRMATION = os.environ.get("MIGRATE_CONFIRM_PRODUCTION", "").strip().upper()


async def main() -> int:
    print(f"DATABASE_NAME={settings.DATABASE_NAME}")
    print(f"PROVISION_DRY_RUN={'TRUE' if PROVISION_DRY_RUN else 'FALSE'}")

    if not PROVISION_DRY_RUN and PRODUCTION_CONFIRMATION != "YES":
        print("ERROR: Real migration is blocked. Set MIGRATE_MANAGER_LOGIN_IDS_DRY_RUN=true for dry-run, or set MIGRATE_CONFIRM_PRODUCTION=YES to confirm production execution.")
        return 2

    result = await ensure_manager_login_ids(
        dry_run=PROVISION_DRY_RUN,
        require_confirmation=PRODUCTION_CONFIRMATION == "YES",
    )

    print(f"TOTAL_MANAGERS_FOUND={result.get('total_managers_found', 0)}")
    print(f"MANAGER_IDS_ALREADY_ASSIGNED={result.get('manager_ids_already_assigned', 0)}")
    print(f"MANAGER_IDS_MISSING={result.get('manager_ids_missing', 0)}")
    print(f"MAPPINGS_TO_CREATE={result.get('mappings_to_create', 0)}")
    print(f"DUPLICATE_CONFLICTS={result.get('duplicate_conflicts', 0)}")
    print(f"RECORDS_THAT_WOULD_BE_UPDATED={result.get('records_that_would_be_updated', 0)}")
    print(f"UPDATED={result.get('updated', 0)}")

    if PROVISION_DRY_RUN:
        print("STATUS=DRY_RUN_ONLY")
        return 0

    print("STATUS=SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
