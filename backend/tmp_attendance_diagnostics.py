import asyncio, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from backend.app.database import connect_to_mongo, get_database, close_mongo_connection
from datetime import datetime

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print(json.dumps({'error':'db_connect_failed', 'detail': str(e)}))
        return
    db = get_database()
    if db is None:
        print(json.dumps({'error':'no_db'}))
        return
    # Employee count
    emp_count = await db.employees.count_documents({})
    # Today's date
    today = datetime.utcnow().date().isoformat()
    # Check attendance date field variations: Date, date
    att_date_count_Date = await db.attendance.count_documents({'Date': today})
    att_date_count_date = await db.attendance.count_documents({'date': today})
    # Distinct EmpID for today's attendance (both Date and date)
    distinct_empids_Date = await db.attendance.distinct('EmpID', {'Date': today})
    distinct_empids_date = await db.attendance.distinct('EmpID', {'date': today})
    # Total attendance documents
    total_attendance = await db.attendance.count_documents({})

    # Sample of attendance doc keys and a few records
    sample = await db.attendance.find({}, {'_id':0}).limit(5).to_list(length=5)

    output = {
        'today_utc': today,
        'employee_count': emp_count,
        'attendance_total_docs': total_attendance,
        'attendance_docs_with_Date_eq_today': att_date_count_Date,
        'attendance_docs_with_date_eq_today': att_date_count_date,
        'distinct_empids_with_Date_eq_today_count': len(distinct_empids_Date),
        'distinct_empids_with_date_eq_today_count_date_field': len(distinct_empids_date),
        'sample_attendance_docs': sample
    }
    print(json.dumps(output, default=str, indent=2))
    await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())