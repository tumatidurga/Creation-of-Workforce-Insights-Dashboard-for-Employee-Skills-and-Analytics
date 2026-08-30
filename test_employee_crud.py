import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import EmployeeService
from backend.app.models.schemas import EmployeeCreate, EmployeeUpdate


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: CHECK EXISTING EMPLOYEE")
    print("====================================")

    employee = await EmployeeService.get_by_id(
        "EMP000001"
    )

    if employee:
        print("Employee exists:")
        print(
            employee["empId"],
            "-",
            employee["firstName"],
            employee["lastName"]
        )
    else:
        print("Employee not found.")

    print("\n====================================")
    print("TEST 2: CREATE EMPLOYEE")
    print("====================================")

    test_employee_id = "TEST000001"

    existing = await EmployeeService.get_by_id(
        test_employee_id
    )

    if existing:
        print(
            "Test employee already exists. "
            "Skipping creation."
        )
    else:

        employee_data = EmployeeCreate(
            empId=test_employee_id,
            firstName="Test",
            lastName="Employee",
            email="test.employee@company.com",
            phone="9999999999",
            gender="Male",
            age=25,
            department="IT",
            jobRole="Software Engineer",
            designation="Software Engineer",
            jobLevel=1,
            managerId="EMP000001",
            managerName="Aarav A. Sharma",
            location="Kolkata",
            status="Active",
            monthlyIncome=35000,
            yearsAtCompany=0,
            yearsInRole=0,
            yearsWithManager=0,
            workLifeBalanceScore=4,
            jobSatisfactionScore=4,
            environmentSatisfactionScore=4,
            relationshipSatisfactionScore=4,
            skills=[],
            education="Bachelor's Degree",
            educationField="Computer Science",
            emergencyContact={
                "name": "Test Contact",
                "relationship": "Parent",
                "phone": "8888888888"
            },
            address="Kolkata"
        )

        created = await EmployeeService.create(
            employee_data
        )

        print("Employee created:")
        print(
            created["empId"],
            "-",
            created["firstName"],
            created["lastName"],
            "-",
            created["department"]
        )

    print("\n====================================")
    print("TEST 3: GET CREATED EMPLOYEE")
    print("====================================")

    created_employee = await EmployeeService.get_by_id(
        test_employee_id
    )

    if created_employee:

        print("Created employee found:")
        print(
            "ID:",
            created_employee["empId"]
        )

        print(
            "Name:",
            created_employee["firstName"],
            created_employee["lastName"]
        )

        print(
            "Department:",
            created_employee["department"]
        )

        print(
            "Job Role:",
            created_employee["jobRole"]
        )

        print(
            "Salary:",
            created_employee["monthlyIncome"]
        )

        print(
            "Status:",
            created_employee["status"]
        )

    else:
        print(
            "ERROR: Created employee "
            "could not be retrieved."
        )

    print("\n====================================")
    print("TEST 4: UPDATE CREATED EMPLOYEE")
    print("====================================")

    update_data = EmployeeUpdate(
        department="Engineering",
        jobRole="Backend Developer",
        monthlyIncome=40000
    )

    updated = await EmployeeService.update(
        test_employee_id,
        update_data
    )

    if updated:

        print("Employee updated:")
        print(
            "Department:",
            updated["department"]
        )

        print(
            "Job Role:",
            updated["jobRole"]
        )

        print(
            "Salary:",
            updated["monthlyIncome"]
        )

    else:
        print(
            "ERROR: Employee update failed."
        )

    print("\n====================================")
    print("TEST 5: DELETE TEST EMPLOYEE")
    print("====================================")

    deleted = await EmployeeService.delete(
        test_employee_id
    )

    print(
        "Delete successful:",
        deleted
    )

    print("\n====================================")
    print("TEST 6: VERIFY DELETION")
    print("====================================")

    deleted_employee = await EmployeeService.get_by_id(
        test_employee_id
    )

    if deleted_employee is None:
        print(
            "SUCCESS: Test employee was deleted."
        )
    else:
        print(
            "ERROR: Test employee still exists."
        )


if __name__ == "__main__":
    asyncio.run(main())