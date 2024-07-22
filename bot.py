import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from core import Config, load_config, storage
from database import init_db
from handlers import UserHandlers, AdminHandlers, PaymentHandlers

logging.basicConfig(level=logging.INFO)
config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)
dp: Dispatcher = Dispatcher(storage=storage)

dp.include_router(UserHandlers.router)
dp.include_router(AdminHandlers.router)
dp.include_router(PaymentHandlers.router)


async def main():
    init_db()

    await bot.delete_webhook(drop_pending_updates=False)
    polling_task = asyncio.create_task(dp.start_polling(bot))

    await asyncio.gather(polling_task)


if __name__ == '__main__':
    asyncio.run(main())
