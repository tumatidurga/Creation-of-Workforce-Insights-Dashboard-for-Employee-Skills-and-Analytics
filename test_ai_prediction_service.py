import asyncio

from backend.app.database import connect_to_mongo
from backend.app.services.workforce_services import (
    AIPredictionService
)


async def main():

    print("Connecting to MongoDB...")

    await connect_to_mongo()

    print("MongoDB connected.")

    print("\n====================================")
    print("TEST 1: GET ALL AI PREDICTIONS")
    print("====================================")

    predictions = await AIPredictionService.get_all()

    print(
        "TOTAL AI PREDICTIONS:",
        len(predictions)
    )

    for prediction in predictions[:5]:

        print(
            prediction.get("empId"),
            "-",
            prediction.get("attritionRisk"),
            "-",
            prediction.get("skillGapScore"),
            "-",
            prediction.get("workforceHealthScore"),
            "-",
            prediction.get("recommendation"),
            "-",
            prediction.get("predictionDate")
        )

    print("\n====================================")
    print("TEST 2: GET PREDICTION BY EMPLOYEE")
    print("====================================")

    prediction = await AIPredictionService.get_by_emp_id(
        "EMP000001"
    )

    if prediction:

        print("Prediction found:")

        print(
            "Employee:",
            prediction.get("empId")
        )

        print(
            "Attrition Risk:",
            prediction.get("attritionRisk")
        )

        print(
            "Skill Gap Score:",
            prediction.get("skillGapScore")
        )

        print(
            "Workforce Health Score:",
            prediction.get("workforceHealthScore")
        )

        print(
            "Recommendation:",
            prediction.get("recommendation")
        )

        print(
            "Prediction Date:",
            prediction.get("predictionDate")
        )

    else:

        print("Prediction NOT FOUND")


if __name__ == "__main__":
    asyncio.run(main())