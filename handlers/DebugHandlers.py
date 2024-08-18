from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from core import bot
from states import UserStates

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
