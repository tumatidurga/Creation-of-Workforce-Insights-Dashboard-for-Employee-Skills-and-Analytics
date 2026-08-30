import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import ShiftService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL SHIFT RECORDS")
    print("====================================")

    shifts = await ShiftService.get_all()

    print("TOTAL SHIFT RECORDS:", len(shifts))

    for shift in shifts[:5]:

        print(
            shift.get("empId"),
            "-",
            shift.get("shiftName"),
            "-",
            shift.get("shiftStart"),
            "-",
            shift.get("shiftEnd"),
            "-",
            shift.get("overtimeHours"),
            "-",
            shift.get("status")
        )

    print("\n====================================")
    print("TEST 2: APPROVED SHIFTS")
    print("====================================")

    approved = await ShiftService.get_all(
        status="Approved"
    )

    print(
        "TOTAL APPROVED SHIFTS:",
        len(approved)
    )

    for shift in approved[:5]:

        print(
            shift.get("empId"),
            "-",
            shift.get("shiftName"),
            "-",
            shift.get("status")
        )

    print("\n====================================")
    print("TEST 3: PENDING SHIFTS")
    print("====================================")

    pending = await ShiftService.get_all(
        status="Pending"
    )

    print(
        "TOTAL PENDING SHIFTS:",
        len(pending)
    )

    for shift in pending[:5]:

        print(
            shift.get("empId"),
            "-",
            shift.get("shiftName"),
            "-",
            shift.get("status")
        )


if __name__ == "__main__":
    asyncio.run(main())