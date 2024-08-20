import asyncio

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database import user_is_not_banned, get_ban_info


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 0.3):
        self.delay = delay
        super().__init__()

    async def __call__(self, handler, event: Message, data):
        await asyncio.sleep(self.delay)
        return await handler(event, data)


class BanMiddleware(BaseMiddleware):
    def __init__(self):
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
                        await event.answer(
                            f"Вы забанены до <i>{ban_info[2]}</i>"
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            f"Вы забанены до {ban_info[2]}",
                            show_alert=True
                        )
                return

        return await handler(event, data)
