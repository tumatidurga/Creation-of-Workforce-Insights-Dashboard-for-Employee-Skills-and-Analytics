import asyncio
from backend.app.database import connect_to_mongo, close_mongo_connection, get_database
from backend.app.services.workforce_services import LeaveService
from backend.app.models.schemas import LeaveStatusUpdate

async def main():
    await connect_to_mongo()
    try:
        update = LeaveStatusUpdate(status='Approved', approverComments='Approved in debug')
        result = await LeaveService.update_status('6a885560d0009ba4d8304b5f', update, actor_user={'name':'Automation','userId':'hr-admin','empId':None,'role':'HR_ADMIN'})
        print('RESULT:', result)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()

if __name__ == '__main__':
    asyncio.run(main())
