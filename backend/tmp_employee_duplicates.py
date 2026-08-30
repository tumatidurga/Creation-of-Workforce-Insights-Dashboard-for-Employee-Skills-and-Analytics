import asyncio
import sys
sys.path.append(r'.')
from backend.app.database import connect_to_mongo, close_mongo_connection, get_database

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print('ERROR: connect_to_mongo failed:', e)
        return
    db = get_database()
    try:
        # Count missing or null EmpID
        missing_count = await db.employees.count_documents({"EmpID": {"$in": [None, "", [], {}]}})
        print('missing_EmpID_count:', missing_count)
        # Find duplicate EmpID counts
        pipeline = [
            {"$match": {"EmpID": {"$nin": [None, ""]}}},
            {"$group": {"_id": "$EmpID", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        dups = []
        async for doc in db.employees.aggregate(pipeline):
            dups.append(doc)
        print('duplicate_EmpID_examples_count:', len(dups))
        if dups:
            import json
            print(json.dumps(dups, indent=2))
    except Exception as e:
        print('ERROR during duplicate check:', e)
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
