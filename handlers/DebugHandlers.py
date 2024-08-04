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


@router.message(Command('test_my_gender'))
async def my_gender(message: Message, state: FSMContext):
    await message.answer('Фу! Вы 100%. Пользование ботом для вас теперь ограничено')
    await state.set_state('gay')


@router.message(StateFilter(default_state))
async def deleting_unexpected_messages(message: Message):
    await bot.delete_message(message.from_user.id, message.message_id)


@router.callback_query()
async def kalosbornik(callback: CallbackQuery, state: FSMContext):
    print(callback.data)
    print(await state.get_state(), await state.get_data(), sep='\n\n')
