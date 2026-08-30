import asyncio
from backend.app.database import connect_to_mongo, get_database

async def main():
    await connect_to_mongo()
    db = get_database()
    account = await db.user_accounts.find_one({'managerLoginId':'MGR000001'}, {'_id':0})
    account_user_id = account.get('userId')
    profile_doc = await db.user_profiles.find_one({'userId': account_user_id}, {'_id':0})
    emp_doc = await db.employees.find_one({'EmpID': account.get('empId')})
    synthesized = {}
    if profile_doc:
        synthesized = dict(profile_doc)
        synthesized['userId'] = account_user_id
        synthesized['empId'] = account.get('empId')
        synthesized['role'] = account.get('role')
        synthesized['name'] = synthesized.get('name') or account.get('name') or (emp_doc.get('EmployeeName') if emp_doc else None)
        synthesized['email'] = synthesized.get('email') or account.get('email') or (emp_doc.get('Email') if emp_doc else None)
    else:
        synthesized = {
            'userId': account_user_id,
            'empId': account.get('empId'),
            'name': emp_doc.get('EmployeeName') if emp_doc else account.get('name'),
            'email': account.get('email'),
            'role': account.get('role')
        }
    # Remove sensitive fields
    synthesized.pop('passwordHash', None)
    synthesized.pop('password', None)
    print('PROFILE:', synthesized)

if __name__ == '__main__':
    asyncio.run(main())
