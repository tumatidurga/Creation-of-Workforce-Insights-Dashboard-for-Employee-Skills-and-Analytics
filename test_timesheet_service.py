import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import TimesheetService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL TIMESHEET RECORDS")
    print("====================================")

    timesheets = await TimesheetService.get_all()

    print(
        "TOTAL TIMESHEET RECORDS:",
        len(timesheets)
    )

    for timesheet in timesheets[:5]:

        print(
            timesheet.get("empId"),
            "-",
            timesheet.get("date"),
            "-",
            timesheet.get("projectName"),
            "-",
            timesheet.get("hoursLogged"),
            "-",
            timesheet.get("clientBillingHours"),
            "-",
            timesheet.get("status")
        )

    print("\n====================================")
    print("TEST 2: FILTER BY EMPLOYEE")
    print("====================================")

    employee_timesheets = await TimesheetService.get_all(
        emp_id="EMP000001"
    )

    print(
        "EMP000001 TIMESHEET RECORDS:",
        len(employee_timesheets)
    )

    for timesheet in employee_timesheets[:5]:

        print(
            timesheet.get("empId"),
            "-",
            timesheet.get("date"),
            "-",
            timesheet.get("projectName"),
            "-",
            timesheet.get("hoursLogged"),
            "-",
            timesheet.get("status")
        )


if __name__ == "__main__":
    asyncio.run(main())