import math
from idlelib.query import Query

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction

from aiogram import Bot, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.base import StorageKey

from core import *
from database import *
from filters import *
from keyboards import UserKeyboards as User_kb
from lexicon import *
from states import UserStates
import utils

config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)

router: Router = Router()

ADMIN_IDS = config.tg_bot.admin_ids


@router.message(Command('menu', 'start'), StateFilter(default_state))
async def start(message: Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    await message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())
    await state.clear()

    if not get_user(message.from_user.id):
        user = message.from_user
        phone_number = None
        database.add_user(user.id, user.username, phone_number)


@router.callback_query(F.data == 'back_to_menu', StateFilter(default_state))
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['start_message'], reply_markup=User_kb.start_kb())


@router.callback_query(F.data == 'shop_button', StateFilter(default_state))
async def shop_button(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['shop_message'], reply_markup=User_kb.shop_kb())


@router.callback_query(F.data == 'account_button', StateFilter(default_state))
async def account_button(callback: CallbackQuery):
    await utils.send_account_info(callback)


@router.callback_query(F.data == 'shop_buy_button', StateFilter(default_state))
async def start_buy_button(callback: CallbackQuery):
    await callback.message.edit_text(show_lexicon['item'], reply_markup=User_kb.action_kb('show'))


@router.callback_query(F.data == 'shop_sell_button', StateFilter(default_state))
async def start_sell_button(callback: CallbackQuery):
    await callback.message.edit_text(sell_lexicon['item'], reply_markup=User_kb.action_kb('sell'))


@router.callback_query(F.data == 'shop_create_order_button', StateFilter(default_state))
async def start_create_order_button(callback: CallbackQuery):
    await callback.message.edit_text(co_lexicon['game'], reply_markup=User_kb.co_game_kb())


@router.callback_query(F.data.startswith('co_game'), StateFilter(default_state))
async def co_game(callback: CallbackQuery):
    game = callback.data.split('_')[-1]
    await callback.message.edit_text(co_lexicon['project'], reply_markup=User_kb.co_project_kb(game))


@router.callback_query(F.data.startswith('co_project'), StateFilter(default_state))
async def co_project(callback: CallbackQuery):
    project = callback.data.split('_')[-1]
    await callback.message.edit_text(co_lexicon['server'].format(project), reply_markup=User_kb.co_server_kb(project))


@router.callback_query(F.data.startswith('co_server'), StateFilter(default_state))
async def co_server(callback: CallbackQuery):
    project, server = callback.data.split('_')[-2], callback.data.split('_')[-1]
    await callback.message.edit_text(co_lexicon['amount'].format(project, server),
                                     reply_markup=User_kb.co_amount_kb(project, server))


@router.callback_query(F.data.startswith('co_amount'), StateFilter(default_state))
async def co_amount(callback: CallbackQuery, state: FSMContext):
    _, _, project, server, amount = callback.data.split('_')

    if amount == 'custom':
        await callback.message.edit_text(co_lexicon['virt_custom'].format(project, server))
        await state.set_state(UserStates.input_amount)
        return await state.update_data({'project': project, 'server': server, 'action_type': 'buy'})

    price_ = utils.calculate_virt_price(amount, get_price_db(project, server, 'buy'))

    await callback.message.edit_text(
        text=LEXICON['confirm_text_virt'].format('Покупка', project, server, amount, price_),
        reply_markup=User_kb.confirmation_of_creation_kb('virt')
    )


@router.callback_query(F.data == 'shop_autoposter_discord_button', StateFilter(default_state))
async def autoposter_discord_button(callback: CallbackQuery):
    await callback.message.edit_text('Soon..', reply_markup=User_kb.back_to_start_kb())


@router.callback_query(F.data == 'back_to_shop', StateFilter(default_state))
async def back_to_shop(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['shop_message'], reply_markup=User_kb.shop_kb())


@router.callback_query(F.data.startswith('virt_'), StateFilter(default_state))
async def handle_virt_callback(callback: CallbackQuery):
    text = show_lexicon['game'].format('Вирта')
    if callback.data.split('_')[-1] == 'sell':
        text = sell_lexicon['game'].format('вирты')

    await callback.message.edit_text(
        text=text,
        reply_markup=User_kb.game_kb('virt', callback.data.split('_')[-1])
    )


@router.callback_query(F.data.startswith('business_'), StateFilter(default_state))
async def handle_business_callback(callback: CallbackQuery):
    text = show_lexicon['game'].format('Бизнес')
    if callback.data.split('_')[-1] == 'sell':
        text = sell_lexicon['game'].format('бизнеса')

    await callback.message.edit_text(
        text=text,
        reply_markup=User_kb.game_kb('business', callback.data.split('_')[-1])
    )


@router.callback_query(F.data.startswith('account_'), StateFilter(default_state))
async def handle_business_callback(callback: CallbackQuery):
    text = show_lexicon['game'].format('Аккаунт')
    if callback.data.split('_')[-1] == 'sell':
        text = sell_lexicon['game'].format('аккаунта')

    await callback.message.edit_text(
        text=text,
        reply_markup=User_kb.game_kb('account', callback.data.split('_')[-1])
    )


@router.callback_query(F.data.startswith('game_'), StateFilter(default_state))
async def game_callback_handler(callback: CallbackQuery):
    action_type = callback.data.split('_')[-1]
    game = callback.data.split('_')[1]
    item = callback.data.split('_')[2]

    await utils.show_projects(callback, item, game, action_type)


@router.callback_query(F.data.startswith('back_to_games_'), StateFilter(default_state))
async def back_to_games_callback(callback: CallbackQuery):
    item = callback.data.split('_')[-2]
    action_type = callback.data.split('_')[-1]

    text = show_lexicon['game'].format('Аккаунт')
    if action_type == 'sell':
        text = sell_lexicon['game'].format('аккаунта')

    await callback.message.edit_text(text, reply_markup=User_kb.game_kb(item, action_type))


@router.callback_query(F.data.startswith('project_'), StateFilter(default_state))
async def handle_project_callback(callback: CallbackQuery):
    item = callback.data.split('_')[1]
    project_name = callback.data.split('_')[2]
    action_type = callback.data.split('_')[-1]

    await utils.show_servers(callback, item, project_name, action_type)


@router.callback_query(F.data.startswith('back_to_projects_'), StateFilter(default_state))
async def handle_main_menu_callback(callback: CallbackQuery):
    _, _, _, item, game, action_type = callback.data.split('_')

    await utils.show_projects(callback, item, game, action_type)


@router.callback_query(F.data.startswith('back_to_servers'), StateFilter(default_state))
async def back_to_servers_handler(callback: CallbackQuery):
    project_name = callback.data.split('_')[3]
    action_type = callback.data.split('_')[-1]

    await utils.show_servers(callback, 'virt', project_name, action_type)


@router.callback_query(F.data.startswith('back_to_'), StateFilter(default_state))
async def back_to_handler(callback: CallbackQuery):
    destination = callback.data.split('_')[-1]

    if destination == 'buy':
        await start_create_order_button(callback)
    elif destination == 'sell':
        await start_sell_button(callback)
    elif destination == 'show':
        await start_buy_button(callback)


@router.callback_query(F.data.startswith('server_'), ~F.data.endswith('show'), StateFilter(default_state))
async def handle_server_callback(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, action_type = callback.data.split('_')
    text = sell_lexicon['special_1'].format(utils.get_item_for_sell_text(item), utils.determine_game(project),
                                            project, server, '{}')

    if item == 'virt':
        return await callback.message.edit_text(text.format(sell_lexicon['virt_1']),
                                                reply_markup=User_kb.amount_kb(project, server, action_type))
    elif item == 'business':
        await callback.message.edit_text(text.format(LEXICON['input_business_name']))
        await state.set_state(UserStates.input_business_name)
    elif item == 'account':
        await callback.message.edit_text(text.format(LEXICON['input_account_description']))
        await state.set_state(UserStates.input_account_description)
    await state.update_data({'project': project, 'server': server, 'action_type': action_type})


@router.callback_query(F.data.startswith('server_'), F.data.endswith('show'), StateFilter(default_state))
async def handle_server_show_callback(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, _ = callback.data.split('_')

    await utils.show_orders(callback, state, item, project, server)


@router.callback_query(F.data.startswith('watch-other'))
async def watch_other_handler(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, _ = callback.data.split('_')

    await utils.show_orders(callback, state, item, project, server, True, callback.data.split('_')[-1])


@router.callback_query(F.data.startswith('amount_'), StateFilter(default_state))
async def handle_amount_callback(callback: CallbackQuery, state: FSMContext):
    _, amount, project, server = callback.data.split('_')

    if amount == 'custom':
        await callback.message.edit_text("Введите нужное количество виртуальной валюты:")
        await state.set_state(UserStates.input_amount)
        await state.update_data({'project': project, 'server': server, 'action_type': 'sell'})

    else:
        price_ = utils.calculate_virt_price(amount, get_price_db(project, server, 'sell'))
        price_, amount = '{:,}'.format(price_), '{:,}'.format(int(amount))

        await callback.message.edit_text(
            text=LEXICON['confirm_text_virt'].format('Продажа', project, server, amount, price_),
            reply_markup=User_kb.confirmation_of_creation_kb('virt')
        )


@router.message(StateFilter(UserStates.input_amount))
async def input_amount(message: Message, state: FSMContext):
    amount = message.text
    if amount.isnumeric() and 500000 <= int(amount) <= 100000000000:
        data = await state.get_data()
        cost = get_price_db(data['project'], data['server'], data['action_type'])
        cost, amount = '{:,}'.format(cost), '{:,}'.format(amount)

        action_text = 'Покупка' if data['action_type'] == 'buy' else 'Продажа'

        await message.answer(
            text=LEXICON['confirm_text_virt'].format(action_text, data['project'], data['server'], amount, cost),
            reply_markup=User_kb.confirmation_of_creation_kb('virt')
        )
        await state.clear()

    else:
        await message.answer('Неверный формат ввода. Попробуйте ещё раз.', reply_markup=User_kb.cancel_kb())


@router.message(StateFilter(UserStates.input_business_name))
async def business_name(message: Message, state: FSMContext):
    data = await state.get_data()
    mes = await message.answer(LEXICON['input_business_price'], reply_markup=User_kb.cancel_kb())
    data['message'] = mes
    data['name'] = message.text
    await state.set_state(UserStates.input_business_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_business_price))
async def business_price(message: Message, state: FSMContext):
    try:
        price_ = int(message.text)
    except ValueError:
        return await message.answer('Цена должна быть числом', reply_markup=User_kb.cancel_kb())

    data = await state.get_data()
    mes: Message = data['message']
    await mes.edit_text(mes.text)
    await message.answer(
        text=LEXICON['confirm_text_business'].format(data['project'], data['server'], data['name'], price_),
        reply_markup=User_kb.confirmation_of_creation_kb('business')
    )
    await state.clear()


@router.message(StateFilter(UserStates.input_account_description))
async def account_description(message: Message, state: FSMContext):
    data = await state.get_data()
    data['description'] = message.text
    await message.answer(LEXICON['input_account_price'], reply_markup=User_kb.cancel_kb())
    await state.set_state(UserStates.input_account_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_account_price))
async def account_price(message: Message, state: FSMContext):
    try:
        price_ = int(message.text)
    except ValueError:
        return await message.answer('Цена должна быть числом')

    data = await state.get_data()
    await message.answer(
        text=LEXICON['confirm_text_account'].format(data['project'], data['server'], data['description'], price_),
        reply_markup=User_kb.confirmation_of_creation_kb('account')
    )
    await state.clear()


@router.callback_query(F.data == 'cancel_button',
                       StateFilter(UserStates.input_business_name, UserStates.input_account_description))
async def cancel_button_order_creation(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('🗑 Составление заказа отменено')
    await state.clear()


@router.callback_query(F.data.startswith('confirmation_of_creation_'), StateFilter(default_state))
async def handle_confirm_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action_type = callback.data.split('_')[-1]

    if action_type == 'confirm':
        username = callback.from_user.username
        item = callback.data.split('_')[-2]

        if item == 'virt':
            data = utils.parse_message_virt(callback.message.text)
            if not data:
                return await callback.message.edit_text("Кажется, что-то пошло не так...")
            action_text, project, server, amount, price_ = data.values()
            action_type = 'sell' if action_text == 'Продать' else 'buy'

            if action_type == 'buy' and get_balance(user_id) < price_:
                return await callback.message.edit_text('Недостаточно средств')

            order_id = add_order(user_id, username, action_type, item, project, server, amount, price_)

            await callback.message.edit_text("✅ Ваш заказ подтвержден и сохранен. Ожидайте ответа.")

            matched_order = match_orders(user_id, action_type, project, server, amount)
            if matched_order:
                matched_order_id, other_user_id = matched_order

                buyer_id = user_id if action_type == 'buy' else other_user_id
                seller_id = user_id if action_type == 'sell' else other_user_id
                buyer_order_id = order_id if action_type == 'buy' else matched_order_id
                seller_order_id = order_id if action_type == 'sell' else matched_order_id
                matched_orders_id = create_matched_order(buyer_id, buyer_order_id, seller_id, seller_order_id)

                await utils.notify_users_of_chat(bot, matched_orders_id, buyer_id, seller_id, order_id)

                database.update_order_status(buyer_order_id, 'matched')
                database.update_order_status(seller_order_id, 'matched')

        elif item == 'business':
            data = utils.parse_message_business(callback.message.text)
            if not data:
                return await callback.message.edit_text("Кажется, что-то пошло не так...")

            project, server, name, price_ = data.values()
            add_order(user_id, username, 'sell', item, project, server, price_, name)

            await callback.message.edit_text("✅ Ваш заказ подтвержден и сохранен. Ожидайте ответа.")

        else:
            data = utils.parse_message_account(callback.message.text)
            if not data:
                return await callback.message.edit_text("Кажется, что-то пошло не так...")

            project, server, description, price_ = data.values()
            add_order(user_id, username, 'sell', item, project, server, price_, description)

            await callback.message.edit_text("✅ Ваш заказ подтвержден и сохранен. Ожидайте ответа.")

    else:
        await callback.message.edit_text("🚫 Ваш заказ отменен.")


@router.callback_query(F.data.startswith('report_'), StateFilter(UserStates.in_chat))
async def report_callback(callback: CallbackQuery, state: FSMContext):
    if await state.get_data() == UserStates.waiting_for_problem_description:
        return await callback.answer()
    _, offender_id, order_id = callback.data.split('_')

    user_data.setdefault(callback.from_user.id, {})
    user_data[callback.from_user.id]['complaint'] = {}
    user_data[callback.from_user.id]['complaint']['offender_id'] = offender_id
    user_data[callback.from_user.id]['complaint']['order_id'] = order_id
    await state.set_state(UserStates.waiting_for_problem_description)

    await callback.message.answer('📝 Пожалуйста, опишите подробно суть проблемы:')


@router.callback_query(F.data.startswith('confirmation_of_deal'))
async def handle_chat_action_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split('_')[-2]
    chat_id = active_chats[user_id]
    buyer_id, seller_id = map(int, chat_id.split('_'))
    other_user_id = buyer_id if user_id == seller_id else seller_id
    seller_order_id = get_matched_order(int(callback.data.split('_')[-1]))[4]
    buyer_order_id = get_matched_order(int(callback.data.split('_')[-1]))[2]

    if action == 'cancel':
        cancel_requests[chat_id][user_id] = True
        await callback.answer()

        if user_id == seller_id:
            del active_chats[buyer_id]
            del active_chats[seller_id]

            buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
            seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

            await buyer_state.clear()
            await seller_state.clear()

            edit_balance(buyer_id, utils.get_price(seller_order_id, 'buy'))

            await bot.send_message(buyer_id, "🚫 Сделка отменена продавцом.")
            await bot.send_message(seller_id, "🚫 Сделка отменена.")

            try:
                await bot.delete_message(buyer_id, cancel_requests[chat_id]['buyer_message_id'])
            except Exception:
                pass
            del cancel_requests[chat_id]

            try:
                update_order_status(seller_order_id, 'pending')
                if buyer_order_id != 0:
                    update_order_status(buyer_order_id, 'pending')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'deleted': {e}")

        else:
            await bot.send_message(user_id, "‼️ Вы хотите отменить сделку. Ожидайте подтверждения от продавца.")
            await bot.send_message(other_user_id, "‼️ Покупатель хочет отменить сделку. Если вы хотите отменить "
                                                  "сделку, нажмите 'Отменить сделку'.")

            if cancel_requests[chat_id][other_user_id]:
                edit_balance(buyer_id, utils.get_price(seller_order_id, 'buy'))

                del active_chats[buyer_id]
                del active_chats[seller_id]

                await bot.send_message(buyer_id, "🚫 Сделка отменена.")
                await bot.send_message(seller_id, "🚫 Сделка отменена.")

                buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
                seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

                await buyer_state.clear()
                await seller_state.clear()

                await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])
                del cancel_requests[chat_id]

                try:
                    update_order_status(seller_order_id, 'pending')
                    if buyer_order_id != 0:
                        update_order_status(buyer_order_id, 'pending')
                except sqlite3.Error as e:
                    print(f"Error updating order status to 'deleted': {e}")

    elif action == 'confirm':
        if user_id == buyer_id:
            edit_balance(seller_id, utils.get_price(seller_order_id, 'sell'))

            cancel_requests[chat_id][user_id] = True

            await bot.delete_message(buyer_id, callback.message.message_id)
            await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])

            await bot.send_message(buyer_id, "✅ Сделка подтверждена вами.")
            await bot.send_message(seller_id, "✅ Покупатель подтвердил сделку. Сделка завершена.")

            try:
                update_order_status(seller_order_id, 'confirmed')
                if buyer_order_id != 0:
                    update_order_status(buyer_order_id, 'confirmed')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'confirmed': {e}")

            del active_chats[buyer_id]
            del active_chats[seller_id]
            del cancel_requests[chat_id]

            buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
            seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

            await buyer_state.clear()
            await seller_state.clear()


@router.message(StateFilter(UserStates.in_chat))
async def handle_chat_message(message: Message):
    user_id = message.from_user.id
    chat_id = active_chats[user_id]
    buyer_id, seller_id = map(int, chat_id.split('_'))
    recipient_id = buyer_id if user_id == seller_id else seller_id

    bot_user_id = get_bot_user_id(user_id)
    save_chat_message(chat_id, user_id, recipient_id, message.text)

    await bot.send_message(recipient_id, f"Сообщение от ID {bot_user_id}: {message.text}")


@router.message(Command('account'))
async def account_info(message: Message):
    await utils.send_account_info(message)


@router.callback_query(F.data == 'my_orders', StateFilter(default_state))
async def process_my_orders(callback: CallbackQuery):
    await callback.answer()
    orders = get_orders_by_user_id(callback.from_user.id)

    if orders:
        for order in orders:
            order_id, _, _, action, item, project, server, amount, description, price, status, created_at = order
            action_text = 'Продажа' if action == 'sell' else 'Покупка'
            item_text = 'Вирты' if item == 'virt' else 'Бизнес' if item == 'business' else 'Аккаунт'
            status_text = 'Создано 🌀' if status == 'pending' else ''
            if item == 'virt':
                aditional = LEXICON['aditional_virt'].format('{0:,}'.format(int(amount)))
            elif item == 'business':
                aditional = LEXICON['aditional_business'].format(description)
            else:
                aditional = LEXICON['aditional_account'].format(description)

            await callback.message.edit_text(
                LEXICON['my_orders_message'].format(order_id, created_at, status_text, action_text, item_text, project,
                                                    server,
                                                    '{0:,}'.format(int(price)), aditional))
    else:
        await callback.message.answer("🤕 У вас пока нет ордеров.")


@router.callback_query(F.data == 'complaints_button')
async def handle_complaints_button(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['report_message'], reply_markup=User_kb.report_kb())


@router.message(Command('report'))
async def report_command(message: Message):
    await message.answer(LEXICON['report_message'], reply_markup=User_kb.report_kb())


@router.callback_query(F.data == 'write_ticket')
async def process_write_ticket_callback(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    if get_user_matched_orders(callback.from_user.id):
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await callback.message.answer("Введите ID сделки (только числом), по которому хотите написать жалобу:",
                                      reply_markup=User_kb.cancel_kb())

        await state.set_state(UserStates.waiting_for_order_id)
        user_data.setdefault(callback.from_user.id, {})
        user_data[callback.from_user.id]['complaint'] = {}

    else:
        return await callback.message.edit_text('🤕 Похоже, у Вас ещё нет совершённых сделок')


@router.callback_query(F.data == 'my_tickets')
async def process_my_tickets_callback(callback: CallbackQuery):
    reports = complaints(callback.from_user.id)

    if not reports:
        return await callback.message.edit_text('У вас ещё нет жалоб')

    text = ''
    for report in reports:
        text += LEXICON['report'].format(*report)

    await callback.message.edit_text(text)


@router.message(StateFilter(UserStates.waiting_for_order_id))
async def process_order_id(message: Message, state: FSMContext):
    try:
        order_id = int(message.text.strip())
    except ValueError:
        return await message.answer("❔ Я не могу найти сделку с таким ID, может вы ошиблись?")

    if not check_matched_order(order_id, message.from_user.id):
        return await message.answer("У вас не было сделки с данным ID, попробуйте еще раз",
                                    reply_markup=User_kb.cancel_kb())

    user_data[message.from_user.id]['complaint']['order_id'] = order_id
    await state.set_state(UserStates.waiting_for_problem_description)

    await message.answer("Теперь подробно изложите суть проблемы:")


@router.callback_query(F.data == 'cancel_button', StateFilter(UserStates.waiting_for_problem_description))
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    await state.clear()
    await callback.message.edit_text('🗑 Отправка жалобы отменена')


@router.message(StateFilter(UserStates.waiting_for_problem_description))
async def process_problem_description(message: Message):
    complaint_text = message.text
    user_data[message.from_user.id]['complaint']['complaint_text'] = complaint_text

    await message.answer("Выберите действие:", reply_markup=User_kb.send_report_kb())


@router.callback_query(F.data.in_(['send_ticket', 'cancel_ticket']))
async def process_ticket_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == 'send_ticket':
        try:
            order_id = user_data[callback.from_user.id]['complaint']['order_id']
            complaint = get_matched_order(order_id)
            complainer_id = callback.from_user.id
            offender_id = complaint[1] if complaint[1] != complainer_id else complaint[3]
            complaint = user_data[callback.from_user.id]['complaint']['complaint_text']
            create_report(order_id, complainer_id, offender_id, complaint)

            await callback.message.edit_text(
                "✅ Тикет успешно отправлен. Пожалуйста, дождитесь ответа от администратора")
            await state.clear()

            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, '‼️ Поступил репорт\n/admin')
                except Exception as e:
                    print(f'Ошибка при попытке оповещения админа о новой жалобе: {str(e)}')

        except Exception as e:
            await callback.message.answer("❔ Что-то пошло не так. Пожалуйста, свяжитесь с поддержкой напрямую")
            print(e, datetime.datetime.now().time(), sep='\n')

    elif callback.data == 'cancel_ticket':
        user_data[callback.from_user.id]['complaint'] = {}
        await callback.message.edit_text("Вы отменили создание тикета.")


@router.message(Command('help'), StateFilter(default_state))
async def help_command(message: Message):
    await message.answer(LEXICON['help_message'])


@router.message(Command('myorders'), StateFilter(default_state))
async def my_orders_command(message: Message):
    orders = get_orders_by_user_id(message.from_user.id)

    if orders:
        for order in orders:
            order_id, _, _, action, item, project, server, amount, description, price, status, created_at = order
            action_text = 'Продажа' if action == 'sell' else 'Покупка'
            item_text = 'Вирты' if item == 'virt' else 'Бизнес' if item == 'business' else 'Аккаунт'
            status_text = 'Создано 🌀' if status == 'pending' else ''
            if item == 'virt':
                aditional = LEXICON['aditional_virt'].format('{0:,}'.format(int(amount)))
            elif item == 'business':
                aditional = LEXICON['aditional_business'].format(description)
            else:
                aditional = LEXICON['aditional_account'].format(description)

            await message.answer(
                LEXICON['my_orders_message'].format(order_id, created_at, status_text, action_text, item_text, project,
                                                    server,
                                                    '{0:,}'.format(int(price)), aditional))

    else:
        await message.answer("❔ У вас пока нет ордеров.")


@router.callback_query(F.data == 'support_button', StateFilter(default_state))
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['support_message'], reply_markup=User_kb.support_kb())


@router.message(Command('support'))
async def support_command(message: Message):
    await message.answer(LEXICON['support_message'], reply_markup=User_kb.support_kb())


@router.callback_query(F.data == 'contact_support', StateFilter(default_state))
async def contact_support_handler(callback: CallbackQuery):
    await callback.message.edit_text('текст')


@router.message(Command('info'), StateFilter(default_state))
async def info_command(message: Message):
    await message.answer(LEXICON['info_message'])


@router.callback_query(F.data.startswith('buy_order_'), StateFilter(default_state))
async def buy_order(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]

    if utils.get_price(order_id, 'buy') > get_balance(callback.from_user.id):
        await callback.answer()
        return await callback.message.answer(f'Недостаточно средств')

    await callback.message.edit_text(
        text=callback.message.text + '\n\n🤔 Вы уверены?',
        reply_markup=User_kb.buy_order_kb(order_id)
    )


@router.callback_query(F.data.startswith('confirmation_of_buying_'), StateFilter(default_state))
async def confirmation_of_buying(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]

    if utils.get_price(order_id, 'buy') > get_balance(callback.from_user.id):
        await callback.answer()
        return await callback.message.answer('Недостаточно средств')

    buyer_id = callback.from_user.id
    edit_balance(buyer_id, -utils.get_price(order_id, 'buy'))

    seller_id = get_user_id_by_order(order_id)
    matched_orders_id = create_matched_order(buyer_id, 0, seller_id, int(order_id))

    await callback.message.edit_text(callback.message.text[:-13] + '✅ Начался чат с продавцом')
    await utils.notify_users_of_chat(bot, matched_orders_id, buyer_id, seller_id, order_id)


def todo() -> None:
    # TODO: починить репорты (админу высылается список, в котором на 1 и тот же Id могут быть 2 разные жалобы)

    # TODO: /admin
    #       Вместе с username пользователей выводи user id обоих, выводи время создание репорта и добавь кнопки:
    #       Ответить, закрыть, забанить 1д,7д,30д, навсегда,
    #       Кнока присоединения к переписке (сделай возможность выходить из нее),
    #       Кнопки подветрждения и отмена сделки. + Кнопки с необходимой инфой.
    #       С инфой об самом ордере, об обоих пользователях, переписка.

    # TODO: Главное меню - /start /menu (ВАЖНО! ЦЕНА ДЛЯ ПОКУПКИ БУДЕТ ВЫШЕ ЦЕНЫ ДЛЯ ПРОДАЖИ НА 30%)
    #       Выводится одно полное сообщение-приветствие с прикрепленными кнопками - Купить Продать Создать заявку
    #       (Автопостер Discord, в разработке)
    #       Купить - работает кнопка по аналогии (/orders /ordersbiz /ordersacc) Выбор покупки чего
    #       Виртуальная валюта, Бизнес, Аккаунт. И далее по накатанной
    #       Продать - создание ордера. Выбор продажи чего Виртуальная валюта, Бизнес, Аккаунт.
    #       Бизнес - ввод платформы, проекта, описание(пользовательское), цена (пользовательская), подтверждение.
    #       Аккаунт - ввод платформы, проекта, сервера, описание(пользовательское),
    #       цена (пользовательская), подтверждение.
    #       Виртуальная валюта - ввод платформы, проекта, сервера, кол-во валюты, подтверждение.

    # TODO: Баланс, платежка

    # TODO: если пользователю напишут во время другого чата

    pass
