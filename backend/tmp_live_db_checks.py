import asyncio, json, sys
sys.path.append(r'.')
from backend.app.database import connect_to_mongo, close_mongo_connection, get_database

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print('ERROR: Could not connect to MongoDB:', e)
        return

    db = get_database()
    if db is None:
        print('ERROR: DB not connected')
        return

    try:
        emp_count = await db.employees.count_documents({})
        att_count_today = await db.attendance.count_documents({"Date": "2026-08-21"})
        distinct_empids = await db.attendance.distinct("EmpID", {"Date": "2026-08-21"})

        print('EMPLOYEE_COUNT:', emp_count)
        print('ATTENDANCE_COUNT_TODAY:', att_count_today)
        print('DISTINCT_EMPIDS_TODAY:', json.dumps(distinct_empids, indent=2))
    except Exception as e:
        print('ERROR during DB queries:', e)
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
