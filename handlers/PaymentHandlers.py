from aiogram import Bot, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from core import config, bot
from database import *
from keyboards import UserKeyboards as User_kb
from lexicon import LEXICON, payment_lexicon
from states import UserStates
import utils

router: Router = Router()


@router.callback_query(F.data == 'top_up_balance', StateFilter(default_state))
async def start_top_up(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    balance = '{:,}'.format(round(get_balance(callback.from_user.id))).replace(',', ' ')

    data['original_message_id'] = (
        await callback.message.edit_text(
            text=payment_lexicon['input_amount_top_up'].format(balance),
            reply_markup=User_kb.payment_back_to_account())
    ).message_id

    await state.set_state(UserStates.top_up)
    await state.update_data(data)


@router.message(StateFilter(UserStates.top_up))
async def order(message: Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    balance = '{:,}'.format(round(get_balance(message.from_user.id))).replace(',', ' ')

    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if 'original_message_id' not in data:
        await message.answer('Что-то пошло не так, попробуйте ещё раз.')
        await state.clear()

    if not message.text:
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_amount_top_up'].format(balance) + LEXICON['text_needed'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass
        return

    if message.text.replace(' ', '').isdigit():
        amount = int(message.text.replace(' ', ''))
    else:
        return await bot.edit_message_text(
            text=payment_lexicon['input_amount_top_up'].format(balance) + payment_lexicon['wrong_amount'],
            chat_id=message.from_user.id, message_id=data['original_message_id'],
            reply_markup=User_kb.payment_back_to_account()
        )

    response = await utils.create_invoice(amount, '', '1', '1')

    if response['Success']:
        await bot.edit_message_text(
            text=payment_lexicon['confirm_top_up'].format(balance, amount),
            chat_id=message.from_user.id, message_id=data['original_message_id'],
            reply_markup=User_kb.invoice_kb(response['Model']['Url'])
        )

    else:
        await bot.edit_message_text(
            text='<b>Что-то пошло не так... Свяжитесь, пожалуйста, с поддержкой:</b>',
            chat_id=message.from_user.id, message_id=data['original_message_id'],
            reply_markup=User_kb.support_kb()
        )

        print(f'Ошибка {response["ErrorCode"]} при попытке создания инвойса: {response["Message"]}')

    await state.clear()


@router.callback_query(F.data == 'cashout_request')
async def cashout_request(callback: CallbackQuery, state: FSMContext):
    balance = get_balance(callback.from_user.id)

    if balance == 0:
        return await callback.message.edit_text(LEXICON['no_money_to_cashout'], reply_markup=User_kb.top_up_kb())

    balance = '{:,}'.format(round(balance)).replace(',', ' ')

    data = {
        'original_message_id': (
            await callback.message.edit_text(
                payment_lexicon['input_amount_cashout'].format(balance),
                reply_markup=User_kb.payment_back_to_account())
        ).message_id
    }

    await state.set_state(UserStates.cashout_amount)
    await state.update_data(data)


@router.message(StateFilter(UserStates.cashout_amount))
async def cashout_amount_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    balance = get_balance(message.from_user.id)
    balance_text = '{:,}'.format(round(balance)).replace(',', ' ')

    await bot.delete_message(message.from_user.id, message.message_id)

    if 'original_message_id' not in data:
        await message.answer('Что-то пошло не так. Попробуйте ещё раз.')
        return state.clear()

    if not message.text:
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_amount_cashout'].format(balance_text) + LEXICON['text_needed'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    try:
        amount = float(message.text.replace(' ', ''))
    except ValueError:
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_amount_cashout'].format(balance_text) + payment_lexicon['wrong_amount'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if amount < 60 or amount > balance:
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_amount_cashout'].format(balance_text) + payment_lexicon['limit'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    await bot.edit_message_text(
        text=payment_lexicon['input_card_number'].format(balance_text, '{:,}'.format(round(amount)).replace(', ', ' ')),
        chat_id=message.from_user.id, message_id=data['original_message_id'],
        reply_markup=User_kb.back_to_cashout_amount()
    )

    data['amount'] = round(amount)

    await state.set_state(UserStates.input_card_number)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_card_number))
async def input_card_number(message: Message, state: FSMContext):
    data = await state.get_data()
    balance_text = '{:,}'.format(round(get_balance(message.from_user.id))).replace(',', ' ')

    await bot.delete_message(message.from_user.id, message.message_id)

    if 'original_message_id' not in data:
        await message.answer('Что-то пошло не так. Попробуйте ещё раз.')
        return state.clear()

    if not message.text:
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_card_number'].format(
                    balance_text, '{:,}'.format(data['amount']).replace(', ', ' ')) + LEXICON['text_needed'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if len(message.text) not in [16, 19] or not message.text.replace(' ', '').isdecimal():
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_card_number'].format(balance_text, '{:,}'.format(
                    data['amount']).replace(', ', ' ')) + payment_lexicon['wrong_number'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if data['amount'] < 0 or data['amount'] > get_balance(message.from_user.id):
        try:
            await bot.edit_message_text(
                text=payment_lexicon['input_amount_cashout'] + payment_lexicon['limit'],
                chat_id=message.from_user.id, message_id=data['original_message_id'],
                reply_markup=User_kb.payment_back_to_account()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    amount_text = '{:,}'.format(data['amount']).replace(',', ' ')

    await bot.edit_message_text(
        text=payment_lexicon['confirm_cashout'].format(amount_text, message.text),
        chat_id=message.from_user.id, message_id=data['original_message_id'],
        reply_markup=User_kb.confirm_cashout_kb()
    )

    data['card_number'] = message.text

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data.startswith('cashout'), StateFilter(default_state))
async def cashout_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback.data.split('_')[-1] == 'cancel':
        return await utils.send_account_info(callback)

    if not all(key in data for key in ('original_message_id', 'amount', 'card_number')):
        await callback.message.delete()
        await callback.answer('Эта кнопка устарела, попробуйте ещё раз.')
        return state.clear()

    try:
        edit_balance(callback.from_user.id, -data['amount'], 'cashout')

        user = get_user(callback.from_user.id)
        amount_text = '{:,}'.format(data['amount']).replace(',', ' ')

        for admin_id in config.tg_bot.admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=payment_lexicon['cashout_request'].format(
                        user[2], user[1], data['card_number'], amount_text)
                )
            except TelegramBadRequest:
                pass

        await callback.message.edit_text(
            payment_lexicon['cashout_request_saved'].format(amount_text, data['card_number']),
            reply_markup=User_kb.from_cashout_to_main_menu()
        )

    except Exception as e:
        print(f'Ошибка при попытке вывода средств: {str(e)}')
        await callback.message.edit_text(payment_lexicon['cashout_error'])


@router.callback_query(F.data == 'from_cashout_to_main_menu', StateFilter(default_state))
async def cashout_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        reply_markup=None)
    await callback.message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())
