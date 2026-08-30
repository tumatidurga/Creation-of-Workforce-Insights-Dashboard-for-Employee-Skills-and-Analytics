"""
Simple async test of Motor connection using the same configuration used in database.py
Prints only:
MOTOR_CONNECTION_OK
<database name>
user_accounts count

Do not print credentials/secrets.
"""
import asyncio
import sys

sys.path.insert(0, '.')
from backend.app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    url = settings.MONGODB_URL
    db_name = settings.DATABASE_NAME
    try:
        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
        # ping
        await client.admin.command('ping')
        db = client[db_name]
        cnt = await db.user_accounts.count_documents({})
        print('MOTOR_CONNECTION_OK')
        print(db_name)
        print(cnt)
    except Exception as e:
        print('MOTOR_CONNECTION_FAILED')
        print(str(e))
    finally:
        try:
            client.close()
        except Exception:
            pass

if __name__ == '__main__':
    asyncio.run(main())
