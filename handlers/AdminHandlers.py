import asyncio

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction

from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from core import *
from database import *
from filters import *
from keyboards import AdminKeyboards as Admin_kb, UserKeyboards as User_kb
from lexicon import *
from states import AdminStates
import utils
from utils.admin_messages import send_information

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

    await message.answer(LEXICON['admin_menu'].format(
        income='в разработке',
        users_number=count_users(),
        active_orders_number=count_active_orders(),
        active_deals_number=count_active_deals()
    ),
        reply_markup=Admin_kb.menu_kb())


@router.callback_query(F.data == 'back_to_admin_menu', StateFilter(default_state))
async def back_to_menu(callback: CallbackQuery):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    await callback.message.edit_text(f'Здравствуйте, {callback.from_user.first_name}! 😊',
                                     reply_markup=Admin_kb.menu_kb())


@router.callback_query(F.data == 'admin_reports', StateFilter(default_state))
async def admin_reports(callback: CallbackQuery):
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
async def admin_information(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    await callback.message.edit_text('Выберите критерий поиска:', reply_markup=Admin_kb.information_kb())
    await state.clear()


@router.callback_query(F.data.startswith('admin_information'), StateFilter(default_state))
async def admin_information_by(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    argument = target_map.get(callback.data.split('_')[-1])

    data = {
        'target': callback.data.split('_')[-1],
        'admin_information_message_mes_id': (
            await callback.message.edit_text(LEXICON['admin_information'].format(argument),
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

    if not await send_information(data['target'], target_id, message.chat.id, data['admin_information_message_mes_id']):
        await state.clear()
        await state.update_data(data)


@router.callback_query(F.data.startswith('send_information_about'))
async def send_information_about_handler(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    _, _, _, target, target_id = callback.data.split('_')

    await send_information(target, target_id, callback.from_user.id, callback.message.message_id)


@router.callback_query(F.data.in_(['admin_edit_price', 'back_to_games']), StateFilter(default_state))
async def admin_edit_price(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['edit_price_1'], reply_markup=Admin_kb.game_kb())


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

    user_id = callback.data.split('_')[-1]

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
async def ban_user_for_yime_handler(message: Message, state: FSMContext):
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

        await bot.edit_message_text(
            LEXICON['admin_ban_user_confirmed'].format(data['user_id'], data['period_text']),
            chat_id=callback.from_user.id, message_id=data['ban_user_message_mes_id']
        )

        await bot.send_message(data['user_id'], f'Вас забанили на {data["period_text"]}')

    except Exception as e:
        print(f'Ошибка при попытке бана пользователя: {str(e)}')

        await callback.message.delete()
        return await callback.answer('Что-то пошло не так... Попробуйте ещё раз', show_alert=True)
