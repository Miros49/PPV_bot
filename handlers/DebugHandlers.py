import asyncio

from aiogram import Bot, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.base import StorageKey

import utils
from database import *
from filters import *
from keyboards import UserKeyboards as User_kb
from lexicon import *
from states import UserStates

config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)

router: Router = Router()


@router.callback_query(StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def my_gender(callback: CallbackQuery):
    await callback.answer('‼️ Во время сделки вы не можете использовать другой функционал', show_alert=True)


@router.message(StateFilter(default_state))
async def deleting_unexpected_messages(message: Message):
    await bot.delete_message(message.from_user.id, message.message_id)


@router.callback_query()
async def callback_debug_handler(callback: CallbackQuery, state: FSMContext):
    print('CALLBACK DDEBUG:')
    print('callback.data:   ', callback.data)
    print('state:   ', await state.get_state())
    print('data:    ', await state.get_data())
