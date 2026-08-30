import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import PerformanceService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL PERFORMANCE RECORDS")
    print("====================================")

    records = await PerformanceService.get_all()

    print(
        "TOTAL PERFORMANCE RECORDS:",
        len(records)
    )

    for record in records[:5]:

        print(
            record.get("empId"),
            "-",
            "Performance:",
            record.get("performanceScore"),
            "-",
            "KPI:",
            record.get("kpiCompletionRate"),
            "-",
            "Productivity:",
            record.get("productivityScore"),
            "-",
            "Rating:",
            record.get("performanceRating"),
            "-",
            "Review:",
            record.get("reviewDate")
        )

    print("\n====================================")
    print("TEST 2: GET PERFORMANCE BY EMPLOYEE")
    print("====================================")

    employee_id = "EMP000001"

    record = await PerformanceService.get_by_emp_id(
        employee_id
    )

    if record:

        print("Performance record found:")

        print(
            "Employee:",
            record.get("empId")
        )

        print(
            "Performance Score:",
            record.get("performanceScore")
        )

        print(
            "KPI Completion:",
            record.get("kpiCompletionRate")
        )

        print(
            "Productivity Score:",
            record.get("productivityScore")
        )

        print(
            "Performance Rating:",
            record.get("performanceRating")
        )

        print(
            "Review Date:",
            record.get("reviewDate")
        )

        print(
            "Promotion Recommended:",
            record.get("promotionRecommended")
        )

    else:

        print(
            "No performance record found for",
            employee_id
        )


if __name__ == "__main__":
    asyncio.run(main())