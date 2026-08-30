import asyncio
from backend.app.database import connect_to_mongo, get_database
from backend.app.routers.auth import get_manager_team_emp_ids

async def main():
    await connect_to_mongo()
    db = get_database()
    mgr = await db.user_accounts.find_one({'managerLoginId':'MGR000001'}, {'_id':0})
    team = await get_manager_team_emp_ids(mgr)
    cursor = db.employees.find({}, {'_id':0,'EmpID':1}).limit(200)
    not_in_team = None
    async for e in cursor:
        eid = e.get('EmpID')
        if eid and (eid not in (team or [])):
            not_in_team = eid
            break
    print('SAMPLE_NOT_IN_TEAM:', not_in_team)

if __name__ == '__main__':
    asyncio.run(main())
