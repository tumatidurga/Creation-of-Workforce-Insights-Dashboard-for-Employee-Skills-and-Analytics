import asyncio

from backend.app.database import connect_to_mongo, get_database
from backend.app.services.workforce_services import AuditService
from backend.app.models.schemas import AuditLogCreate


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    # ==========================================================
    # TEST 1: GET EXISTING AUDIT LOGS
    # ==========================================================

    print("\n====================================")
    print("TEST 1: GET EXISTING AUDIT LOGS")
    print("====================================")

    logs = await AuditService.get_all()

    print("TOTAL AUDIT LOGS:", len(logs))

    for log in logs:
        print(
            log.get("id"),
            "-",
            log.get("actor"),
            "-",
            log.get("action"),
            "-",
            log.get("module"),
            "-",
            log.get("status")
        )

    # ==========================================================
    # TEST 2: CREATE AUDIT LOG
    # ==========================================================

    print("\n====================================")
    print("TEST 2: CREATE AUDIT LOG")
    print("====================================")

    audit_data = AuditLogCreate(
        actor="System",
        action="Test audit entry",
        module="Workforce Management",
        ipAddress="127.0.0.1",
        status="SUCCESS"
    )

    created = await AuditService.create(
        audit_data
    )

    print("AUDIT LOG CREATED:")
    print("ID:", created.get("id"))
    print("Actor:", created.get("actor"))
    print("Action:", created.get("action"))
    print("Module:", created.get("module"))
    print("Timestamp:", created.get("timestamp"))
    print("IP Address:", created.get("ipAddress"))
    print("Status:", created.get("status"))

    # ==========================================================
    # TEST 3: GET AUDIT LOGS AGAIN
    # ==========================================================

    print("\n====================================")
    print("TEST 3: GET AUDIT LOGS AGAIN")
    print("====================================")

    logs = await AuditService.get_all()

    print("TOTAL AUDIT LOGS:", len(logs))

    # ==========================================================
    # Find the ACTUAL latest audit log by timestamp
    # ==========================================================

    latest_log = max(
        logs,
        key=lambda log: log.get(
            "timestamp",
            ""
        )
    )

    print("\nLATEST AUDIT LOG:")

    print(
        "ID:",
        latest_log.get("id")
    )

    print(
        "Actor:",
        latest_log.get("actor")
    )

    print(
        "Action:",
        latest_log.get("action")
    )

    print(
        "Module:",
        latest_log.get("module")
    )

    print(
        "Timestamp:",
        latest_log.get("timestamp")
    )

    print(
        "Status:",
        latest_log.get("status")
    )

    # ==========================================================
    # VERIFY CREATED RECORD IS THE LATEST
    # ==========================================================

    if latest_log.get("id") == created.get("id"):

        print(
            "\nSUCCESS: Newly created audit log "
            "is the latest record."
        )

    else:

        print(
            "\nWARNING: Newly created audit log "
            "is NOT the latest record."
        )


if __name__ == "__main__":
    asyncio.run(main())