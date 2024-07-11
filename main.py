import datetime
import logging
import asyncio
import sqlite3
import math

import database

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from database import *
from states import UserState
from utils import convert_datetime

admin_id = 853603010
logging.basicConfig(level=logging.INFO)

TOKEN = '7488450312:AAEdwH49J-QJ9xCRQvJz8qsNC1hesY_dFoI'

storage: MemoryStorage = MemoryStorage()

bot: Bot = Bot(token=TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

database.init_db()
action_cb = CallbackData('action', 'type')
project_cb = CallbackData('project', 'name')
server_cb = CallbackData('server', 'name')
orders_servers_cb = CallbackData('orders_servers', 'name')
main_menu_cb = CallbackData('main_menu', 'action')
amount_cb = CallbackData('amount', 'value')
orders_amount_cb = CallbackData('orders_amount', 'value')
confirm_cb = CallbackData('confirm', 'action')

GTA5RP_SERVERS = [
    'Downtown', 'Strawberry', 'Vinewood', 'Blackberry', 'inquad',
    'Sunrise', 'Rainbow', 'Richman', 'Eclipse', 'La Mesa', 'Burton',
    'Rockford', 'Alta', 'Del Perro', 'Davis', 'Harmony', 'Redwood',
    'Hawick', 'Grapeseed'
]

MAJESTIC_SERVERS = [
    'New York', 'Detroit', 'Chicago', 'San Francisco', 'Atlanta',
    'San Diego', 'Los Angeles', 'Miami', 'Las Vegas', 'Washington', 'Dallas'
]

RADMIR_SERVERS = ['1', '2', '3']

user_data = {}
user_states = {}
active_chats = {}
cancel_requests = {}

PRICE_PER_MILLION_VIRTS = {
    'GTA5RP': {'buy': 1600, 'sell': 1000},
    'Majestic': {'buy': 700, 'sell': 400},
    'Radmir GTA5': {'buy': 300, 'sell': 100}
}


@dp.message_handler(commands=['start'])
async def start(message: Message):
    user = message.from_user
    phone_number = None
    database.add_user(user.id, user.username, phone_number)
    await message.reply(
        "Я - ваш личный помощник, который поможет вам быстро и легко приобрести нужные виртуальные товары.\n\n"
        "Перед началом рекомендую ознакомиться с моими функциями во избежания ошибок.\n"
        "Помните, что  валюту вы покупаете не у меня, а у других пользователей, которые так же хотят продать свои виртуальные товары. И наоборот.\n\n"
        "Я лишь создаю условия, при которых вы можете безопасно проводить сделки и исключаю вашу возможность быть обманутым."
    )

    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton(text="Купить вирты", callback_data=action_cb.new(type='buy')),
        InlineKeyboardButton(text="Продать вирты", callback_data=action_cb.new(type='sell')),
        InlineKeyboardButton(text='что-то', callback_data='dfghjk,mv'),
        InlineKeyboardButton(text='few', callback_data='qwdqjh'),
        InlineKeyboardButton(text='few', callback_data='qwdqjh'),
        InlineKeyboardButton(text='few', callback_data='qwdqjh')
    ]
    keyboard.add(*buttons)

    await message.answer(
        "Для того, чтобы создать заявку на покупку или продажу действуйте в рамках инструкций, которые я буду вам показывать.\n"
        "Я помогу вам заполнить заявку.\n"
        "Выберите действие:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == '/admin' and message.from_user.id in [admin_id, 922787101])
async def admin(message: Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="📢 Репорты", callback_data='admin_reports'),
        InlineKeyboardButton(text='💸 Транзакции', callback_data='admin_transactions'),  # TODO: доделать кнопку
        InlineKeyboardButton(text='👨‍💻 Поддержка', callback_data='admin_support'),  # TODO: доделать кнопку
        InlineKeyboardButton(text='ℹ️ Информация', callback_data='admin_information')  # TODO: доделать кнопку
    )

    await message.answer(f'Здравствуйте, {message.from_user.username}! 😊', reply_markup=kb)


@dp.callback_query_handler(action_cb.filter(type=['buy', 'sell']))
async def handle_action_callback(callback: CallbackQuery, callback_data: dict):
    user_id = callback.from_user.id
    action_type = callback_data['type']
    user_data[user_id] = {'action': action_type}

    await callback.message.delete()

    if action_type == 'buy':
        action_text = "приобрести"
    elif action_type == 'sell':
        action_text = "продать"
    else:
        action_text = ""

    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton(text="GTA5RP", callback_data=project_cb.new(name='GTA5RP')),
        InlineKeyboardButton(text="Majestic", callback_data=project_cb.new(name='Majestic')),
        InlineKeyboardButton(text="Radmir GTA5", callback_data=project_cb.new(name='Radmir GTA5'))
    ]
    keyboard.add(*buttons)

    await callback.message.answer(f"Выберите проект на котором хотите {action_text} виртуальную валюту.",
                                  reply_markup=keyboard)
    await callback.answer()


@dp.callback_query_handler(project_cb.filter(name=['GTA5RP', 'Majestic', 'Radmir GTA5']))
async def handle_project_callback(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id
    project_name = callback_data['name']
    action_type = user_data[user_id]['action']

    user_data[user_id]['project'] = project_name

    if project_name == 'GTA5RP':
        servers = GTA5RP_SERVERS
    elif project_name == 'Majestic':
        servers = MAJESTIC_SERVERS
    elif project_name == 'Radmir GTA5':
        servers = RADMIR_SERVERS
    else:
        await query.message.edit_text("Ошибка: проект не найден.")
        await query.answer()
        return

    action_text = "покупки" if action_type == 'buy' else "продажи"

    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=server, callback_data=server_cb.new(name=server)) for server in servers]
    keyboard.add(*buttons)

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=main_menu_cb.new(action='main_menu')))

    await query.message.edit_text(
        f"Вы выбрали проект {project_name}. Выберите сервер для {action_text} виртуальной валюты:",
        reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(main_menu_cb.filter(action='main_menu'))
async def handle_main_menu_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action_type = user_data[user_id]['action']

    action_text = "приобрести" if action_type == 'buy' else "продать"

    keyboard = InlineKeyboardMarkup(row_width=3)
    projects = ['GTA5RP', 'Majestic', 'Radmir GTA5']
    buttons = [InlineKeyboardButton(text=project, callback_data=project_cb.new(name=project)) for project in projects]
    keyboard.add(*buttons)

    await callback.message.edit_text(
        f"Выберите проект на котором хотите {action_text} виртуальную валюту.",
        reply_markup=keyboard)


@dp.callback_query_handler(server_cb.filter())
async def handle_server_callback(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id
    server_name = callback_data['name']
    user_data[user_id]['server'] = server_name
    action_type = user_data[user_id]['action']
    project_name = user_data[user_id]['project']

    if server_name == 'Другое количество':
        await bot.send_message(query.from_user.id, "Введите нужное количество виртов:")
        await query.message.delete()
    else:
        keyboard = InlineKeyboardMarkup(row_width=2)
        buttons = [
            InlineKeyboardButton(text="1.000.000", callback_data=amount_cb.new(value='1000000')),
            InlineKeyboardButton(text="1.500.000", callback_data=amount_cb.new(value='1500000')),
            InlineKeyboardButton(text="2.000.000", callback_data=amount_cb.new(value='2000000')),
            InlineKeyboardButton(text="3.000.000", callback_data=amount_cb.new(value='3000000')),
            InlineKeyboardButton(text="5.000.000", callback_data=amount_cb.new(value='5000000')),
            InlineKeyboardButton(text="10.000.000", callback_data=amount_cb.new(value='10000000')),
            InlineKeyboardButton(text="Другое количество", callback_data=amount_cb.new(value='custom'))
        ]
        keyboard.add(*buttons)

        action_text = "приобрести" if action_type == 'buy' else "продать"
        await query.message.edit_text(
            f"Вы выбрали проект {project_name}, сервер {server_name}. Теперь выберите количество виртуальной валюты, которое хотите {action_text}:",
            reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(amount_cb.filter())
async def handle_amount_callback(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id
    amount_value = callback_data['value']

    if amount_value == 'custom':
        await bot.send_message(query.from_user.id, "Введите нужное количество виртуальной валюты:")
        await query.message.delete()
    else:
        amount = int(amount_value)
        if amount < 500000 or amount > 1000000000000:
            await bot.send_message(user_id,
                                   "Количество виртуальной валюты должно быть от 500,000")
            await query.answer()
            return

        user_data[user_id]['amount'] = amount

        action_type = user_data[user_id]['action']
        project = user_data[user_id]['project']
        server = user_data[user_id]['server']
        price_per_million = PRICE_PER_MILLION_VIRTS[project][action_type.lower()]
        price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))

        if action_type == 'buy':
            action_text = "Купить"
        elif action_type == 'sell':
            action_text = "Продать"
        else:
            action_text = ""

        confirm_text = f"Вы выбрали:\nДействие: {action_text}\nПроект: {project}\nСервер: {server}\nКоличество виртов: {'{:,}'.format(amount)}\n\nИтоговая цена: {'{:,}'.format(price)} руб.\n\nПодтвердить заказ?"

        keyboard = InlineKeyboardMarkup(row_width=2)
        buttons = [
            InlineKeyboardButton(text="Подтвердить", callback_data=confirm_cb.new(action='confirm')),
            InlineKeyboardButton(text="Отменить", callback_data=confirm_cb.new(action='cancel'))
        ]
        keyboard.add(*buttons)

        await query.message.edit_text(confirm_text, reply_markup=keyboard)

    await query.answer()


@dp.callback_query_handler(confirm_cb.filter(action=['confirm', 'cancel']),
                           lambda callback: callback.from_user.id not in active_chats)
async def handle_confirm_callback(callback: types.CallbackQuery, callback_data: dict):
    user_id = callback.from_user.id
    action = callback_data['action']

    if action == 'confirm':
        action = user_data[user_id]['action']
        project = user_data[user_id]['project']
        server = user_data[user_id]['server']
        amount = user_data[user_id]['amount']
        username = callback.from_user.username

        order_id = add_order(user_id, username, action, project, server, amount)

        matched_order = database.match_orders(user_id, action, project, server, amount)
        if matched_order:
            await callback.message.delete()

            matched_order_id, other_user_id = matched_order

            buyer_id = user_id if action == 'buy' else other_user_id
            seller_id = user_id if action == 'sell' else other_user_id
            buyer_order_id = order_id if action == 'buy' else matched_order_id
            seller_order_id = order_id if action == 'sell' else matched_order_id
            matched_orders_id = create_matched_order(buyer_id, buyer_order_id, seller_id, seller_order_id)

            await notify_users_of_chat(matched_orders_id, buyer_id, seller_id, order_id)

            database.update_order_status(order_id, 'matched')
            database.update_order_status(matched_order_id, 'matched')

        del user_data[user_id]

        await callback.message.edit_text("🟢 Ваш заказ подтвержден и сохранен. Ожидайте ответа.")
    else:
        del user_data[user_id]
        await callback.message.edit_text("🟥 Ваш заказ отменен.")

    await callback.answer()


async def send_order_info(matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str, order_id: int | str):
    order = get_order(order_id=order_id)

    project = order[4]
    server = order[5]
    amount = int(order[6])

    order_ifo = ("✳️ <i><u>Информация по сделке:</u></i> ✳️\n\n"
                 f"🆔: <b>{str(matched_orders_id)}</b>\n"
                 "🛒 Операция: <i>{}</i>\n"
                 f"👨‍💻 Проект: <b>{project}</b>\n"
                 f"🌆 Сервер: <b>{server}</b>\n"
                 f"💵 Кол-во виртов: <code>{str(amount)}</code>\n\n"
                 "<b><u>Итоговая сумма: {} руб</u></b>")

    price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
    price = str(math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000)))

    await bot.send_message(buyer_id, order_ifo.format('Покупка', price), parse_mode='HTML')

    price_per_million = PRICE_PER_MILLION_VIRTS[project]["sell"]
    price = str(math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000)))

    await bot.send_message(seller_id, order_ifo.format('Продажа', price), parse_mode='HTML')


async def notify_users_of_chat(matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str,
                               order_id: int | str):
    chat_id = f"{buyer_id}_{seller_id}"
    active_chats[buyer_id] = chat_id
    active_chats[seller_id] = chat_id

    cancel_requests[chat_id] = {buyer_id: False, seller_id: False}

    buyer_message = "⭕️ Мы нашли продавца для вашего заказа. Начинается чат с продавцом."
    seller_message = "⭕️ Мы нашли покупателя для вашего заказа. Начинается чат с покупателем."

    await bot.send_message(buyer_id, buyer_message)
    await bot.send_message(seller_id, seller_message)

    await send_order_info(matched_orders_id, buyer_id, seller_id, order_id)

    buyer_keyboard = InlineKeyboardMarkup(row_width=2)
    buyer_keyboard.row(
        InlineKeyboardButton(text="📢 Репорт", callback_data=f'report_{str(seller_id)}_{str(matched_orders_id)}'))
    buyer_keyboard.row(
        InlineKeyboardButton(text="✅ Подтвердить сделку", callback_data=confirm_cb.new(action='confirm_')),
        InlineKeyboardButton(text="❌ Отменить сделку", callback_data=confirm_cb.new(action='cancel_'))
    )

    seller_keyboard = InlineKeyboardMarkup(row_width=1)
    seller_keyboard.add(
        InlineKeyboardButton(text="📢 Репорт", callback_data=f'report_{str(buyer_id)}_{str(matched_orders_id)}'),
        InlineKeyboardButton(text="Отменить сделку", callback_data=confirm_cb.new(action='cancel_'))
    )

    action_message = "Выберите действие:"
    message_buyer = await bot.send_message(buyer_id, action_message, reply_markup=buyer_keyboard)
    message_seller = await bot.send_message(seller_id, action_message, reply_markup=seller_keyboard)

    cancel_requests[chat_id]['buyer_message_id'] = message_buyer.message_id
    cancel_requests[chat_id]['seller_message_id'] = message_seller.message_id


@dp.callback_query_handler(lambda callback: callback.data.startswith('report_'))
async def report_callback(callback: CallbackQuery, state: FSMContext):
    if await state.get_state() == UserState.waiting_for_problem_description:
        return await callback.answer()
    _, offender_id, order_id = callback.data.split('_')

    user_data.setdefault(callback.from_user.id, {})
    user_data[callback.from_user.id]['complaint'] = {}
    user_data[callback.from_user.id]['complaint']['offender_id'] = offender_id
    user_data[callback.from_user.id]['complaint']['order_id'] = order_id
    user_states[callback.from_user.id] = 'waiting_for_problem_description'
    await state.set_state(UserState.waiting_for_problem_description)

    await callback.message.answer('📝 Пожалуйста, опишите подробно суть проблемы:')


@dp.callback_query_handler(confirm_cb.filter(action=['confirm_', 'cancel_']))
async def handle_chat_action_callback(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id
    action = callback_data['action']
    chat_id = active_chats[user_id]
    buyer_id, seller_id = map(int, chat_id.split('_'))
    other_user_id = buyer_id if user_id == seller_id else seller_id

    if action == 'cancel_':
        cancel_requests[chat_id][user_id] = True

        await bot.delete_message(user_id, query.message.message_id)

        if user_id == seller_id:

            await bot.send_message(buyer_id, "🟥 Сделка отменена продавцом.")
            await bot.send_message(seller_id, "🟥 Сделка отменена.")

            await bot.delete_message(buyer_id, cancel_requests[chat_id]['buyer_message_id'])

            try:
                update_order_status(buyer_id, 'deleted')
                update_order_status(seller_id, 'deleted')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'deleted': {e}")

            del active_chats[buyer_id]
            del active_chats[seller_id]
            del cancel_requests[chat_id]
        else:

            await bot.send_message(user_id, "⭕️ Вы хотите отменить сделку. Ожидайте подтверждения от продавца.")
            await bot.send_message(other_user_id,
                                   "⭕️ Покупатель хочет отменить сделку. Если вы хотите отменить сделку, нажмите 'Отменить сделку'.")

            if cancel_requests[chat_id][other_user_id]:
                await bot.send_message(buyer_id, "🟥 Сделка отменена.")
                await bot.send_message(seller_id, "🟥 Сделка отменена.")

                await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])

                try:
                    update_order_status(buyer_id, 'deleted')
                    update_order_status(seller_id, 'deleted')
                except sqlite3.Error as e:
                    print(f"Error updating order status to 'deleted': {e}")

                del active_chats[buyer_id]
                del active_chats[seller_id]
                del cancel_requests[chat_id]

    elif action == 'confirm_':
        if user_id == buyer_id:

            cancel_requests[chat_id][user_id] = True

            await bot.delete_message(buyer_id, query.message.message_id)
            await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])

            await bot.send_message(buyer_id, "🟢 Сделка подтверждена вами.")
            await bot.send_message(seller_id, "🟢 Покупатель подтвердил сделку. Переписка завершена.")

            try:
                update_order_status(buyer_id, 'confirmed')
                update_order_status(seller_id, 'confirmed')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'confirmed': {e}")

            del active_chats[buyer_id]
            del active_chats[seller_id]
            del cancel_requests[chat_id]


@dp.message_handler(lambda message: message.from_user.id in active_chats and
                                    message.text not in ['/support', '/report'] and
                                    user_states.get(message.from_user.id) not in
                                    ['waiting_for_user_id', 'waiting_for_order_id', 'waiting_for_problem_description'])
async def handle_chat_message(message: types.Message):
    user_id = message.from_user.id
    chat_id = active_chats[user_id]
    buyer_id, seller_id = map(int, chat_id.split('_'))
    recipient_id = buyer_id if user_id == seller_id else seller_id

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE user_id=?", (user_id,))
    bot_user_id = cursor.fetchone()[0]
    conn.close()

    save_chat_message(chat_id, user_id, recipient_id, message.text)

    await bot.send_message(recipient_id, f"Сообщение от ID {bot_user_id}: {message.text}")


@dp.message_handler(commands=['account'])
async def account_info(message: Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)

    if user_data:
        user_id, tg_id, username, phone_number, ballance, created_at = user_data
        account_info_text = f"Данные вашего аккаунта:\n\n" \
                            f"Баланс: {ballance}\n" \
                            f"User ID: {user_id}\n" \
                            f"Username: {username}\n" \
                            f"Telegram ID: {tg_id}\n" \
                            f"Дата захода в бота: {created_at}\n"

        buttons = [
            InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up_balance"),
            InlineKeyboardButton(text="Мои ордера", callback_data="my_orders")
        ]
        keyboard = InlineKeyboardMarkup().add(*buttons)

        await message.answer(account_info_text, reply_markup=keyboard)
    else:
        await message.answer("Данные пользователя не найдены.")


@dp.callback_query_handler(lambda query: query.data == 'top_up_balance',
                           lambda query: query.from_user.id not in active_chats)
async def process_top_up_balance(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("Здесь будет процесс пополнения баланса...")


@dp.callback_query_handler(lambda query: query.data == 'my_orders')
async def process_my_orders(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    orders = get_orders_by_user_id(user_id)

    if orders:
        orders_text = "Ваши ордера:\n\n"
        for order in orders:
            order_id, _, action, project, server, amount, status, created_at = order
            orders_text += f"ID ордера: {order_id}\n" \
                           f"Действие: {action}\n" \
                           f"Проект: {project}\n" \
                           f"Сервер: {server}\n" \
                           f"Сумма: {amount}\n" \
                           f"Статус: {status}\n" \
                           f"Дата создания: {created_at}\n\n"
    else:
        orders_text = "У вас пока нет ордеров."

    await callback_query.answer()
    await callback_query.message.answer(orders_text)


@dp.message_handler(commands=['report'])
async def report_command(message: Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    write_ticket_button = types.InlineKeyboardButton(text="Написать тикет", callback_data="write_ticket")
    my_tickets_button = types.InlineKeyboardButton(text="Мои тикеты", callback_data="my_tickets")
    keyboard.add(write_ticket_button, my_tickets_button)

    report_text = "Если вы хотите оставить жалобу на пользователя, выберите 'Написать тикет'.\nДля просмотра ваших тикетов нажмите 'Мои тикеты'."

    await message.answer(report_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'write_ticket')
async def process_write_ticket_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    await callback.message.answer("Введите ID пользователя (только числом), на которого хотите составить тикет:")

    user_states[callback.from_user.id] = 'waiting_for_user_id'
    await state.set_state(UserState.waiting_for_user_id)

    user_data.setdefault(callback.from_user.id, {})
    user_data[callback.from_user.id]['complaint'] = {}


@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'waiting_for_user_id')
# @dp.callback_query_handler(StateFilter(dp, UserState.waiting_for_user_id))
async def process_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        return await message.answer("Пожалуйста, введите корректный ID пользователя (только числом).")

    offender_id = get_user_id_by_id(user_id)

    if not offender_id:
        return await message.answer("🤕 Похоже, что такого пользователя не существует. Попробуйте ещё раз")

    user_data[message.from_user.id]['complaint']['offender_id'] = offender_id
    await message.answer("Теперь введите ID сделки (только числом), по которому хотите написать тикет:")

    user_states[message.from_user.id] = 'waiting_for_order_id'
    await state.set_state(UserState.waiting_for_order_id)


# @dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'waiting_for_order_id')
@dp.message_handler(StateFilter(dp, UserState.waiting_for_order_id))
async def process_order_id(message: Message, state: FSMContext):
    try:
        order_id = int(message.text.strip())
    except ValueError:
        return await message.answer("Пожалуйста, введите корректный ID сделки (только числом).")

    if not check_matched_order(order_id, message.from_user.id):
        return await message.answer(
            "Похоже, у Вас не было такой сделки. Попробуйте ещё раз")  # TODO: кнопку выхода отсюда

    user_data[message.from_user.id]['complaint']['order_id'] = order_id

    await message.answer("Теперь подробно изложите суть проблемы:")

    user_states[message.from_user.id] = 'waiting_for_problem_description'
    await state.set_state(UserState.waiting_for_problem_description)


# @dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'waiting_for_problem_description')
@dp.message_handler(StateFilter(dp, UserState.waiting_for_problem_description))
async def process_problem_description(message: types.Message):
    complaint_text = message.text
    user_data[message.from_user.id]['complaint']['complaint_text'] = complaint_text

    keyboard = types.InlineKeyboardMarkup()
    send_ticket_button = types.InlineKeyboardButton(text="Отправить тикет", callback_data="send_ticket")
    cancel_ticket_button = types.InlineKeyboardButton(text="Отменить тикет", callback_data="cancel_ticket")
    keyboard.add(send_ticket_button, cancel_ticket_button)

    await message.answer("Выберите действие:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data in ['send_ticket', 'cancel_ticket'])
async def process_ticket_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == 'send_ticket':
        try:
            order_id = user_data[callback.from_user.id]['complaint']['order_id']
            complainer_id = callback.from_user.id
            offender_id = user_data[callback.from_user.id]['complaint']['offender_id']
            complaint = user_data[callback.from_user.id]['complaint']['complaint_text']
            create_report(order_id, complainer_id, offender_id, complaint)

            await callback.message.edit_text(
                "✅ Тикет успешно отправлен. Пожалуйста, дождитесь ответа от администратора")
            user_states[callback.from_user.id] = {}
            await state.clear()

            await bot.send_message(admin_id, '‼️ Поступил репорт\n/admin')
            await bot.send_message(922787101, '‼️ Поступил репорт\n/admin')

        except Exception as e:
            await callback.message.answer("🤕 Что-то пошло не так. Пожалуйста, свяжитесь с поддержкой напрямую")
            print(e, datetime.datetime.now().time(), sep='\n')

    elif callback.data == 'cancel_ticket':
        user_data[callback.from_user.id]['complaint'] = {}
        await callback.message.edit_text("Вы отменили создание тикета.")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = """
    Привет! Я бот для оставления жалоб и управления тикетами.

    Список доступных команд:
    /help - Вывести это сообщение с инструкцией
    /report - Начать процесс оставления жалобы на пользователя

    Инструкция пользования:
    1. Нажмите кнопку "Написать тикет" в меню, чтобы начать оставление жалобы.
    2. Следуйте указаниям бота для ввода ID пользователя и заказа.
    3. После ввода обоих ID жалоба будет зарегистрирована.

    Если у вас возникли вопросы или проблемы, обратитесь к администратору.
    """
    await message.answer(help_text)


@dp.message_handler(commands=['myorders'])
async def my_orders_command(message: Message):
    user_id = message.from_user.id
    orders = get_orders_by_user_id(user_id)

    if orders:
        orders_text = "Ваши ордера:\n\n"
        for order in orders:
            order_id, _, action, project, server, amount, status, created_at = order
            orders_text += f"ID ордера: {order_id}\n" \
                           f"Действие: {action}\n" \
                           f"Проект: {project}\n" \
                           f"Сервер: {server}\n" \
                           f"Сумма: {amount}\n" \
                           f"Статус: {status}\n" \
                           f"Дата создания: {created_at}\n\n"

        await message.answer(orders_text)
    else:
        await message.answer("У вас пока нет ордеров.")


@dp.message_handler(commands=['support'])
async def support_command(message: types.Message):
    support_info = "Для связи с поддержкой используйте следующие контактные данные:\n\n" \
                   "Email: support@example.com\n" \
                   "Телефон: +1234567890\n" \
                   "Telegram: @support_username\n"

    await message.answer(support_info)


@dp.message_handler(commands=['info'])
async def info_command(message: types.Message):
    bot_info = "Это бот для управления заказами и общения с поддержкой.\n" \
               "Он предоставляет различные функции, такие как управление ордерами и связь с поддержкой."

    await message.answer(bot_info)


@dp.message_handler(commands=['orders'])
async def orders_command(message: types.Message):
    user_data[message.from_user.id]: dict = {}
    user_data[message.from_user.id]['watched_orders']: list = []
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton(text="GTA5RP", callback_data=project_cb.new(name='GTA5RP_orders')),
        InlineKeyboardButton(text="Majestic", callback_data=project_cb.new(name='Majestic_orders')),
        InlineKeyboardButton(text="Radmir GTA5", callback_data=project_cb.new(name='Radmir GTA5_orders'))
    ]
    keyboard.add(*buttons)

    await message.answer(f"Выберите проект", reply_markup=keyboard)


@dp.callback_query_handler(project_cb.filter(name=['GTA5RP_orders', 'Majestic_orders', 'Radmir GTA5_orders']))
async def handle_project_orders_callback(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id
    project_name: str = callback_data['name']

    user_data[user_id] = {}
    user_data[user_id]['project'] = project_name.split('_')[0]

    if project_name == 'GTA5RP_orders':
        servers = GTA5RP_SERVERS
    elif project_name == 'Majestic_orders':
        servers = MAJESTIC_SERVERS
    elif project_name == 'Radmir GTA5_orders':
        servers = RADMIR_SERVERS
    else:
        return await query.message.edit_text("Ошибка: проект не найден.")

    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=server, callback_data=orders_servers_cb.new(name=server)) for server in
               servers]
    keyboard.add(*buttons)

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=main_menu_cb.new(action='back_to_projects_orders')))

    await query.message.edit_text(
        f"Вы выбрали проект {project_name.split('_')[0]}. Теперь выберите сервер",
        reply_markup=keyboard)
    await query.answer()


@dp.callback_query_handler(main_menu_cb.filter(action='back_to_projects_orders'))
async def handle_orders_back_to_projects_callback(query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=3)
    projects = ['GTA5RP', 'Majestic', 'Radmir GTA5']
    buttons = [InlineKeyboardButton(text=project, callback_data=project_cb.new(name=f'{project}_orders')) for project in
               projects]
    keyboard.add(*buttons)

    await query.message.edit_text(
        f"Выберите проект", reply_markup=keyboard)


@dp.callback_query_handler(orders_servers_cb.filter())
async def handle_orders_server_callback(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id
    server = callback_data['name']
    project = user_data[user_id]['project']

    orders = get_pending_sell_orders(user_id, project, server)

    if not orders:
        return await query.message.edit_text("К сожалению, на данный момент ещё нет доступных ордеров на продажу, "
                                             "удовлетворяющих данным параметрам 😢")
    await query.message.delete()

    watched_orders = []
    orders_num = 0
    for order in orders:
        order_id, user_id, username, action, project, server, amount, status, created_at = order

        price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
        price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))

        # orders_text = f"🆔 ID ордера: {order_id}\n\n" \
        orders_text = f"🛒 Операция: Продажа\n" \
                      f"👨‍💻 Проект: {project}\n" \
                      f"🌆 Сервер: {server}\n" \
                      f"💵 Кол-во валюты: {math.ceil(amount)}\n" \
                      f"⌚️ Дата создания: {convert_datetime(created_at)}\n\n" \
                      f"Цена: {price}руб"

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(order_id)}'))

        watched_orders.append(order_id)

        if orders_num == 4:
            kb.add(InlineKeyboardButton(
                text='⏬ Посмотреть ещё',
                callback_data=f'watch-other_{project}_{server}_{"-".join([str(el) for el in watched_orders])}')
            )
            return await query.message.answer(orders_text, reply_markup=kb)

        await query.message.answer(orders_text, reply_markup=kb)

        orders_num += 1


@dp.callback_query_handler(lambda query: query.data.startswith('watch-other_'))
async def watch_other_callback(query: CallbackQuery):
    user_id = query.from_user.id
    _, project, server, watched_orders = query.data.split('_')
    watched_orders = list(map(int, watched_orders.split('-')))
    print(watched_orders)

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(watched_orders[-1])}'))
    await query.message.edit_text(query.message.text, reply_markup=kb)

    orders = get_pending_sell_orders(user_id, project, server)

    if not orders:
        return await query.message.edit_text("Нет других подобных ордеров 😢")

    orders_num = 0
    for order in orders:
        order_id, user_id, username, action, project, server, amount, status, created_at = order

        if order_id in watched_orders:
            continue

        price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
        price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))

        orders_text = f"🆔 ID ордера: {order_id}\n\n" \
                      f"🛒 Операция: Продажа\n" \
                      f"👨‍💻 Проект: {project}\n" \
                      f"🌆 Сервер: {server}\n" \
                      f"💵 Кол-во валюты: {math.ceil(amount)}\n" \
                      f"⌚️ Дата создания: {convert_datetime(created_at)}\n\n" \
                      f"Цена: {price}руб"

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(order_id)}'))

        if orders_num == 4:
            kb.add(InlineKeyboardButton(
                text='⏬ Посмотреть ещё',
                callback_data=f'watch_other_{project}_{server}_{"-".join(user_data[user_id]["watched_orders"])}')
            )
            return await query.message.answer(orders_text, reply_markup=kb)

        await query.message.answer(orders_text, reply_markup=kb)

        watched_orders.append(order_id)
        orders_num += 1


@dp.callback_query_handler(lambda query: query.data.startswith('buy_order_'),
                           lambda query: query.from_user.id not in active_chats)
async def buy_order(query: CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text="🤝 Да, начать чат с продавцом",
                                callback_data=f'confirmation_of_buying_{str(query.data.split("_")[-1])}'))
    await query.message.edit_text(query.message.text + '\n\n🤔 Вы уверены?', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('confirmation_of_buying_'),
                           lambda query: query.from_user.id not in active_chats)
async def confirmation_of_buying(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]
    buyer_id = callback.from_user.id
    seller_id = get_user_id_by_order(order_id)
    matched_orders_id = create_matched_order(buyer_id, 0, seller_id, order_id)

    await callback.message.edit_text(callback.message.text[:-13] + '✅ Начался чат с продавцом')
    await notify_users_of_chat(matched_orders_id, buyer_id, seller_id, order_id)

    # TODO: добавить деньги
    # TODO: FSM!!!


@dp.callback_query_handler(
    lambda callback: callback.data == 'admin_reports' and callback.from_user.id in [admin_id, 922787101])
async def admin_reports(callback: CallbackQuery):
    complaints = get_open_reports()
    if not complaints:
        return await callback.message.edit_text("✅ Нет необработанных жалоб")
    await callback.message.delete()

    for complaint in complaints:
        complaint_id, order_id, complainer_id, offender_id, complaint_text = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        text = (f'📋 <i><u>Репорт по заказу: {str(order_id)}</u></i>\n\n'
                f'👤 Автор: {complainer_username} (<code>{complainer_id}</code>)\n'
                f'💢 Жалуется на: {offender_username} (<code>{offender_id}</code>)\n\n'
                f'<b>📝 Причина:</b>\n{complaint_text}')

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton(text='Вмешаться', callback_data=f'reply_to_report_{str(complaint_id)}'))

        await callback.message.answer(text, reply_markup=kb, parse_mode='HTML')


@dp.callback_query_handler(lambda callback: callback.data.startswith('reply_to_report_'))
async def reply_to_report(callback: CallbackQuery):
    report_id, order_id, complainer_id, offender_id, complaint, _, created_at = get_report(callback.data.split('_')[-1])

    await callback.message.answer('Допиши в 906 строчке кода')


@dp.message_handler(
    lambda message: message.from_user.id in user_data and 'amount' not in user_data[
        message.from_user.id] and '/orders' != message.text and message.from_user.id not in active_chats)
async def handle_custom_amount(message: types.Message):
    user_id = message.from_user.id
    try:
        amount = int(message.text.replace(".", "").replace(",", ""))
        if amount < 500000 or amount > 1000000000000:
            await message.answer("Минимальное кол-во виртуальной валюты: 500.000 ")
            return

        user_data[user_id]['amount'] = amount

        action_type = user_data[user_id]['action']
        project = user_data[user_id]['project']
        server = user_data[user_id]['server']

        price_per_million = PRICE_PER_MILLION_VIRTS[project][action_type.lower()]
        price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))

        if action_type == 'buy':
            action_text = "Купить"
        elif action_type == 'sell':
            action_text = "Продать"
        else:
            action_text = ""

        confirm_text = f"Вы выбрали:\nДействие: {action_text}\nПроект: {project}\nСервер: {server}\nКоличество виртов: {'{:,}'.format(amount)}\n\nИтоговая цена: {'{:,}'.format(price)} руб.\n\nПодтвердить заказ?"

        keyboard = InlineKeyboardMarkup(row_width=2)
        buttons = [
            InlineKeyboardButton(text="Подтвердить", callback_data=confirm_cb.new(action='confirm')),
            InlineKeyboardButton(text="Отменить", callback_data=confirm_cb.new(action='cancel'))
        ]
        keyboard.add(*buttons)

        await message.answer(confirm_text, reply_markup=keyboard)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное количество виртов.")


def todo() -> None:
    # TODO: вывод заказов по параметру проект
    # TODO: вывод заказов по параметрам проект, сервер

    # TODO: кнопка "продавть" в меню, открывающая продажу вирты, бизнеса и аккаунта

    # TODO: кнопка "созать заказ" купить и продать вирту, бизнес или аккаунт
    pass


if __name__ == '__main__':  # TODO: починить репорты (админу высылается список, в котором на 1 и тот же Id могут быть 2 разные жалобы)
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)


