import sys, pathlib, asyncio
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from backend.app.services.workforce_services import EmployeeService

async def main():
    items, total = await EmployeeService.get_all(size=1)
    print('total', total)
    print(items[0])

asyncio.run(main())
