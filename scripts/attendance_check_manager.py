import asyncio
from backend.app.database import connect_to_mongo, get_database
from backend.app.services.workforce_services import AttendanceService

async def main():
    await connect_to_mongo()
    db = get_database()
    mgr = await db.user_accounts.find_one({'managerLoginId':'MGR000001'}, {'_id':0})
    emp_id = mgr.get('empId')
    items, total = await AttendanceService.get_all(page=1,size=50, employee_emp_id=emp_id)
    print('ATT_COUNT:', len(items), 'TOTAL:', total)
    leak = False
    for it in items:
        if str(it.get('empId') or it.get('EmpID') or '').strip() != emp_id:
            leak = True
            print('LEAK_RECORD:', it)
            break
    print('LEAK_DETECTED:', leak)

if __name__ == '__main__':
    asyncio.run(main())
