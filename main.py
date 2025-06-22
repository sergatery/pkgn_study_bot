import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config
from handlers.common import router as common_router
from handlers.admin import router as admin_router
from handlers.student import router as student_router
from handlers.homework import router as homework_router
from handlers.lectures import router as lectures_router
from handlers.tests import router as tests_router
from database import init_db
import time
print("Текущая временная зона:", time.tzname)

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Initialize database
    init_db()
    
    # Create bot and dispatcher
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Include routers
    dp.include_router(common_router)
    dp.include_router(admin_router)
    dp.include_router(student_router)
    dp.include_router(homework_router)
    dp.include_router(lectures_router)
    dp.include_router(tests_router)
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())