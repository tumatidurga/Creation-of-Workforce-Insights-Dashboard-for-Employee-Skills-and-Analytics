import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.config import settings

logger = logging.getLogger("uvicorn.error")


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None


db_instance = Database()


async def ensure_automation_indexes() -> None:
    """Ensure the small set of automation query indexes exists without duplicating existing ones."""
    if db_instance.db is None:
        return

    required_indexes = [
        ("attendance", [("CheckIn", 1), ("CheckOut", 1)]),
        ("attendance", [("EmpID", 1), ("Date", 1)]),
        ("attendance", [("EmpID", 1), ("ShiftDate", 1)]),
        ("leaves", [("Status", 1)]),
        ("shifts", [("EmpID", 1), ("ShiftDate", 1)]),
        ("shifts", [("EmpID", 1), ("Date", 1)]),
        ("notifications", [("AutomationEventKey", 1), ("NotificationScope", 1)]),
        ("audit_logs", [("AutomationEventKey", 1)]),
        ("employees", [("EmpID", 1)]),
    ]

    for collection_name, key_fields in required_indexes:
        try:
            collection = db_instance.db[collection_name]
            existing_keys = set()
            async for index_info in collection.list_indexes():
                index_key = tuple(sorted(index_info.get("key", {}).items()))
                if index_key:
                    existing_keys.add(index_key)

            target_key = tuple(sorted(key_fields))
            if target_key in existing_keys:
                continue

            await collection.create_index(key_fields)
        except Exception:
            logger.exception(f"Failed to ensure automation index for {collection_name} on {key_fields}")


async def connect_to_mongo():
    """Connect to the configured MongoDB database.

    Uses serverless-safe connection pool settings:
    - maxPoolSize=10  prevents connection exhaustion in serverless environments
    - minPoolSize=0   allows pool to scale down completely between requests
    - serverSelectionTimeoutMS=5000  fails fast if the DB is unreachable
    """
    if not settings.MONGODB_URL:
        logger.warning("MONGODB_URL is not set. Skipping database connection.")
        return

    try:
        logger.info(
            f"Connecting to MongoDB at {settings.MONGODB_URL[:40]}..."
        )

        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=0,
            serverSelectionTimeoutMS=5000,
        )

        # Verify that MongoDB is actually reachable.
        await db_instance.client.admin.command("ping")

        db_instance.db = db_instance.client[
            settings.DATABASE_NAME
        ]
        await ensure_automation_indexes()

        logger.info(
            f"MongoDB connection successful: "
            f"{settings.DATABASE_NAME}"
        )

    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")

        db_instance.client = None
        db_instance.db = None

        raise


async def close_mongo_connection():
    """Close MongoDB connection gracefully."""

    if db_instance.client:
        db_instance.client.close()

        db_instance.client = None
        db_instance.db = None

        logger.info("MongoDB connection closed.")


def get_database():
    """Return the active MongoDB database instance.

    In serverless environments (Vercel), the lifespan event may not always
    fire before the first request. This function is intentionally kept
    synchronous and returns whatever is currently initialised.
    Callers should check for None and handle it gracefully.
    """
    return db_instance.db