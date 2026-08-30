import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import NotificationService


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL NOTIFICATIONS")
    print("====================================")

    notifications = await NotificationService.get_all()

    print(
        "TOTAL NOTIFICATIONS:",
        len(notifications)
    )

    for notification in notifications[:5]:

        print(
            notification.get("empId"),
            "-",
            notification.get("type"),
            "-",
            notification.get("message"),
            "-",
            notification.get("isRead"),
            "-",
            notification.get("timestamp")
        )

    print("\n====================================")
    print("TEST 2: NOTIFICATION DETAILS")
    print("====================================")

    if notifications:

        notification = notifications[0]

        print(
            "ID:",
            notification.get("id")
        )

        print(
            "Employee:",
            notification.get("empId")
        )

        print(
            "Title:",
            notification.get("title")
        )

        print(
            "Type:",
            notification.get("type")
        )

        print(
            "Message:",
            notification.get("message")
        )

        print(
            "Read:",
            notification.get("isRead")
        )

        print(
            "Priority:",
            notification.get("priority")
        )

        print(
            "Timestamp:",
            notification.get("timestamp")
        )

    else:

        print("No notifications found.")


if __name__ == "__main__":
    asyncio.run(main())