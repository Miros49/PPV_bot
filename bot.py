import asyncio
import logging
import subprocess

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI
from uvicorn import Config, Server

from core import config, storage, bot
from database import init_db, init_wellcome_db
from handlers import UserHandlers, AdminHandlers, PaymentHandlers, DebugHandlers
from middlewares import RateLimitMiddleware, BanMiddleware, TechnicalWork, WelcomeStub
from services import run_server

logging.basicConfig(level=logging.INFO)

default = DefaultBotProperties(parse_mode='HTML')
dp: Dispatcher = Dispatcher(storage=storage)

# dp.update.middleware(RateLimitMiddleware())
# dp.update.middleware(BanMiddleware())
# dp.update.middleware(TechnicalWork())
# dp.update.middleware(WelcomeStub())

# dp.message.middleware(WelcomeStub())
dp.message.middleware(RateLimitMiddleware())
dp.message.middleware(BanMiddleware())
dp.message.middleware(TechnicalWork())

# dp.callback_query.middleware(WelcomeStub())
dp.callback_query.middleware(RateLimitMiddleware())
dp.callback_query.middleware(BanMiddleware())
dp.callback_query.middleware(TechnicalWork())

dp.include_router(AdminHandlers.router)
dp.include_router(UserHandlers.router)
dp.include_router(PaymentHandlers.router)
dp.include_router(DebugHandlers.router)


async def main():
    init_db()
    init_wellcome_db()

    await bot.delete_webhook(drop_pending_updates=False)

    polling_task = asyncio.create_task(dp.start_polling(bot))

    # Запуск uvicorn как отдельного процесса
    # server_process = subprocess.Popen([
    #     "uvicorn",
    #     "services.payment:app",
    #     "--host", config.server.ip,
    #     "--port", str(config.server.port),
    #     "--reload"  # Используйте reload, только если вам нужна автоматическая перезагрузка
    # ])

    try:
        await polling_task
    finally:
        # server_process.terminate()  # Завершение процесса при остановке бота
        pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Forced shutdown...")
