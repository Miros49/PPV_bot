from aiogram import Bot, Router, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from core import Config, load_config
from database import *
from keyboards import UserKeyboards as User_kb
from states import UserStates

config: Config = load_config('.env')
router: Router = Router()


@router.callback_query(F.data == 'top_up_balance')
async def start_top_up(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите сумму для пополнения (от 60 руб):")
    await state.set_state(UserStates.top_up)


@router.message(StateFilter(UserStates.top_up))
async def order(message: Message, bot: Bot, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    amount_text = message.text
    if amount_text.isdigit() and int(amount_text) >= 60:
        amount = int(amount_text) * 100
    else:
        return await message.answer('Неверный формат ввода, попробуй ещё раз')

    await bot.send_invoice(
        chat_id=message.from_user.id,
        title='Пополнение счёта',
        description=f'На сумму: {amount_text} руб.',
        payload='test',
        provider_token=config.payment.token,
        currency='RUB',
        prices=[LabeledPrice(label='Сумма пополнения:', amount=amount)],
        max_tip_amount=2000,
        suggested_tip_amounts=[500, 1000, 1500],
        request_timeout=15
    )
    await state.clear()


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def succesful_payment_handler(message: Message):
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount / 100
    edit_balance(user_id, amount)
    user_db_data = get_user(user_id)

    if user_db_data:
        user_id, tg_id, username, phone_number, balance, created_at = user_db_data
        account_info_text = f"Данные вашего аккаунта:\n\n" \
                            f"├ Баланс: {balance}\n" \
                            f"├ User ID: {user_id}\n" \
                            f"├ Username: {username}\n" \
                            f"└ Дата регистрации в боте: {created_at}\n"

        await message.answer(account_info_text, reply_markup=User_kb.account_kb())

