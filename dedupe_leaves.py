#!/usr/bin/env python3
"""
Deduplicate the `leaves` collection in the specified MongoDB database.
Keeps one document per (EmpID, StartDate, EndDate) triple and deletes other duplicates.

Usage:
  - Set MONGODB_URI env var to point to the MongoDB server (default: mongodb://localhost:27017)
  - Optionally set MONGODB_DB to choose DB (default: test)
  - Run: python dedupe_leaves.py

This script uses pymongo.
"""
import os
import sys
from pprint import pprint

try:
    from pymongo import MongoClient
except ImportError:
    print("pymongo is not installed. Please install it (python -m pip install pymongo) and re-run this script.")
    sys.exit(2)

uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.environ.get("MONGODB_DB", "test")

print(f"Connecting to MongoDB URI={uri} DB={db_name}")
client = MongoClient(uri)
db = client[db_name]
coll = db.get_collection("leaves")

# Aggregation to find duplicate groups by EmpID + StartDate + EndDate
pipeline = [
    {
        "$group": {
            "_id": {"EmpID": "$EmpID", "StartDate": "$StartDate", "EndDate": "$EndDate"},
            "ids": {"$push": "$_id"},
            "count": {"$sum": 1},
        }
    },
    {"$match": {"count": {"$gt": 1}}},
]

print("Finding duplicate groups (by EmpID, StartDate, EndDate)...")
cursor = coll.aggregate(pipeline)

groups = list(cursor)
num_groups = len(groups)
print(f"Found {num_groups} duplicate group(s)")

total_removed = 0
removed_by_group = []
for g in groups:
    ids = g.get("ids", [])
    # Keep the first _id, remove the rest
    if len(ids) <= 1:
        continue
    keep = ids[0]
    to_remove = ids[1:]
    res = coll.delete_many({"_id": {"$in": to_remove}})
    removed_count = res.deleted_count
    total_removed += removed_count
    removed_by_group.append({"_id": g.get("_id"), "kept": keep, "removed_count": removed_count})

print(f"Total documents removed: {total_removed}")
if removed_by_group:
    print("Sample of removed groups (up to 20):")
    pprint(removed_by_group[:20])

print("Done.")
