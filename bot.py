from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot_instance import bot
from routers import router
import asyncio

dp = Dispatcher(storage=MemoryStorage())


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("[LOG] - Бот запущен успешно")
    await dp.start_polling(bot, parse_mode="HTML")


if __name__ == "__main__":
    asyncio.run(main())
