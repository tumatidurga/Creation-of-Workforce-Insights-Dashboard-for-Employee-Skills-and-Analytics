import asyncio, json, sys
sys.path.append(r'.')
from backend.app.database import connect_to_mongo, close_mongo_connection
from backend.app.services.workforce_services import EmployeeService

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print('ERROR: Could not connect to MongoDB:', e)
        return
    try:
        items, total = await EmployeeService.get_all(page=1, size=50)
        print('returned_items_count:', len(items))
        print('total:', total)
        print('page: 1')
        print('size: 50')
        pages = (total + 50 - 1) // 50 if 50 else 1
        print('pages:', pages)
        print('\nSAMPLE_ITEMS:')
        print(json.dumps(items[:5], indent=2, default=str))
    except Exception as e:
        print('ERROR during EmployeeService.get_all:', e)
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
