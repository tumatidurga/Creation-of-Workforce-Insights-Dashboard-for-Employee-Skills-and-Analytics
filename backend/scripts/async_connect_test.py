import os, sys, asyncio
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.database import connect_to_mongo, get_database
from backend.app.config import settings

async def main():
    import traceback
    print('settings url', settings.MONGODB_URL)
    try:
        await connect_to_mongo()
        db = get_database()
        print('connected db:', db.name if db is not None else None)
    except Exception:
        traceback.print_exc()

asyncio.run(main())
