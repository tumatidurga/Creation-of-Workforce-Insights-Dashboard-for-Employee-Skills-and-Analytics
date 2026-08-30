import sys
import asyncio
import json
sys.path.append(r'D:\infosys springboard internship docs\workforce-management-automation-system')
from backend.app.services.workforce_services import AttendanceService

async def main():
    items, total = await AttendanceService.get_all(page=1, size=50, date='2026-08-21')
    print('TOTAL_EMPLOYEES_MATCHING:', total)
    print('RETURNED_ITEMS_COUNT:', len(items))
    # Count statuses
    counts = {}
    for it in items:
        s = (it.get('status') or it.get('AttendanceStatus') or '').strip()
        counts[s] = counts.get(s, 0) + 1
    print('STATUS_COUNTS:', json.dumps(counts, indent=2))
    # print first 5 items
    print('SAMPLE_ITEMS:', json.dumps(items[:5], indent=2, default=str))

if __name__ == '__main__':
    asyncio.run(main())
