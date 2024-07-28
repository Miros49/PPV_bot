from aiogram import Bot, Router, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from core import Config, load_config
from database import *
from keyboards import UserKeyboards as User_kb
from lexicon import LEXICON
from states import UserStates

config: Config = load_config('.env')
router: Router = Router()


@router.callback_query(F.data == 'top_up_balance')
async def start_top_up(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("‼️ Введите сумму для пополнения (мин. 60 руб):")
    await state.set_state(UserStates.top_up)


@router.message(StateFilter(UserStates.top_up))
async def order(message: Message, bot: Bot, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    amount_text = message.text
    if amount_text.isdigit() and int(amount_text) >= 60:
        amount = int(amount_text) * 100
    else:
        return await message.answer('❕Введите корректное число')

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
    pass


@router.callback_query(F.data == 'cashout_request')
async def cashout_request(callback: CallbackQuery, state: FSMContext):
    balance = get_balance(callback.from_user.id)

    if balance == 0:
        return await callback.message.edit_text(LEXICON['no_money_to_cashout'], reply_markup=User_kb.top_up_kb())

    await callback.message.edit_text(LEXICON['input_card_number'])
    await state.set_state(UserStates.input_card_number)


@router.message(StateFilter(UserStates.input_card_number))
async def input_card_number(message: Message, state: FSMContext):
    await message.answer(LEXICON['confirm_cashout'].format(str(get_balance(message.from_user.id)), message.text),
                         reply_markup=User_kb.confirm_cashout_kb())
    await state.clear()


@router.callback_query(F.data.startswith('cashout'))
async def cashout_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('я устал')
