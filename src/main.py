import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram_dialog import StartMode
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.client import client_router
from config import BOT_TOKEN


storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)
dp.include_routers(client_router)

async def on_startup(dp):
    commands = [
        types.BotCommand(command="/start", description="Запуск бота"),
    ]
    await bot.set_my_commands(commands)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup(dp)
    print("Бот запущен!")
    await dp.start_polling(bot)

asyncio.run(main())
