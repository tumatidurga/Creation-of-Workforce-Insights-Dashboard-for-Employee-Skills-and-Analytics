import asyncio
import json
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.database import connect_to_mongo, get_database, close_mongo_connection
from backend.app.services.workforce_services import LeaveService

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print(json.dumps({"error": "db_connect_failed", "detail": str(e)}))
        return

    try:
        items = await LeaveService.get_all(page=1, size=50, emp_id='EMP000001')
    except Exception as e:
        print(json.dumps({"error": "service_error", "detail": str(e)}))
    else:
        print(json.dumps({"count": len(items), "items": items}, default=str, indent=2))

    await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
