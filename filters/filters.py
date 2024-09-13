from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core import config


class IsAdminFilter(Filter):
    async def __call__(self, update: Message | CallbackQuery, *args, **kwargs):
        return update.from_user.id in config.tg_bot.admin_ids


class AdminGameFilter(Filter):
    async def __call__(self, callback: CallbackQuery, *args, **kwargs):
        return ('admin_game' in callback.data) or ('a_back_to_projects' in callback.data)
