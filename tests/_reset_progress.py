"""Reset task progress to 100 to allow re-generating report."""
import asyncio, sys
from app.config.database import AsyncSessionMaker
from app.services.data_service import DataService

async def reset(task_id):
    async with AsyncSessionMaker() as db:
        task = await DataService.get_task(db, task_id)
        if task:
            task.progress = 100
            await db.commit()
            print(f"Reset task {task_id}: progress={task.progress}")
        else:
            print(f"Task {task_id} not found")
            sys.exit(1)

asyncio.run(reset(sys.argv[1]))
