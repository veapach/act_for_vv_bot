from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot_instance import bot
from routers import router
import asyncio
from datetime import datetime
from database import db

dp = Dispatcher(storage=MemoryStorage())


async def on_shutdown(dispatcher: Dispatcher):
    stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[LOG] [{stop_time}] - Бот завершает работу")
    await bot.session.close()
    await dispatcher.storage.close()


async def main():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await bot.session.close()

    dp.include_router(router)
    await db.initialize_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print(f"[LOG] [{start_time}] - Бот запущен успешно")
    print("Для остановки бота введите 'stop' или нажмите Ctrl+C")

    stop_event = asyncio.Event()

    async def check_stop_command():
        while True:
            command = await asyncio.get_event_loop().run_in_executor(None, input)
            if command.lower() == "stop":
                stop_event.set()
                break

    try:
        polling_task = asyncio.create_task(dp.start_polling(bot, parse_mode="HTML"))
        input_task = asyncio.create_task(check_stop_command())

        await asyncio.wait(
            [polling_task, input_task], return_when=asyncio.FIRST_COMPLETED
        )
    except KeyboardInterrupt:
        print("[LOG] - Получен сигнал Ctrl+C")
    finally:
        await on_shutdown(dp)
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[LOG] [{stop_time}] - Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
