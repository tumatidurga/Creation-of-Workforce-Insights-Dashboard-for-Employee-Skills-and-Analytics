import asyncio

from backend.app.database import connect_to_mongo, get_database
from backend.app.services.workforce_services import LeaveService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    db = get_database()

    print("\n====================================")
    print("TEST 1: GET ALL LEAVE RECORDS")
    print("====================================")

    leaves = await LeaveService.get_all()

    print(
        "SERVICE RETURNED:",
        len(leaves)
    )

    for leave in leaves[:5]:
        print(
            leave.get("empId"),
            "-",
            leave.get("leaveType"),
            "-",
            leave.get("startDate"),
            "-",
            leave.get("endDate"),
            "-",
            leave.get("status"),
            "- Days:",
            leave.get("days")
        )

    print("\n====================================")
    print("TEST 2: FILTER APPROVED LEAVES")
    print("====================================")

    approved = await LeaveService.get_all(
        status="Approved"
    )

    print(
        "SERVICE RETURNED APPROVED:",
        len(approved)
    )

    for leave in approved[:10]:
        print(
            leave.get("empId"),
            "-",
            leave.get("leaveType"),
            "-",
            leave.get("status")
        )

    print("\n====================================")
    print("TEST 3: VERIFY NO WRONG STATUS")
    print("====================================")

    wrong_status = [
        leave
        for leave in approved
        if str(leave.get("status")).lower()
        != "approved"
    ]

    print(
        "WRONG STATUS RECORDS:",
        len(wrong_status)
    )

    if wrong_status:
        print("\nFIRST WRONG RECORD:")
        print(wrong_status[0])
    else:
        print(
            "SUCCESS: All returned records are Approved."
        )


if __name__ == "__main__":
    asyncio.run(main())