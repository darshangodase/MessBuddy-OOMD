import asyncio
import sys
sys.path.insert(0, 'backend_py')

from app.db import DatabaseManager
from app.models.mess import Mess

async def test():
    try:
        await DatabaseManager.get_instance().init_db()
        print("Database initialized")
        
        mess = await Mess.find_one()
        if mess:
            print(f"Found mess: {mess.Mess_Name}")
            print(f"Ratings: {mess.Ratings}")
            print(f"RatedBy: {mess.RatedBy}")
            
            dict_result = mess.to_dict()
            print(f"to_dict() worked: {dict_result.get('Mess_Name')}")
        else:
            print("No mess found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
