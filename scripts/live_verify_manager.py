import asyncio
from backend.app.database import connect_to_mongo, get_database
from backend.app.routers.auth import get_manager_team_emp_ids
from backend.app.services.workforce_services import EmployeeService, AttendanceService, LeaveService, ShiftService, TimesheetService, PayrollService

async def run():
    await connect_to_mongo()
    db = get_database()
    manager_login = 'MGR000001'
    account = await db.user_accounts.find_one({'managerLoginId': manager_login}, {'_id':0,'passwordHash':0})
    if not account:
        print('Manager account not found')
        return
    auth_user = account
    print('AUTH_USER:', {'userId':auth_user.get('userId'),'empId':auth_user.get('empId'),'role':auth_user.get('role')})

    # compute team ids
    team_ids = await get_manager_team_emp_ids(auth_user)
    print('TEAM_IDS_COUNT:', len(team_ids) if team_ids else 0)

    results = {}

    # Employees
    items, total = await EmployeeService.get_all(page=1,size=50, emp_ids=team_ids)
    results['employees'] = {'count': len(items), 'total': total}

    # Attendance
    attendance_items, attendance_total = await AttendanceService.get_all(page=1,size=50, employee_emp_ids=team_ids)
    results['attendance'] = {'count': len(attendance_items), 'total': attendance_total}

    # Leaves
    leaves = await LeaveService.get_all(page=1,size=50, emp_ids=team_ids)
    results['leaves'] = {'count': len(leaves)}

    # Shifts
    shifts = await ShiftService.get_all(page=1,size=50, emp_ids=team_ids)
    results['shifts'] = {'count': len(shifts)}

    # Timesheets
    timesheets = await TimesheetService.get_all(page=1,size=50, emp_ids=team_ids)
    results['timesheets'] = {'count': len(timesheets)}

    # Payroll - get payroll records for team
    payroll_records = await PayrollService.get_all(page=1,size=50)
    # filter by team ids to ensure payrolls belong to team when HR or manager
    payroll_team = [p for p in payroll_records if str(p.get('empId') or p.get('EmpID') or '') in set(team_ids)]
    results['payroll'] = {'fetched': len(payroll_records), 'belong_to_team': len(payroll_team)}

    print('RESULTS:')
    for k,v in results.items():
        print(k, v)

if __name__ == '__main__':
    asyncio.run(run())
