from aiogram import Bot, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from core import Config, load_config
from database import *
from keyboards import UserKeyboards as User_kb
from lexicon import LEXICON, payment_lexicon
from states import UserStates
import utils

config: Config = load_config('.env')
router: Router = Router()

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)


@router.callback_query(F.data == 'top_up_balance')
async def start_top_up(callback: CallbackQuery, state: FSMContext):
    data = {'mes_original': await callback.message.edit_text(payment_lexicon['input_amount_top_up'],
                                                             reply_markup=User_kb.payment_back_to_account())}
    await state.set_state(UserStates.top_up)
    await state.update_data(data)


@router.message(StateFilter(UserStates.top_up))
async def order(message: Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if 'mes_original' not in data:
        await message.answer('Что-то пошло не так, попробуйте ещё раз.')
        await state.clear()

    mes: Message = data['mes_original']

    if not message.text:
        try:
            data['mes_original'] = mes.edit_text(payment_lexicon['input_amount_top_up'] + LEXICON['text_needed'],
                                                 reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return state.update_data(data)

    amount_text = message.text.replace(' ', '')

    if amount_text.isdigit() and int(amount_text) >= 60:
        amount = int(amount_text) * 100
    else:
        data['mes_original'] = await mes.edit_text(
            payment_lexicon['input_amount_top_up'] + payment_lexicon['wrong_amount'],
            reply_markup=User_kb.payment_back_to_account())
        return await state.update_data(data)

    await mes.delete()

    data['mes_original'] = await bot.send_invoice(
        chat_id=message.from_user.id,
        title='Пополнение счёта',
        description=f'На сумму: {amount_text} руб.',
        payload='test',
        provider_token=config.payment.token,
        currency='RUB',
        prices=[LabeledPrice(label='Сумма пополнения:', amount=amount)],
        max_tip_amount=2000,
        suggested_tip_amounts=[500, 1000, 1500],
        request_timeout=15,
        reply_markup=User_kb.payment_top_up_back()
    )

    await state.clear()
    await state.update_data(data)


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def succesful_payment_handler(message: Message, state: FSMContext):
    amount = message.successful_payment.total_amount / 100
    edit_balance(message.from_user.id, amount, 'top_up')

    data = await state.get_data()

    if 'mes_original' in data:
        await data['mes_original'].delete()

    await utils.send_account_info(message)
    await state.clear()


@router.callback_query(F.data == 'cashout_request')
async def cashout_request(callback: CallbackQuery, state: FSMContext):
    balance = get_balance(callback.from_user.id)

    if balance == 0:
        return await callback.message.edit_text(LEXICON['no_money_to_cashout'], reply_markup=User_kb.top_up_kb())

    balance = '{:,}'.format(round(balance)).replace(',', ' ')

    data = {'mes_original': await callback.message.edit_text(payment_lexicon['input_amount_cashout'].format(balance),
                                                             reply_markup=User_kb.payment_back_to_account())}

    await state.set_state(UserStates.cashout_amount)
    await state.update_data(data)


@router.message(StateFilter(UserStates.cashout_amount))
async def cashout_amount_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    balance = get_balance(message.from_user.id)

    await bot.delete_message(message.from_user.id, message.message_id)

    if 'mes_original' not in data:
        await message.answer('Что-то пошло не так. Попробуйте ещё раз.')
        return state.clear()

    mes: Message = data['mes_original']

    if not message.text:
        try:
            data['mes_original'] = await mes.edit_text(payment_lexicon['input_amount_cashout'] + LEXICON['text_needed'],
                                                       reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    try:
        amount = float(message.text.replace(' ', ''))
    except ValueError:
        try:
            data['mes_original'] = await mes.edit_text(
                payment_lexicon['input_amount_cashout'] + payment_lexicon['wrong_amount'],
                reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if amount < 0 or amount > balance:
        try:
            data['mes_original'] = await mes.edit_text(
                payment_lexicon['input_amount_cashout'] + payment_lexicon['limit'],
                reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    data['amount'] = amount
    data['mes_original'] = await mes.edit_text(payment_lexicon['input_card_number'],
                                               reply_markup=User_kb.back_to_cashout_amount())
    await state.set_state(UserStates.input_card_number)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_card_number))
async def input_card_number(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.from_user.id, message.message_id)

    if 'mes_original' not in data:
        await message.answer('Что-то пошло не так. Попробуйте ещё раз.')
        return state.clear()

    mes: Message = data['mes_original']

    if not message.text:
        try:
            data['mes_original'] = await mes.edit_text(payment_lexicon['input_card_number'] + LEXICON['text_needed'],
                                                       reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if len(message.text) not in [16, 19] or not message.text.replace(' ', '').isdecimal():
        try:
            data['mes_original'] = await mes.edit_text(
                payment_lexicon['input_card_number'] + payment_lexicon['wrong_number'],
                reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if data['amount'] < 0 or data['amount'] > get_balance(message.from_user.id):
        try:
            data['mes_original'] = await mes.edit_text(
                payment_lexicon['input_amount_cashout'] + payment_lexicon['limit'],
                reply_markup=User_kb.payment_back_to_account())
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    data['mes_original'] = await mes.edit_text(
        payment_lexicon['confirm_cashout'].format(data['amount'], message.text),
        reply_markup=User_kb.confirm_cashout_kb()
    )
    data['card_number'] = message.text

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data.startswith('cashout'))
async def cashout_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback.data.split('_')[-1] == 'cancel':
        return await utils.send_account_info(callback)

    if not all(key in data for key in ('mes_original', 'amount', 'card_number')):
        await callback.message.delete()
        await callback.answer('Эта кнопка устарела, попробуйте ещё раз.')
        return state.clear()

    try:
        edit_balance(callback.from_user.id, -data['amount'], 'cashout')

        for admin_id in config.tg_bot.admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=payment_lexicon['cashout_request'].format(
                        get_bot_user_id(callback.from_user.id), data['card_number'], data['amount']),
                )
            except TelegramBadRequest:
                pass

        await callback.message.edit_text(
            payment_lexicon['cashout_request_saved'].format(data['amount'], data['card_number']),
            reply_markup=User_kb.from_cashout_to_main_menu()
        )

    except Exception as e:
        print(f'Ошибка при попытке вывода средств: {str(e)}')
        await callback.message.edit_text(payment_lexicon['cashout_error'])


@router.callback_query(F.data == 'from_cashout_to_main_menu')
async def cashout_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        reply_markup=None)
    await callback.message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())
