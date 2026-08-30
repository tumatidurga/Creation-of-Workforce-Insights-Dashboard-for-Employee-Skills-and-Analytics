import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import PayrollService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL PAYROLL RECORDS")
    print("====================================")

    payroll = await PayrollService.get_all()

    print(
        "TOTAL PAYROLL RECORDS:",
        len(payroll)
    )

    for record in payroll[:5]:

        print(
            record.get("empId"),
            "-",
            record.get("month"),
            "-",
            record.get("baseSalary"),
            "-",
            record.get("overtimePay"),
            "-",
            record.get("performanceBonus"),
            "-",
            record.get("taxDeductions"),
            "-",
            record.get("netPay")
        )

    print("\n====================================")
    print("TEST 2: FILTER BY PAYROLL MONTH")
    print("====================================")

    month = payroll[0].get("month") if payroll else None

    if month:

        filtered = await PayrollService.get_all(
            month=month
        )

        print(
            "MONTH:",
            month
        )

        print(
            "RECORDS FOR MONTH:",
            len(filtered)
        )

        for record in filtered[:5]:

            print(
                record.get("empId"),
                "-",
                record.get("month"),
                "-",
                record.get("baseSalary"),
                "-",
                record.get("netPay")
            )

    else:

        print("No payroll records found.")


if __name__ == "__main__":
    asyncio.run(main())