import asyncio, json, sys
sys.path.append(r'.')
from backend.app.database import connect_to_mongo, close_mongo_connection, get_database
from backend.app.services.workforce_services import AttendanceService

async def main():
    try:
        await connect_to_mongo()
    except Exception as e:
        print('ERROR: Could not connect to MongoDB:', e)
        return

    try:
        page = 1
        size = 50
        date = "2026-08-21"
        items, total = await AttendanceService.get_all(page=page, size=size, date=date)
        pages = (total + size - 1) // size if size else 1
        print('returned_items_count:', len(items))
        print('total:', total)
        print('page:', page)
        print('size:', size)
        print('pages:', pages)

        # status counts
        counts = {}
        for it in items:
            st = (it.get('status') or it.get('AttendanceStatus') or '').strip()
            counts[st] = counts.get(st, 0) + 1

        # specific mapping counts
        absent_count = sum(1 for s in counts for _ in [1] if str(s).lower() == 'absent')
        # But better compute by scanning items for substrings
        absent = sum(1 for it in items if ((it.get('status') or it.get('AttendanceStatus') or '').strip().lower() == 'absent'))
        working = sum(1 for it in items if ((it.get('status') or it.get('AttendanceStatus') or '').strip().lower() == 'working' or ((it.get('checkIn') or it.get('CheckIn')) and not (it.get('checkOut') or it.get('CheckOut')))))
        checked_out = sum(1 for it in items if ((it.get('status') or it.get('AttendanceStatus') or '').strip().lower() in ['checked out','checked_out','checkedout','day completed','checked']))
        late = sum(1 for it in items if (it.get('LateArrival') is True or (it.get('status') and 'late' in it.get('status').lower())))

        print('status_counts_raw:', json.dumps(counts, indent=2))
        print('Absent_detected:', absent)
        print('Working_detected:', working)
        print('CheckedOut_detected:', checked_out)
        print('Late_detected:', late)

        print('\nSAMPLE_ITEMS (first 5):')
        print(json.dumps(items[:5], indent=2, default=str))
    except Exception as e:
        print('ERROR during AttendanceService.get_all:', e)
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
