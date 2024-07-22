import asyncio
import logging
import math

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from core import *
from database import *
from filters import *
from keyboards import UserKeyboards as User_kb
from keyboards import AdminKeyboards as Admin_kb
from lexicon import *
from states import UserStates

# from utils import convert_datetime

logging.basicConfig(level=logging.INFO)
config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)

router: Router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command('admin'), StateFilter(default_state))
async def admin(message: Message):
    await message.answer(f'Здравствуйте, {message.from_user.username}! 😊', reply_markup=Admin_kb.menu_kb())


@router.callback_query(F.data == 'admin_reports', StateFilter(default_state))
async def admin_reports(callback: CallbackQuery):
    complaints = get_open_reports()
    if not complaints:
        return await callback.message.edit_text("✅ Нет необработанных жалоб")
    await callback.message.delete()

    for complaint in complaints:
        _, order_id, complainer_id, offender_id, complaint_text = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        text = (f'📋 <i><u>Репорт по заказу: {str(order_id)}</u></i>\n\n'
                f'👤 Автор: {complainer_username} (<code>{complainer_id}</code>)\n'
                f'💢 Жалуется на: {offender_username} (<code>{offender_id}</code>)\n\n'
                f'<b>📝 Причина:</b>\n{complaint_text}')

        await callback.message.answer(text, parse_mode='HTML')
        # TODO: добавить кнопку для того, чтобы отреагировать на репорт
