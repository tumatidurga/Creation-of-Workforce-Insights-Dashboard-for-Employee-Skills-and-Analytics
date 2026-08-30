import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import EmployeeService


async def main():

    await connect_to_mongo()

    print("====================================")
    print("TEST 1: GET ALL EMPLOYEES")
    print("====================================")

    employees, total = await EmployeeService.get_all(
        size=2
    )

    print("Total:", total)

    for employee in employees:
        print(
            employee.get("empId"),
            "-",
            employee.get("firstName"),
            employee.get("lastName"),
            "-",
            employee.get("department"),
            "-",
            employee.get("status")
        )

    print("\n====================================")
    print("TEST 2: GET EMPLOYEE BY ID")
    print("====================================")

    employee = await EmployeeService.get_by_id(
        "EMP000001"
    )

    if employee:
        print("Employee found:")
        print("ID:", employee.get("empId"))
        print(
            "Name:",
            employee.get("firstName"),
            employee.get("lastName")
        )
        print("Email:", employee.get("email"))
        print("Department:", employee.get("department"))
        print("Job Role:", employee.get("jobRole"))
        print("Salary:", employee.get("monthlyIncome"))
        print("Status:", employee.get("status"))
    else:
        print("Employee NOT FOUND")


if __name__ == "__main__":
    asyncio.run(main())