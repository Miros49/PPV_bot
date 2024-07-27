from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core import *

config: Config = load_config('.env')
ADMIN_IDS: list[int] = config.tg_bot.admin_ids


class IsAdminFilter(Filter):
    async def __call__(self, update: Message | CallbackQuery, *args, **kwargs):
        return update.from_user.id in ADMIN_IDS


class AdminGameFilter(Filter):
    async def __call__(self, callback: CallbackQuery, *args, **kwargs):
        return ('admin_game' in callback.data) or ('a_back_to_projects' in callback.data)
