import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import AttendanceService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL ATTENDANCE")
    print("====================================")

    records, total = await AttendanceService.get_all(
        size=2
    )

    print(
        "TOTAL ATTENDANCE RECORDS:",
        total
    )

    for record in records:
        print(
            record.get("empId"),
            "-",
            record.get("date"),
            "-",
            record.get("checkIn"),
            "-",
            record.get("checkOut"),
            "-",
            record.get("workingHours"),
            "-",
            record.get("status")
        )

    print("\n====================================")
    print("TEST 2: GET ATTENDANCE ANOMALIES")
    print("====================================")

    anomalies = await AttendanceService.get_anomalies()

    print(
        "TOTAL ANOMALIES:",
        len(anomalies)
    )

    for anomaly in anomalies[:5]:
        print(
            anomaly.get("empId"),
            "-",
            anomaly.get("date"),
            "-",
            anomaly.get("status"),
            "-",
            anomaly.get("isAnomaly")
        )


if __name__ == "__main__":
    asyncio.run(main())