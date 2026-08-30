import asyncio, json, sys
sys.path.append(r'.')
from backend.app.database import connect_to_mongo, close_mongo_connection, get_database
from backend.app.services.workforce_services import AttendanceService

EMP = "EMP000001"

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print('ERROR: Could not connect to MongoDB:', e)
        return

    try:
        items, total = await AttendanceService.get_all(page=1, size=50, date='2026-08-21')
        found = [it for it in items if (it.get('empId') or it.get('EmpID') or it.get('employeeId')) == EMP]
        print(f'FOUND_COUNT_FOR_{EMP}:', len(found))
        print('FOUND_RECORDS:')
        print(json.dumps(found, indent=2, default=str))
    except Exception as e:
        print('ERROR during AttendanceService.get_all fetch for EMP:', e)
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
