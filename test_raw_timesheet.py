import asyncio

from backend.app.database import connect_to_mongo, get_database


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    db = get_database()

    print("\n====================================")
    print("RAW TIMESHEET DOCUMENT")
    print("====================================")

    document = await db.timesheets.find_one(
        {},
        {"_id": 0}
    )

    print(document)


if __name__ == "__main__":
    asyncio.run(main())