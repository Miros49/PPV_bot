import asyncio

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime, timezone, timedelta

from core import config
from database import user_is_not_banned, get_ban_info, is_technical_work, remember_user_id, remember_welcomed_user_id, \
    is_user_welcomed, add_user
from keyboards.UserKeyboards import wellcome_kb
from lexicon import LEXICON


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        await asyncio.sleep(self.delay)
        return await handler(event, data)


class BanMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

            if not user_is_not_banned(user_id):
                ban_info = get_ban_info(user_id)
                if ban_info:
                    if isinstance(event, Message):
                        await event.delete()
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            f"Вы забанены до {ban_info[2]}",
                            show_alert=True
                        )
                return

        return await handler(event, data)


class TechnicalWork(BanMiddleware):
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id in config.tg_bot.admin_ids:
            return await handler(event, data)

        if isinstance(event, (Message, CallbackQuery)):
            if is_technical_work():
                remember_user_id(event.from_user.id)

                if isinstance(event, Message):
                    await event.delete()
                    return await event.answer(LEXICON['technical_work_message'])

                return await event.answer(LEXICON['technical_work_callback'], show_alert=True)

        return await handler(event, data)


class WelcomeStub(BanMiddleware):
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        current_time = datetime.now(timezone(timedelta(hours=3)))
        prod = datetime(2024, 10, 4, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        if event.from_user.id in config.tg_bot.admin_ids or current_time > prod:
            return await handler(event, data)

        if isinstance(event, (Message, CallbackQuery)):
            if not is_user_welcomed(event.from_user.id):
                remember_welcomed_user_id(event.from_user.id)
                add_user(event.from_user.id, event.from_user.username, None)

                if isinstance(event, Message):
                    await event.delete()
                    return await event.answer(LEXICON['welcome_message'], reply_markup=wellcome_kb())

        if isinstance(event, Message):
            await event.delete()
