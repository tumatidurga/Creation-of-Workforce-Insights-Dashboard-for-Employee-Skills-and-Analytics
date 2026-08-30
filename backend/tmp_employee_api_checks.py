import asyncio, json, sys
sys.path.append(r'.')
from backend.app.database import connect_to_mongo, close_mongo_connection
from backend.app.services.workforce_services import EmployeeService

async def run():
    await connect_to_mongo()
    try:
        print('=== PAGE 1 ===')
        items1, total1 = await EmployeeService.get_all(page=1, size=50)
        print('items1_count:', len(items1))
        print('total1:', total1)
        print('page1_first_empId:', items1[0].get('empId') if items1 else None)

        print('\n=== PAGE 2 ===')
        items2, total2 = await EmployeeService.get_all(page=2, size=50)
        print('items2_count:', len(items2))
        print('total2:', total2)
        print('page2_first_empId:', items2[0].get('empId') if items2 else None)

        set1 = set([e.get('empId') for e in items1])
        set2 = set([e.get('empId') for e in items2])
        overlap = set1.intersection(set2)
        print('\noverlap_count_between_page1_and_page2:', len(overlap))

        print('\n=== SEARCH EMP000001 ===')
        s_items, s_total = await EmployeeService.get_all(page=1, size=50, search='EMP000001')
        print('search_items_count:', len(s_items))
        print('search_total:', s_total)
        print('search_first:', s_items[0].get('empId') if s_items else None)

        print('\n=== FILTER department=IT ===')
        f_items, f_total = await EmployeeService.get_all(page=1, size=50, department='IT')
        print('filter_items_count:', len(f_items))
        print('filter_total:', f_total)
        if f_items:
            print('filter_first_empId:', f_items[0].get('empId'))

    except Exception as e:
        print('ERROR:', e)
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(run())
