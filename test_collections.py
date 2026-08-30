import asyncio

from backend.app.database import connect_to_mongo
from backend.app.database import get_database


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    db = get_database()

    collections = await db.list_collection_names()

    print("\n====================================")
    print("MONGODB COLLECTIONS")
    print("====================================")

    for collection in sorted(collections):
        print(collection)


if __name__ == "__main__":
    asyncio.run(main())