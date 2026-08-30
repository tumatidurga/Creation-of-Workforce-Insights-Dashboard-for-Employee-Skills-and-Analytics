import asyncio

from backend.app.database import connect_to_mongo, get_database


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    db = get_database()

    print("\n====================================")
    print("RAW LEAVE STATUS COUNTS")
    print("====================================")

    statuses = await db.leaves.aggregate([
        {
            "$group": {
                "_id": "$Status",
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]).to_list(length=100)

    for item in statuses:
        print(
            repr(item["_id"]),
            "-",
            item["count"]
        )


if __name__ == "__main__":
    asyncio.run(main())