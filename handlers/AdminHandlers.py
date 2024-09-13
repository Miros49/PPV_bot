import asyncio

from aiogram.enums import ChatAction

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from pydantic.v1.class_validators import all_kwargs

from core import *
from database import *
from filters import *
from keyboards import AdminKeyboards as Admin_kb, UserKeyboards as User_kb
from lexicon import *
from states import AdminStates
import utils
from utils.admin_messages import send_information, send_chat_logs

router: Router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command('cls'))
async def cls(message: Message, state: FSMContext):
    await state.clear()

    await bot.delete_message(message.chat.id, message.message_id)

    mes = await message.answer('⚙️🔧 Ваше состояние очищено')
    await asyncio.sleep(1)
    await mes.delete()


@router.message(Command('admin'), StateFilter(default_state))
async def admin(message: Message):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)

    await message.answer(
        LEXICON['admin_menu'].format(
            income=calculate_profit(),
            users_number=count_users(),
            active_orders_number=count_active_orders(),
            active_deals_number=count_active_deals()
        ),
        reply_markup=Admin_kb.menu_reply_kb()
    )


@router.callback_query(F.data == 'back_to_admin_menu', StateFilter(default_state))
async def back_to_menu(callback: CallbackQuery):  # TODO: удалить
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    await callback.message.edit_textedit_text(
        LEXICON['admin_menu'].format(
            income=calculate_profit(),
            users_number=count_users(),
            active_orders_number=count_active_orders(),
            active_deals_number=count_active_deals()
        ),
        reply_markup=Admin_kb.menu_kb()
    )


@router.callback_query(F.data == 'admin_reports', StateFilter(default_state))
async def admin_reports(callback: CallbackQuery):  # TODO: удалить
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    open_complaints = get_open_complaints()

    if not open_complaints:
        return await callback.message.edit_text("✅ Нет необработанных жалоб")
    await callback.message.delete()

    for complaint in open_complaints:
        complaint_id, deal_id, complainer_id, offender_id, complaint_text, answer, created_at = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        await callback.message.answer(
            LEXICON['admin_report'].format(
                complaint_id, deal_id, created_at,
                get_bot_user_id(complainer_id), complainer_username, complainer_id,
                get_bot_user_id(offender_id), offender_username, offender_id, complaint_text),
            reply_markup=Admin_kb.answer_to_complaint_kb(complaint_id)
        )


@router.message(F.text == buttons['open_complaints'], StateFilter(default_state))
async def admin_reports(message: Message):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    open_complaints = get_open_complaints()

    if not open_complaints:
        return await message.answer("✅ Нет необработанных жалоб")
    await message.delete()

    for complaint in open_complaints:
        complaint_id, deal_id, complainer_id, offender_id, complaint_text, answer, created_at = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        await message.answer(
            LEXICON['admin_report'].format(
                complaint_id, deal_id, created_at,
                get_bot_user_id(complainer_id), complainer_username, complainer_id,
                get_bot_user_id(offender_id), offender_username, offender_id, complaint_text),
            reply_markup=Admin_kb.answer_to_complaint_kb(complaint_id)
        )


@router.callback_query(F.data.startswith('answer_to_complaint'), StateFilter(default_state))
async def answer_to_complaint_handler(callback: CallbackQuery, state: FSMContext):
    if not get_complaint(callback.data.split('_')[-1]):
        await callback.message.delete()
        return await callback.answer('🗑 Пользователь удалил данную жалобу', show_alert=True)

    mes = await bot.send_message(
        chat_id=callback.from_user.id, text=LEXICON['admin_input_answer'],
        reply_markup=Admin_kb.cancel_kb(),
        reply_to_message_id=callback.message.message_id
    )

    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        reply_markup=None)

    data = {
        'complaint_id': callback.data.split('_')[-1],
        'admin_original_message_id': mes.message_id
    }

    await state.set_state(AdminStates.input_answer)
    await state.update_data(data)


@router.callback_query(F.data.startswith('reject_complaint'), StateFilter(default_state))
async def reject_complaint_handler(callback: CallbackQuery, state: FSMContext):
    complaint = get_complaint(callback.data.split('_')[-1])

    # try:
    set_complaint_status(complaint[0], 'rejected')

    await bot.send_message(chat_id=complaint[2], text=LEXICON['complaint_rejected'].format(complaint[0]))
    await callback.message.edit_text('✅ Жалоба успешно отклонена')

    # except Exception as e:
    #     await callback.message.edit_text('Что-то пошло не так. Подробности смотри в консоли')
    #     print(f'Ошибка при попытке отклонения жалобы: {str(e)}')

    await state.clear()


@router.callback_query(F.data == 'cancel_button')
async def cancel_answering(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer('✅ Действие отменено', show_alert=True)

    await state.clear()


@router.message(StateFilter(AdminStates.input_answer))
async def confirm_answer_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if not message.text:
        await bot.edit_message_text(
            text=LEXICON['admin_input_answer'] + LEXICON['text_needed'],
            reply_markup=Admin_kb.cancel_kb()
        )

        return state.update_data(data)

    await bot.edit_message_text(
        text=LEXICON['admin_confirm_answer'].format(data['complaint_id'], message.text),
        chat_id=message.chat.id, message_id=data['admin_original_message_id'],
        reply_markup=Admin_kb.confirm_answer_kb()
    )

    data['answer_text'] = message.text

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data == 'confirm_answer', StateFilter(default_state))
async def confirm_answer_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if 'complaint_id' not in data or 'answer_text' not in data:
        await callback.message.delete()
        return callback.answer('Эта кнопка устарела, попробуйте ещё раз')

    set_complaint_answer(data['complaint_id'], data['answer_text'], 'closed')
    complaint = get_complaint(data['complaint_id'])

    await bot.send_message(complaint[2], LEXICON['admin_answered'].format(data['complaint_id']),
                           reply_markup=User_kb.view_answer(data['complaint_id']))

    await callback.message.edit_text(
        LEXICON['admin_confirm_answer'].format(
            data['complaint_id'], data['answer_text']) + LEXICON['admin_answer_saved']
    )


@router.callback_query(F.data == 'admin_information')
async def admin_information(callback: CallbackQuery, state: FSMContext):  # TODO: удалить
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    await callback.message.edit_text('Выберите критерий поиска:', reply_markup=Admin_kb.information_kb())
    await state.clear()


@router.message(F.text.in_(information_buttons), StateFilter(default_state))
async def admin_information_by(message: Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)

    data = {
        'target': information_map.get(message.text, None),
        'previous_steps': [],
        'admin_information_message_mes_id': (
            await message.answer(
                LEXICON['admin_information'].format(target_map.get(information_map.get(message.text, None))),
                reply_markup=Admin_kb.back_to_information_kb())
        ).message_id
    }

    await state.set_state(AdminStates.input_id)
    await state.update_data(data)


@router.message(StateFilter(AdminStates.input_id))
async def send_information_handler(message: Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    try:
        target_id = int(message.text)
    except ValueError:
        return await bot.edit_message_text(
            text=LEXICON['incorrect_value'],
            chat_id=message.chat.id, message_id=data['admin_information_message_mes_id'],
            reply_markup=Admin_kb.back_to_information_kb()
        )

    data['previous_steps'] = [f"{data['target']}_{str(target_id)}"]

    if not await send_information(data['target'], target_id, message.chat.id,
                                  data['admin_information_message_mes_id'], state):
        await state.clear()
        await state.update_data(data)


@router.callback_query(F.data.startswith('send_information_about'))
async def send_information_about_handler(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    data = await state.get_data()
    _, _, _, target, target_id = callback.data.split('_')

    data['previous_steps'].append(f"{target}_{target_id}")

    if data['target'] == 'order' and target_id == '0':
        return await callback.answer('Заказ не был создан вручную', show_alert=True)

    await send_information(target, int(target_id), callback.from_user.id, callback.message.message_id, state)

    await state.update_data(data)


# @router.message(StateFilter(AdminStates.information_about))
# async def doqfjweofj2pieruhvwjpievuqwhep(message: Message, state: FSMContext):
#     data = await state.get_data()
#
#     await message.delete()
#
#     if not message.text:
#         return await message.answer(LEXICON['text_needed'])
#
#     try:
#         target_id = int(message.text)
#
#     if data['target'] == 'order' and target_id == '0':
#         return await callback.answer('Заказ не был создан вручную', show_alert=True)
#
#     await send_information(target, int(target_id), callback.from_user.id, callback.message.message_id, state)


@router.callback_query(F.data.startswith('back_to_information_about'))
async def send_information_about_handler(callback: CallbackQuery, state: FSMContext):  # TODO: удалить
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    data = await state.get_data()
    _, _, _, _, target, target_id = callback.data.split('_')

    await send_information(target, int(target_id), callback.from_user.id, callback.message.message_id, state)

    if 'deal_chat_messages' in data:  # Удаление сообщений из чата пользователей, если такие есть
        for message_id in reversed(data['deal_chat_messages']):
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=message_id)
            except TelegramBadRequest:
                pass

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data.in_(['admin_edit_price', 'back_to_games']), StateFilter(default_state))
async def admin_edit_price(callback: CallbackQuery):  # TODO: изменить
    await callback.message.edit_text(LEXICON['edit_price_1'], reply_markup=Admin_kb.game_kb())


@router.message(F.text == '✏️ Изменить цену', StateFilter(default_state))
async def admin_edit_price(message: Message):
    await message.delete()
    await message.answer(LEXICON['edit_price_1'], reply_markup=Admin_kb.game_kb())


@router.callback_query(AdminGameFilter())
async def admin_game(callback: CallbackQuery):
    game = callback.data.split('_')[-1]
    projects_list = PROJECTS[game]

    await callback.message.edit_text(LEXICON['edit_price_2'].format(game),
                                     reply_markup=Admin_kb.projects_kb(game, projects_list))


@router.callback_query(F.data.startswith('admin_project'), StateFilter(default_state))
async def admin_project(callback: CallbackQuery):
    game = callback.data.split('_')[-2]
    project = callback.data.split('_')[-1]

    await callback.message.edit_text(LEXICON['edit_price_3'].format(game, project),
                                     reply_markup=Admin_kb.servers_kb(project))


@router.callback_query(F.data.startswith('change'), StateFilter(default_state))
async def admin_change(callback: CallbackQuery, state: FSMContext):
    _, project, server = callback.data.split('_')
    game = utils.determine_game(project)

    text = LEXICON['edit_price_4'].format(game, project, server)
    old_prices = get_old_prices(project, server)
    if old_prices:
        text += LEXICON['edit_price_old'].format(old_prices[0], old_prices[1])
    text += LEXICON['edit_price_buy']

    await callback.message.edit_text(text)
    await state.set_state(AdminStates.edit_price_buy)
    await state.update_data({'game': game, 'project': project, 'server': server})


@router.message(StateFilter(AdminStates.edit_price_buy))
async def edit_price_buy(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.answer('Неверный формат ввода. Цена должна быть целым числом. Попробуйте ещё раз')

    data = await state.get_data()

    game, project, server = data['game'], data['project'], data['server']
    text = LEXICON['edit_price_4'].format(game, project, server)

    old_prices = get_old_prices(project, server)

    if old_prices:
        text += LEXICON['edit_price_old'].format(old_prices[0], old_prices[1])
    text += LEXICON['edit_price_sell'].format(str(amount))

    await message.answer(text)

    data['new_buy'] = amount

    await state.set_state(AdminStates.edit_price_sell)
    await state.update_data(data)


@router.message(StateFilter(AdminStates.edit_price_sell))
async def edit_price_sell(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.answer('Неверный формат ввода. Цена должна быть целым числом. Попробуйте ещё раз')

    data = await state.get_data()

    game, project, server, new_buy = data['game'], data['project'], data['server'], data['new_buy']
    old_prices = get_old_prices(project, server)

    old_prices_text = LEXICON['edit_price_old'].format(old_prices[0], old_prices[1]) if old_prices else ''

    text = LEXICON['edit_price_confirm'].format(game, project, server, old_prices_text, new_buy, str(amount))

    await message.answer(text, reply_markup=Admin_kb.confirm_editing(project, server, new_buy, str(amount)))

    await state.clear()


@router.callback_query(F.data.startswith('c-e'), StateFilter(default_state))
async def insert_new_price(callback: CallbackQuery):
    if callback.data[3] == 'N':
        return callback.message.edit_text('🗑 Изменения отменены')

    _, project, server, buy, sell = callback.data.split('_')
    print(callback.data)

    add_prices(project, server, buy, sell)
    await callback.message.edit_text(LEXICON['price_edited'].format(buy, sell))


@router.callback_query(F.data.startswith('admin_ban_user'), StateFilter(default_state))
async def admin_ban_user_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    user_id = get_user_by_id(callback.data.split('_')[-1])[1]

    data['ban_user_message_mes_id'] = (
        await callback.message.edit_text(
            LEXICON['admin_ban_user_input_period'].format(user_id),
            reply_markup=Admin_kb.cancel_kb()
        )
    ).message_id

    data['user_id'] = int(user_id)
    await state.set_state(AdminStates.ban_input_period)
    await state.update_data(data)


# @router.message(StateFilter(AdminStates.ban_input_user_id))
# async def ban_user_id_handler(message: Message, state: FSMContext):
#     data = await state.get_data()
#
#     await bot.delete_message(message.chat.id, message.message_id)
#
#     if not message.text or not message.text.isdigit():
#         return await bot.edit_message_text(
#             LEXICON['admin_ban_user_input_id'] + LEXICON['text_needed'],
#             chat_id=message.chat.id, message_id=data['ban_user_message_mes_id'],
#             reply_markup=Admin_kb.cancel_kb()
#         )
#
#     if not get_user(int(message.text)):
#         return await bot.edit_message_text(
#             '🤕 Извините, но похоже, что пользователя с таким id не существует. Попробуйте ещё раз:',
#             chat_id=message.chat.id, message_id=data['ban_user_message_mes_id'],
#             reply_markup=Admin_kb.cancel_kb()
#         )


@router.message(StateFilter(AdminStates.ban_input_period))
async def ban_user_until_time_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if not message.text:
        return await bot.edit_message_text(
            LEXICON['admin_ban_user_input_period'] + LEXICON['text_needed'],
            chat_id=message.chat.id, message_id=data['ban_user_message_mes_id'],
            reply_markup=Admin_kb.cancel_kb()
        )

    period = utils.parse_time_to_hours(message.text)

    if not period:
        return await bot.edit_message_text(
            LEXICON['admin_ban_user_wrong_period_format'],
            chat_id=message.chat.id, message_id=data['ban_user_message_mes_id'],
            reply_markup=Admin_kb.cancel_kb()
        )

    await bot.edit_message_text(
        LEXICON['admin_ban_user_confirm'].format(data['user_id'], message.text),
        chat_id=message.chat.id, message_id=data['ban_user_message_mes_id'],
        reply_markup=Admin_kb.confirm_ban_kb()
    )

    data['period'] = period
    data['period_text'] = message.text

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data == 'confirm_ban')
async def confirm_ban_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if not all(key in data for key in ('ban_user_message_mes_id', 'period', 'period_text')):
        await callback.message.delete()
        return await callback.answer('Что-то пошло не так... Попробуйте ещё раз', show_alert=True)

    try:
        ban_user(data['user_id'], data['period'])
        period = get_ban_info(data['user_id'])[2]
        bot_user_id = get_bot_user_id(data['user_id'])

        if data['period'] != -1:
            await bot.send_message(data['user_id'], LEXICON['you_was_banned'].format(bot_user_id, period),
                                   reply_markup=User_kb.support_kb())
        else:
            await bot.send_message(data['user_id'], LEXICON['you_was_banned_forever'].format(bot_user_id),
                                   reply_markup=User_kb.support_kb())

        await bot.edit_message_text(
            LEXICON['admin_ban_user_confirmed'].format(get_bot_user_id(data['user_id']), data['period_text']),
            chat_id=callback.from_user.id, message_id=data['ban_user_message_mes_id']
        )

    except Exception as e:
        print(f'Ошибка при попытке бана пользователя: {str(e)}')

        await callback.message.delete()
        return await callback.answer('Что-то пошло не так... Попробуйте ещё раз', show_alert=True)


@router.callback_query(F.data.startswith('admin_unban_user'))
async def admin_unban_user_handler(callback: CallbackQuery):
    bot_user_id = callback.data.split('_')[-1]
    user_id = get_user_by_id(bot_user_id)[1]

    if unban_user(user_id):
        await bot.send_message(user_id, '✅ Вы были разбанены администрацией')
        await callback.message.edit_text(LEXICON['admin_unban_user_confirmed'].format(bot_user_id))
    else:
        await callback.message.edit_text('Что-то пошло не так')


@router.callback_query(F.data.contains('user_balance'))
async def top_up_user_balance_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    data['edition_text'] = 'пополнить' if callback.data.startswith('top_up') else 'сократить'
    bot_user_id = callback.data.split('_')[-1]

    mes = await callback.message.edit_text(
        text=LEXICON['admin_input_amount_to_edit'].format(data['edition_text'], bot_user_id),
        reply_markup=Admin_kb.back_to_inspection_user(bot_user_id)
    )

    data['edition_type'] = 'top-up' if callback.data.startswith('top_up') else 'reduce'
    data['admin_info_original_message_id'] = mes.message_id
    data['bot_user_id'] = int(bot_user_id)
    await state.set_state(AdminStates.input_amount_to_edit)
    await state.update_data(data)


@router.callback_query(F.data == 'back_to_entering_balance_change_amount')
async def back_to_entering_balance_change_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if not all(key in data for key in ('edition_type', 'admin_info_original_message_id', 'bot_user_id')):
        await callback.message.delete()
        await callback.answer('Эта кнопка устарела, попробуйте ещё раз.')
        return state.clear()

    await callback.message.edit_text(
        text=LEXICON['admin_input_amount_to_edit'].format(data['edition_text'], data['bot_user_id']),
        reply_markup=Admin_kb.back_to_inspection_user(data['bot_user_id'])
    )

    await state.set_state(AdminStates.input_amount_to_edit)
    await state.update_data(data)


@router.message(StateFilter(AdminStates.input_amount_to_edit))
async def input_amount_to_edit_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if not message.text:
        try:
            return await bot.edit_message_text(
                text=LEXICON['admin_input_amount_to_edit'].format(
                    data['edition_text'], data['bot_user_id']) + LEXICON['text_needed'],
                chat_id=message.chat.id, message_id=data['admin_info_original_message_id'],
                reply_markup=Admin_kb.back_to_inspection_user(data['bot_user_id'])
            )
        except TelegramBadRequest:
            return

    try:
        float(message.text.replace(' ', ''))  # проверка на ввод числа
    except ValueError:
        try:
            return await bot.edit_message_text(
                text=LEXICON['admin_input_amount_to_edit'].format(
                    data['edition_text'], data['bot_user_id']) + LEXICON['text_needed'],
                chat_id=message.chat.id, message_id=data['admin_info_original_message_id'],
                reply_markup=Admin_kb.back_to_inspection_user(data['bot_user_id'])
            )
        except TelegramBadRequest:
            pass

    await bot.edit_message_text(
        text=LEXICON['admin_edit_user_balance_confirm'].format(
            data['edition_text'], data['bot_user_id'], message.text),
        chat_id=message.chat.id, message_id=data['admin_info_original_message_id'],
        reply_markup=Admin_kb.confirmation_of_editing_user_balance(data['bot_user_id'], data['edition_type'],
                                                                   message.text)
    )

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data.startswith('confirm_balance_change'))
async def confirm_balance_change_handler(callback: CallbackQuery):
    _, _, _, bot_user_id, action, amount = callback.data.split('_')

    user_id = get_user_by_id(bot_user_id)[1]
    amount = amount.replace(' ', '')
    amount_to_edit = float(amount) if action == 'top-up' else float(amount) * (-1)
    income_action = 'loss' if action == 'top-up' else 'income'
    transaction_action = 'increase' if action == 'top-up' else 'reduction'
    action_text_user = 'пополнила' if action == 'top-up' else 'уменьшила'
    action_text_admin = 'пополнен' if action == 'top-up' else 'уменьшен'
    amount_text = '{:,}'.format(round(float(amount))).replace(',', ' ')

    try:
        edit_balance(user_id, amount_to_edit, transaction_action)
        add_income('user', user_id, income_action, float(amount))

        await bot.send_message(
            chat_id=user_id,
            text=LEXICON['notify_user_about_balance_changes'].format(action_text_user, amount_text)
        )
        await callback.message.edit_text(
            LEXICON['admin_confirmation_of_editing_balance'].format(bot_user_id, action_text_admin, amount_text),
            reply_markup=Admin_kb.back_to_inspection_user(bot_user_id)
        )

    except Exception as e:
        print(f'Ошибка при попытке изменение баланса пользователя: {str(e)}')


@router.callback_query(F.data.startswith('show_chat'))
async def interfere_in_chat_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    deal_id = callback.data.split('_')[-1]
    deal = get_deal(deal_id)
    chat_messages = await send_chat_logs(callback, int(deal_id))
    text = '<b>Выберите действие:</b>' if deal[5] == 'open' else '<b>Этот чат завершён</b>'

    await callback.message.answer(text, reply_markup=Admin_kb.interfere_in_chat_like_kb(deal_id, deal[5] == 'open'))

    await state.update_data(deal_chat_messages=chat_messages)


@router.callback_query(F.data.startswith('interfere_in_chat_confirm'))
async def interfere_in_chat_like_handler(callback: CallbackQuery, state: FSMContext):
    deal = get_deal(callback.data.split('_')[-1])

    await bot.send_message(chat_id=deal[1], text=LEXICON['admin_joined_chat'])
    await bot.send_message(chat_id=deal[3], text=LEXICON['admin_joined_chat'])

    data = {
        'in_chat_message_id': (
            await callback.message.edit_text(
                text='Для выхода из чата нажмите на кнопку снизу',
                reply_markup=Admin_kb.exit_chat()
            )
        ).message_id,
        'in_chat_with': [deal[1], deal[3]],
        'deal_id': deal[0]
    }

    for user_id in [deal[1], deal[3]]:
        user_state = FSMContext(storage, StorageKey(int(config.tg_bot.token.split(':')[0]), user_id, user_id))
        await user_state.update_data(admin_id=callback.from_user.id)

    await state.set_state(AdminStates.in_chat)
    await state.update_data(data)


@router.message(StateFilter(AdminStates.in_chat))
async def admin_in_chat_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    user_id = message.from_user.id

    if message.text:
        message_type = 'text'
        item = message.text
        caption = None

        if message.text.startswith('/'):
            await bot.delete_message(message.chat.id, message.message_id)
            alert = await message.answer('‼️ Во время сделки вы не можете использовать другой функционал')
            await asyncio.sleep(2)
            return await alert.delete()

    elif message.photo:
        message_type = 'photo'
        item = message.photo[0].file_id
        caption = message.caption if message.caption else ''

    elif message.video:
        message_type = 'video'
        item = message.video.file_id
        caption = message.caption if message.caption else ''

    elif message.sticker:
        message_type = 'sticker'
        item = message.sticker.file_id
        caption = None

    elif message.voice:
        message_type = 'voice'
        item = message.voice.file_id
        caption = message.caption if message.caption else '⠀'

    elif message.video_note:
        message_type = 'video_note'
        item = message.video_note.file_id
        caption = None

    elif message.animation:
        message_type = 'animation'
        item = message.animation.file_id
        caption = message.caption if message.caption else ''

    else:
        await bot.delete_message(message.chat.id, message.message_id)
        mes = await message.answer('Извините, на данный момент данный тип сообщений не поддерживается')
        await asyncio.sleep(2)
        return await mes.delete()

    send_method = {
        'photo': bot.send_photo,
        'video': bot.send_video,
        'sticker': bot.send_sticker,
        'voice': bot.send_voice,
        'video_note': bot.send_video_note,
        'animation': bot.send_animation,
    }

    for recipient_id in data['in_chat_with']:
        save_chat_message(data['deal_id'], user_id, recipient_id, message_type, item)

        if message.text:
            return await bot.send_message(recipient_id, f"🔹 Сообщение от администрации: {item}")

        if not caption:
            await bot.send_message(recipient_id, f"🔹 Сообщение от администрации:")
            await send_method[message_type](recipient_id, item)
        else:
            await send_method[message_type](recipient_id, item, caption=f'🔹 Сообщение от администрации: ' + caption)


@router.callback_query(F.data == 'exit_chat')
async def exit_chat_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id, message_id=callback.message.message_id,
        reply_markup=None
    )
    await callback.message.answer('Вы вышли из чата')

    await state.clear()


@router.callback_query(F.data.startswith('admin_cancel_deal'))
async def admin_cancel_deal_handler(callback: CallbackQuery):
    deal_id, buyer_id, buyer_order_id, seller_id, seller_order_id, status, created_at = get_deal(
        callback.data.split('_')[-1])

    buyer_state: FSMContext = utils.get_user_state(buyer_id)
    seller_state: FSMContext = utils.get_user_state(seller_id)

    buyer_data = await buyer_state.get_data()
    seller_data = await seller_state.get_data()

    if status != 'open':
        return await callback.message.edit_text(
            text=f'Эта сделка была {"завершена" if status == "confirmed" else "отменена"}',
            reply_markup=None
        )

    edit_balance(buyer_id, utils.get_price(seller_order_id, 'buy'), 'buy_canceled', deal_id=deal_id)
    delete_transaction(user_id=buyer_id, deal_id=deal_id)

    await bot.send_message(buyer_id, LEXICON['admin_canceled_deal_buyer'], reply_markup=User_kb.to_main_menu_hide_kb())
    await bot.send_message(seller_id, LEXICON['admin_canceled_deal_seller'],
                           reply_markup=User_kb.to_main_menu_hide_kb())

    await bot.edit_message_reply_markup(
        chat_id=buyer_id,
        message_id=buyer_data['in_chat_message_id'],
        reply_markup=None
    )
    await bot.edit_message_reply_markup(
        chat_id=seller_id,
        message_id=seller_data['in_chat_message_id'],
        reply_markup=None
    )

    await buyer_state.clear()
    await seller_state.clear()

    utils.deal_completion(deal_id, seller_order_id, buyer_order_id, 'canceled', 'confirmed')


@router.callback_query(F.data.startswith('admin_confirm_deal'))
async def admin_confirm_deal_handler(callback: CallbackQuery):
    deal_id, buyer_id, buyer_order_id, seller_id, seller_order_id, status, created_at = get_deal(
        callback.data.split('_')[-1])

    buyer_state = utils.get_user_state(buyer_id)
    seller_state = utils.get_user_state(seller_id)

    buyer_data = await buyer_state.get_data()
    seller_data = await seller_state.get_data()

    edit_balance(seller_id, utils.get_price(seller_order_id, 'sell'), 'sell', deal_id=deal_id)

    await bot.edit_message_reply_markup(chat_id=buyer_id, message_id=buyer_data['in_chat_message_id'],
                                        reply_markup=None)
    await bot.edit_message_reply_markup(chat_id=seller_id, message_id=seller_data['in_chat_message_id'],
                                        reply_markup=None)

    await bot.send_message(buyer_id, LEXICON['admin_canceled_deal_buyer'],
                           reply_markup=User_kb.to_main_menu_hide_kb())
    await bot.send_message(seller_id, LEXICON['admin_canceled_deal_seller'],
                           reply_markup=User_kb.to_main_menu_hide_kb())

    utils.deal_completion(deal_id, seller_order_id, buyer_order_id, 'confirmed', 'confirmed')


@router.message(F.text == buttons['turn_off'])
async def turn_off_handler(message: Message):
    set_technical_work(True)
    init_user_memory_db()

    await message.answer(LEXICON['admin_technical_worc_on'])


@router.message(F.text == buttons['turn_on'])
async def turn_off_handler(message: Message):
    set_technical_work(False)

    await message.answer(LEXICON['admin_technical_worc_off'])
    mes = await message.answer('<b>⏳ Начинаю оповещение пользователей...</b>')

    for user_id in get_remembered_user_ids():
        try:
            await bot.send_message(user_id, '<b>🟢 Бот снова запущен</b>')
        except TelegramBadRequest:
            pass

    await mes.edit_text('<b>✅ Пользователи оповещены</b>')

    delete_user_memory_table()


@router.message(F.text == buttons['newsletter'])
async def turn_off_handler(message: Message, state: FSMContext):
    mes = await message.answer(LEXICON['admin_input_newsletter'], reply_markup=Admin_kb.cancel_kb())

    await state.set_state(AdminStates.input_newsletter)
    await state.update_data(newsletter_message_id=mes.message_id)


@router.message(StateFilter(AdminStates.input_newsletter))
async def input_newsletter_handler(message: Message, state: FSMContext):
    await message.delete()

    if not (message.text or message.photo):
        return await message.answer(LEXICON['text_needed'])

    if message.photo:
        await bot.send_photo(
            chat_id=message.chat.id, photo=message.photo[0].file_id, caption=message.caption,
            reply_markup=Admin_kb.confirm_newsletter()
        )

    else:
        await message.answer(
            text=LEXICON['admin_confirm_newsletter'].format(message.text),
            reply_markup=Admin_kb.confirm_newsletter()
        )

    await state.clear()


@router.callback_query(F.data == 'confirm_newsletter')
async def confirm_newsletter_handler(callback: CallbackQuery):
    text = utils.extract_text_from_message(callback.message.text) if callback.message.text else None

    await callback.message.delete()
    mes = await callback.message.answer('⏳ Начинаю рассылку...')

    for user_id in get_all_user_ids():
        try:
            if callback.message.photo:
                await bot.send_photo(
                    chat_id=user_id, photo=callback.message.photo[0].file_id, caption=callback.message.caption
                )

            else:
                await bot.send_message(user_id, text)

        except TelegramBadRequest:
            pass

    await callback.message.answer('✅ Рассылка завершена!', reply_to_message_id=mes.message_id)
