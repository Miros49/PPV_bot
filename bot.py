import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI
from uvicorn import Config, Server


from core import config, storage
from database import init_db
from handlers import UserHandlers, AdminHandlers, PaymentHandlers, DebugHandlers
from middlewares import RateLimitMiddleware, BanMiddleware, TechnicalWork, WelcomeStub
from services import run_server

logging.basicConfig(level=logging.INFO)

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)
dp: Dispatcher = Dispatcher(storage=storage)

# dp.update.middleware(RateLimitMiddleware())
# dp.update.middleware(BanMiddleware())
# dp.update.middleware(TechnicalWork())
# dp.update.middleware(WelcomeStub())

dp.message.middleware(WelcomeStub())
dp.message.middleware(RateLimitMiddleware())
dp.message.middleware(BanMiddleware())
dp.message.middleware(TechnicalWork())

dp.callback_query.middleware(WelcomeStub())
dp.callback_query.middleware(RateLimitMiddleware())
dp.callback_query.middleware(BanMiddleware())
dp.callback_query.middleware(TechnicalWork())

dp.include_router(AdminHandlers.router)
dp.include_router(UserHandlers.router)
dp.include_router(PaymentHandlers.router)
dp.include_router(DebugHandlers.router)


async def main():
    init_db()

    await bot.delete_webhook(drop_pending_updates=False)

    polling_task = asyncio.create_task(dp.start_polling(bot))
    server_task = asyncio.to_thread(run_server)

    await asyncio.gather(polling_task, server_task)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
