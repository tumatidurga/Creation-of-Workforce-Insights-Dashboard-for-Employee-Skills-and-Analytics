import asyncio
from backend.app.database import connect_to_mongo, get_database

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print('DB connect failed:', e)
        return
    db = get_database()
    if db is None:
        print('No DB')
        return
    doc = await db.user_accounts.find_one({'managerLoginId':'MGR000001'}, {'_id':0,'passwordHash':0})
    print('FOUND:', doc)

if __name__ == '__main__':
    asyncio.run(main())
