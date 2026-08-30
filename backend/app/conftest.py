import asyncio
import os
from pathlib import Path

import bcrypt
import pytest
from pymongo import MongoClient


TEST_DB_NAME = os.environ.get('DATABASE_NAME', 'workforce_db_test')
TEST_MONGO_URL = os.environ.get('MONGODB_URL', 'mongodb://127.0.0.1:27017')


@pytest.fixture(autouse=True)
def reset_test_auth_state():
    """Keep the test database in a known-good bootstrap state for each test."""
    if not TEST_DB_NAME.endswith('_test'):
        yield
        return

    client = MongoClient(TEST_MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client[TEST_DB_NAME]

    db.auth_revoked_tokens.delete_many({})
    db.user_accounts.delete_many({})
    db.employees.delete_many({})
    db.leaves.delete_many({})
    db.shifts.delete_many({})
    db.notifications.delete_many({})

    hr_pw = os.environ.get('HR_ADMIN_TEST_PASSWORD', 'hr-bootstrap-test-password')
    emp_pw = os.environ.get('EMPLOYEE_TEST_PASSWORD', 'EMP000001')
    manager_one_pw = os.environ.get('MANAGER_ONE_TEST_PASSWORD', 'ManagerOne123')
    manager_two_pw = os.environ.get('MANAGER_TWO_TEST_PASSWORD', 'ManagerTwo123')
    now = __import__('datetime').datetime.utcnow().isoformat()

    employee_docs = [
        {
            'EmpID': 'EMP000001',
            'EmployeeName': 'Aarav A. Sharma',
            'Email': 'aarav.sharma.1@company.com',
            'Department': 'Engineering',
            'JobRole': 'Software Engineer',
            'Location': 'Bengaluru',
            'EmploymentStatus': 'Active',
            'Role': 'Employee',
            'ManagerID': 'EMP010010',
        },
        {
            'EmpID': 'EMP010011',
            'EmployeeName': 'Ritika Nair',
            'Email': 'ritika.nair.11@company.com',
            'Department': 'Engineering',
            'JobRole': 'Frontend Engineer',
            'Location': 'Bengaluru',
            'EmploymentStatus': 'Active',
            'Role': 'Employee',
            'ManagerID': 'EMP010010',
        },
        {
            'EmpID': 'EMP010012',
            'EmployeeName': 'Manoj Verma',
            'Email': 'manoj.verma.12@company.com',
            'Department': 'Engineering',
            'JobRole': 'QA Engineer',
            'Location': 'Pune',
            'EmploymentStatus': 'Active',
            'Role': 'Employee',
            'ManagerID': 'EMP010010',
        },
        {
            'EmpID': 'EMP010021',
            'EmployeeName': 'Naina Shah',
            'Email': 'naina.shah.21@company.com',
            'Department': 'Support',
            'JobRole': 'Support Analyst',
            'Location': 'Hyderabad',
            'EmploymentStatus': 'Active',
            'Role': 'Employee',
            'ManagerID': 'EMP010020',
        },
        {
            'EmpID': 'EMP010022',
            'EmployeeName': 'Dev Patel',
            'Email': 'dev.patel.22@company.com',
            'Department': 'Support',
            'JobRole': 'Support Lead',
            'Location': 'Delhi',
            'EmploymentStatus': 'Active',
            'Role': 'Employee',
            'ManagerID': 'EMP010020',
        },
        {
            'EmpID': 'EMP010010',
            'EmployeeName': 'Sonia Mehta',
            'Email': 'sonia.mehta.10@company.com',
            'Department': 'Engineering',
            'JobRole': 'Engineering Manager',
            'Location': 'Bengaluru',
            'EmploymentStatus': 'Active',
            'Role': 'Manager',
            'ManagerID': 'EMP000001',
        },
        {
            'EmpID': 'EMP010020',
            'EmployeeName': 'Harsh Gupta',
            'Email': 'harsh.gupta.20@company.com',
            'Department': 'Support',
            'JobRole': 'Support Manager',
            'Location': 'Hyderabad',
            'EmploymentStatus': 'Active',
            'Role': 'Manager',
            'ManagerID': 'EMP000001',
        },
        {
            'EmpID': 'EMP010030',
            'EmployeeName': 'Unassigned User',
            'Email': 'unassigned.user.30@company.com',
            'Department': 'Operations',
            'JobRole': 'Operations Analyst',
            'Location': 'Noida',
            'EmploymentStatus': 'Active',
            'Role': 'Employee',
            'ManagerID': None,
        },
    ]
    db.employees.insert_many(employee_docs)

    db.user_accounts.insert_many([
        {
            'userId': 'hr-admin',
            'empId': None,
            'name': 'Priya Sharma',
            'email': 'priya.sharma@enterprise.com',
            'role': 'HR_ADMIN',
            'passwordHash': bcrypt.hashpw(hr_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'passwordStatus': 'custom',
            'mustChangePassword': False,
            'passwordChangedAt': None,
            'status': 'ACTIVE',
            'createdAt': now,
            'updatedAt': now,
        },
        {
            'userId': 'employee-self-service',
            'empId': 'EMP000001',
            'name': 'Aarav A. Sharma',
            'email': 'aarav.sharma.1@company.com',
            'role': 'EMPLOYEE',
            'passwordHash': bcrypt.hashpw(emp_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'passwordStatus': 'custom',
            'mustChangePassword': False,
            'passwordChangedAt': None,
            'status': 'ACTIVE',
            'createdAt': now,
            'updatedAt': now,
        },
        {
            'userId': 'EMP010010',
            'empId': 'EMP010010',
            'managerLoginId': 'MGR000001',
            'name': 'Sonia Mehta',
            'email': 'sonia.mehta.10@company.com',
            'role': 'MANAGER',
            'passwordHash': bcrypt.hashpw(manager_one_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'passwordStatus': 'custom',
            'mustChangePassword': False,
            'passwordChangedAt': None,
            'status': 'ACTIVE',
            'createdAt': now,
            'updatedAt': now,
        },
        {
            'userId': 'EMP010020',
            'empId': 'EMP010020',
            'managerLoginId': 'MGR000002',
            'name': 'Harsh Gupta',
            'email': 'harsh.gupta.20@company.com',
            'role': 'MANAGER',
            'passwordHash': bcrypt.hashpw(manager_two_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'passwordStatus': 'custom',
            'mustChangePassword': False,
            'passwordChangedAt': None,
            'status': 'ACTIVE',
            'createdAt': now,
            'updatedAt': now,
        },
    ])
    client.close()
    yield
    client = MongoClient(TEST_MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client[TEST_DB_NAME]
    db.auth_revoked_tokens.delete_many({})
    db.user_accounts.delete_many({})
    db.employees.delete_many({})
    db.leaves.delete_many({})
    db.shifts.delete_many({})
    db.notifications.delete_many({})
    client.close()
