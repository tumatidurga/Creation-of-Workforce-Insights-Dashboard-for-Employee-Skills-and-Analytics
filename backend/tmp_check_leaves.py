import asyncio
import json
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.database import connect_to_mongo, get_database, close_mongo_connection

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print(json.dumps({"error": "db_connect_failed", "detail": str(e)}))
        return

    db = get_database()
    if db is None:
        print(json.dumps({"error": "no_db_instance"}))
        return

    emp_id = 'EMP000001'
    docs = await db.leaves.find({'EmpID': emp_id}).to_list(length=None)
    print(json.dumps({'emp_id': emp_id, 'count': len(docs), 'documents': docs}, default=str, indent=2))

    await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
