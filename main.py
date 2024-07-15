import asyncio
import logging
import math

from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram import Bot, Dispatcher  # , F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart  # , StateFilter

from core import Config, load_config
from database import *
from keyboards import *
from lexicon import *
# from states import UserState
# from utils import convert_datetime

logging.basicConfig(level=logging.INFO)
config: Config = load_config('.env')

storage = MemoryStorage()
default = DefaultBotProperties(parse_mode='HTML')

bot: Bot = Bot(token=config.tg_bot.token, default=default)
dp: Dispatcher = Dispatcher(storage=storage)

kb = UserKeyboards()
admin_kb = AdminKeyboards()

admin_ids = config.tg_bot.admin_ids

user_data = {}
user_states = {}
active_chats = {}
cancel_requests = {}


@dp.message(CommandStart() or Command('menu'))
async def start(message: Message):
    await message.answer(LEXICON['start_message'], reply_markup=kb.start_kb())

    if not get_user(message.from_user.id):
        user = message.from_user
        phone_number = None
        database.add_user(user.id, user.username, phone_number)


@dp.callback_query(lambda callback: callback.data == 'start_buy_button')
async def start_buy_button(callback: CallbackQuery):
    await callback.message.edit_text('Выберите позицию, которую хотите приобрести', reply_markup=kb.buy_kb())


@dp.callback_query(lambda callback: callback.data == 'start_sell_button')
async def start_sell_button(callback: CallbackQuery):
    await callback.message.edit_text('Выберите позицию, которую хотите продать', reply_markup=kb.sell_kb())


@dp.callback_query(lambda callback: callback.data == 'start_create_order_button')
async def start_create_order_button(callback: CallbackQuery):
    await callback.message.edit_text('Выберите позицию, для которой хотите создать заявку на покупку',
                                     reply_markup=kb.create_order_kb())


@dp.callback_query(lambda callback: callback.data == 'start_autoposter_discord_button')
async def autoposter_discord_button(callback: CallbackQuery):
    await callback.message.edit_text('Soon..', reply_markup=kb.back_to_start_kb())


@dp.callback_query(lambda callback: callback.data == 'back_to_start')
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['start_message'], reply_markup=kb.start_kb())


@dp.message(lambda message: message.text == '/admin' and message.from_user.id in admin_ids)
async def admin(message: Message):
    await message.answer(f'Здравствуйте, {message.from_user.username}! 😊', reply_markup=admin_kb.menu_kb())


@dp.callback_query(lambda callback: callback.data.split('_')[-1] == 'virt')
async def handle_action_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action_type = callback.data.split('_')[0]
    user_data[user_id] = {'action': action_type}

    action_text = "приобрести" if action_type == 'buy' else "продать"

    await callback.message.edit_text(f"Выберите платформу, где хотите {action_text} виртуальную валюту.",
                                     reply_markup=kb.game_kb(action_type))


@dp.callback_query(lambda callback: callback.data.startswith('game_'))
async def game_callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data[user_id]['game'] = callback.data.split('_')[-1]
    action_type = user_data[user_id]['action']
    game = callback.data.split('_')[-1]
    user_data[user_id]['game'] = game
    if game == 'gta5':
        await callback.message.edit_text('теперь пикни проект', reply_markup=kb.projects_kb(action_type))
    else:
        await callback.message.edit_text("I'm sorry, малышка, не готово ещё",
                                         reply_markup=kb.back_to_start_kb())  # TODO: доделать


@dp.callback_query(lambda callback: callback.data.startswith('back_to_games_'))
async def back_to_games_callback(callback: CallbackQuery):
    print(786543)
    user_id = callback.from_user.id
    action_type = user_data[user_id]['action']

    action_text = "приобрести" if action_type == 'buy' else "продать"

    await callback.message.edit_text(f"Выберите проект на котором хотите {action_text} виртуальную валюту.",
                                     reply_markup=kb.game_kb(action_type))


@dp.callback_query(
    lambda callback: callback.data in [f'project_{x}' for x in ['GTA5RP', 'Majestic', 'Radmir GTA5']])
async def handle_project_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    project_name = callback.data.split('_')[-1]
    action_type = user_data[user_id]['action']

    user_data[user_id]['project'] = project_name

    if project_name == 'GTA5RP':
        servers_for_project = GTA5RP_SERVERS
    elif project_name == 'Majestic':
        servers_for_project = MAJESTIC_GTA5_SERVERS
    elif project_name == 'Radmir GTA5':
        servers_for_project = RADMIR_GTA5_SERVERS
    else:
        await callback.message.edit_text("🤕 Я не могу найти выбранный проект")
        await callback.answer()
        return

    action_text = "покупки" if action_type == 'buy' else "продажи"

    await callback.message.edit_text(
        f"Вы выбрали проект {project_name}. Выберите сервер для {action_text} виртуальной валюты:",
        reply_markup=kb.servers_kb(servers_for_project))


@dp.callback_query(lambda callback: callback.data == 'back_to_projects')
async def handle_main_menu_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action_type = user_data[user_id]['action']

    action_text = "приобрести" if action_type == 'buy' else "продать"

    await callback.message.edit_text(
        f"Выберите проект на котором хотите {action_text} виртуальную валюту.",
        reply_markup=kb.projects_kb(action_type))


@dp.callback_query(lambda callback: callback.data.startswith('back_to_'))
async def back_to(callback: CallbackQuery):
    destination = callback.data.split('_')[-1]

    if destination == 'buy':
        await start_buy_button(callback)
    elif destination == 'sell':
        await start_sell_button(callback)
    elif destination == 'servers':
        user_id = callback.from_user.id
        project_name = user_data[user_id]['project']
        action_type = user_data[user_id]['action']

        if project_name == 'GTA5RP':
            servers_for_project = GTA5RP_SERVERS
        elif project_name == 'Majestic':
            servers_for_project = MAJESTIC_GTA5_SERVERS
        elif project_name == 'Radmir GTA5':
            servers_for_project = RADMIR_GTA5_SERVERS
        else:
            return await callback.message.edit_text("🤕 Я не могу найти выбранный проект")

        action_text = "покупки" if action_type == 'buy' else "продажи"

        await callback.message.edit_text(
            f"Вы выбрали проект {project_name}. Выберите сервер для {action_text} виртуальной валюты:",
            reply_markup=kb.servers_kb(servers_for_project))


@dp.callback_query(lambda callback: callback.data.startswith('server_'))
async def handle_server_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    server_name = callback.data.split('_')[-1]
    user_data[user_id]['server'] = server_name
    action_type = user_data[user_id]['action']
    project_name = user_data[user_id]['project']

    action_text = "приобрести" if action_type == 'buy' else "продать"

    await callback.message.edit_text(
        f"Вы выбрали проект {project_name}, сервер {server_name}. "
        f"Теперь выберите количество виртуальной валюты, которое хотите {action_text}:",
        reply_markup=kb.amount_kb())


@dp.callback_query(lambda callback: callback.data.startswith('amount_'))
async def handle_amount_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    amount_value = callback.data.split('_')[-1]

    if amount_value == 'custom':
        await bot.send_message(callback.from_user.id, "Введите нужное количество виртуальной валюты:")
        await callback.message.delete()
    else:
        amount = int(amount_value)
        if amount < 500000 or amount > 1000000000000:
            await bot.send_message(user_id, "🤕 Количество виртуальной валюты должно быть от 500,000")
            return await callback.answer()

        user_data[user_id]['amount'] = amount

        action_type = user_data[user_id]['action']
        project = user_data[user_id]['project']
        server = user_data[user_id]['server']
        price_per_million = PRICE_PER_MILLION_VIRTS[project][action_type.lower()]
        cost = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))

        if action_type == 'buy':
            action_text = "Купить"
        elif action_type == 'sell':
            action_text = "Продать"
        else:
            action_text = ""

        confirm_text = (f"Ваш заказ:\n"
                        f"├ Операция: {action_text}\n"
                        f"├ Проект: {project}\n"
                        f"├ Сервер: {server}\n"
                        f"└ Количество виртов: {'{:,}'.format(amount)}\n\n"
                        f"Итоговая цена: {'{:,}'.format(cost)} руб.\n\n"
                        f"Подтвердить?")
        await callback.message.edit_text(confirm_text, reply_markup=kb.confirmation_of_creation_kb())

    await callback.answer()


@dp.callback_query(
    lambda callback: callback.data.startswith(
        'confirmation_of_creation_') and callback.from_user.id not in active_chats)
async def handle_confirm_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split('_')[-1]

    if action == 'confirm':
        action = user_data[user_id]['action']
        project = user_data[user_id]['project']
        server = user_data[user_id]['server']
        amount = user_data[user_id]['amount']
        username = callback.from_user.username

        order_id = add_order(user_id, username, action, project, server, amount)

        await callback.message.edit_text("✅ Ваш заказ подтвержден и сохранен. Ожидайте ответа.")

        matched_order = database.match_orders(user_id, action, project, server, amount)
        if matched_order:
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

    else:
        del user_data[user_id]
        await callback.message.edit_text("🚫 Ваш заказ отменен.")

    await callback.answer()


async def send_order_info(matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str, order_id: int | str):
    order = get_order(order_id=order_id)

    project = order[4]
    server = order[5]
    amount = int(order[6])

    buyer_message = "‼️ Я нашел продавца по вашему заказу. Начинаю ваш чат с продавцом.\n\n"
    seller_message = "‼️ Я нашел покупателя по вашему заказу. Начинаю ваш чат с покупателем.\n\n"

    order_ifo = ("{}<b><u>Информация по сделке:</u></b> \n\n"
                 f"├ ID сделки: <b>{str(matched_orders_id)}</b>\n"
                 "├ Операция: <b>{}</b>\n"
                 f"├ Проект: <b>{project}</b>\n"
                 f"├ Сервер: <b>{server}</b>\n"
                 f"└ Кол-во виртов: <code>{str(amount)}</code>\n\n"
                 "<b><u>Итоговая сумма</u>: {} руб</b>")

    price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
    cost = str(math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000)))

    await bot.send_message(buyer_id, order_ifo.format(buyer_message, 'Покупка', cost), parse_mode='HTML')

    price_per_million = PRICE_PER_MILLION_VIRTS[project]["sell"]
    cost = str(math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000)))

    await bot.send_message(seller_id, order_ifo.format(seller_message, 'Продажа', cost), parse_mode='HTML')


async def notify_users_of_chat(matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str,
                               order_id: int | str):
    chat_id = f"{buyer_id}_{seller_id}"
    active_chats[buyer_id] = chat_id
    active_chats[seller_id] = chat_id
    cancel_requests[chat_id] = {buyer_id: False, seller_id: False}
    action_message = "Выберите действие:"

    await send_order_info(matched_orders_id, buyer_id, seller_id, order_id)
    message_buyer = await bot.send_message(buyer_id, action_message,
                                           reply_markup=kb.confirmation_of_deal_buyer_kb(seller_id, matched_orders_id))
    message_seller = await bot.send_message(seller_id, action_message,
                                            reply_markup=kb.confirmation_of_deal_seller_kb(buyer_id, matched_orders_id))

    cancel_requests[chat_id]['buyer_message_id'] = message_buyer.message_id
    cancel_requests[chat_id]['seller_message_id'] = message_seller.message_id


@dp.callback_query(lambda callback: callback.data.startswith('report_'))
async def report_callback(callback: CallbackQuery):
    if user_states[callback.from_user.id] == 'waiting_for_problem_description':
        return await callback.answer()
    _, offender_id, order_id = callback.data.split('_')

    user_data.setdefault(callback.from_user.id, {})
    user_data[callback.from_user.id]['complaint'] = {}
    user_data[callback.from_user.id]['complaint']['offender_id'] = offender_id
    user_data[callback.from_user.id]['complaint']['order_id'] = order_id
    user_states[callback.from_user.id] = 'waiting_for_problem_description'

    await callback.message.answer('📝 Пожалуйста, опишите подробно суть проблемы:')


@dp.callback_query(lambda callback: callback.data.startswith('confirmation_of_deal_'))
async def handle_chat_action_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split('_')[-1]
    chat_id = active_chats[user_id]
    buyer_id, seller_id = map(int, chat_id.split('_'))
    other_user_id = buyer_id if user_id == seller_id else seller_id

    if action == 'cancel':
        cancel_requests[chat_id][user_id] = True

        await bot.delete_message(user_id, callback.message.message_id)

        if user_id == seller_id:
            del active_chats[buyer_id]
            del active_chats[seller_id]

            await bot.send_message(buyer_id, "🚫 Сделка отменена продавцом.")
            await bot.send_message(seller_id, "🚫 Сделка отменена.")

            await bot.delete_message(buyer_id, cancel_requests[chat_id]['buyer_message_id'])
            del cancel_requests[chat_id]

            try:
                update_order_status(buyer_id, 'deleted')
                update_order_status(seller_id, 'deleted')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'deleted': {e}")

        else:
            await bot.send_message(user_id, "‼️ Вы хотите отменить сделку. Ожидайте подтверждения от продавца.")
            await bot.send_message(other_user_id, "‼️ Покупатель хочет отменить сделку. Если вы хотите отменить "
                                                  "сделку, нажмите 'Отменить сделку'.")

            if cancel_requests[chat_id][other_user_id]:
                del active_chats[buyer_id]
                del active_chats[seller_id]

                await bot.send_message(buyer_id, "🚫 Сделка отменена.")
                await bot.send_message(seller_id, "🚫 Сделка отменена.")

                await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])
                del cancel_requests[chat_id]

                try:
                    update_order_status(buyer_id, 'deleted')
                    update_order_status(seller_id, 'deleted')
                except sqlite3.Error as e:
                    print(f"Error updating order status to 'deleted': {e}")

    elif action == 'confirm':
        if user_id == buyer_id:

            cancel_requests[chat_id][user_id] = True

            await bot.delete_message(buyer_id, callback.message.message_id)
            await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])

            await bot.send_message(buyer_id, "✅ Сделка подтверждена вами.")
            await bot.send_message(seller_id, "✅ Покупатель подтвердил сделку. Сделка завершена.")

            try:
                update_order_status(buyer_id, 'confirmed')
                update_order_status(seller_id, 'confirmed')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'confirmed': {e}")

            del active_chats[buyer_id]
            del active_chats[seller_id]
            del cancel_requests[chat_id]


@dp.message(
    lambda message: message.from_user.id in active_chats and message.text not in ['/support',
                                                                                  '/report'] and user_states.get(
        message.from_user.id) not in ['waiting_for_user_id', 'waiting_for_order_id', 'waiting_for_problem_description']
)
async def handle_chat_message(message: Message):
    user_id = message.from_user.id
    chat_id = active_chats[user_id]
    buyer_id, seller_id = map(int, chat_id.split('_'))
    recipient_id = buyer_id if user_id == seller_id else seller_id

    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE user_id=?", (user_id,))
    bot_user_id = cursor.fetchone()[0]
    conn.close()

    save_chat_message(chat_id, user_id, recipient_id, message.text)

    await bot.send_message(recipient_id, f"Сообщение от ID {bot_user_id}: {message.text}")


@dp.message(Command('account'))
async def account_info(message: Message):
    user_id = message.from_user.id
    user_db_data = get_user(user_id)

    if user_db_data:
        user_id, tg_id, username, phone_number, ballance, created_at = user_db_data
        account_info_text = f"Данные вашего аккаунта:\n\n" \
                            f"├ Баланс: {ballance}\n" \
                            f"├ User ID: {user_id}\n" \
                            f"├ Username: {username}\n" \
                            f"├ Telegram ID: {tg_id}\n" \
                            f"└ Дата захода в бота: {created_at}\n"

        await message.answer(account_info_text, reply_markup=kb.account_kb())

    else:
        await message.answer("❔ Я не могу найти ваши данные")


@dp.callback_query(lambda callback: callback.data == 'top_up_balance' and callback.from_user.id not in active_chats)
async def process_top_up_balance(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("Здесь будет процесс пополнения баланса...")


@dp.callback_query(lambda query: query.data == 'my_orders')
async def process_my_orders(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    orders = get_orders_by_user_id(user_id)

    if orders:
        orders_text = "Ваши ордера:\n\n"
        for order in orders:
            order_id, _, action, project, server, amount, status, created_at = order
            orders_text += f"├ ID ордера: {order_id}\n" \
                           f"├ Действие: {action}\n" \
                           f"├ Проект: {project}\n" \
                           f"├ Сервер: {server}\n" \
                           f"├ Сумма: {amount}\n" \
                           f"├ Статус: {status}\n" \
                           f"└ Дата создания: {created_at}\n\n"
    else:
        orders_text = "У вас пока нет ордеров."

    await callback_query.answer()
    await callback_query.message.answer(orders_text)


@dp.message(Command('report'))
async def report_command(message: Message):
    await message.answer(LEXICON['report_message'], reply_markup=kb.report_kb())


@dp.callback_query(lambda c: c.data == 'write_ticket')
async def process_write_ticket_callback(callback_query: CallbackQuery):
    await callback_query.answer()

    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    await callback_query.message.answer("Введите ID пользователя, на которого хотите составить тикет:")

    user_states[callback_query.from_user.id] = 'waiting_for_user_id'
    user_data.setdefault(callback_query.from_user.id, {})
    user_data[callback_query.from_user.id]['complaint'] = {}


@dp.message(lambda message: user_states.get(message.from_user.id) == 'waiting_for_user_id')
async def process_user_id(message: Message):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        return await message.answer(
            "Пожалуйста, введите корректный ID пользователя .")  # Как я просил сделать без user id, чисто с айди ордера

    offender_id = get_user_id_by_id(user_id)

    if not offender_id:
        return await message.answer("❔ Я не могу найти пользователя с таким ID, может вы ошиблись?")

    user_data[message.from_user.id]['complaint']['offender_id'] = offender_id
    await message.answer("Теперь введите ID сделки (только числом), по которому хотите написать тикет:")

    user_states[message.from_user.id] = 'waiting_for_order_id'


@dp.message(lambda message: user_states.get(message.from_user.id) == 'waiting_for_order_id')
async def process_order_id(message: Message):
    try:
        order_id = int(message.text.strip())
    except ValueError:
        return await message.answer("❔ Я не могу найти сделку с таким ID, может вы ошиблись?")

    if not check_matched_order(order_id, message.from_user.id):
        return await message.answer(
            "У вас не было сделки с данным ID, попробуйте еще раз")  # TODO: кнопку выхода отсюда

    user_data[message.from_user.id]['complaint']['order_id'] = order_id
    user_states[message.from_user.id] = 'waiting_for_problem_description'

    await message.answer("Теперь подробно изложите суть проблемы:")


@dp.message(lambda message: user_states.get(message.from_user.id) == 'waiting_for_problem_description')
async def process_problem_description(message: Message):
    complaint_text = message.text
    user_data[message.from_user.id]['complaint']['complaint_text'] = complaint_text

    await message.answer("Выберите действие:", reply_markup=kb.send_report_kb())


@dp.callback_query(lambda c: c.data in ['send_ticket', 'cancel_ticket'])
async def process_ticket_action(callback_query: CallbackQuery):
    await callback_query.answer()
    if callback_query.data == 'send_ticket':
        try:
            order_id = user_data[callback_query.from_user.id]['complaint']['order_id']
            complainer_id = callback_query.from_user.id
            offender_id = user_data[callback_query.from_user.id]['complaint']['offender_id']
            complaint = user_data[callback_query.from_user.id]['complaint']['complaint_text']
            create_report(order_id, complainer_id, offender_id, complaint)

            await callback_query.message.edit_text(
                "✅ Тикет успешно отправлен. Пожалуйста, дождитесь ответа от администратора")
            user_states[callback_query.from_user.id] = {}

            await bot.send_message(admin_ids[0], '‼️ Поступил репорт\n/admin')
            await bot.send_message(922787101, '‼️ Поступил репорт\n/admin')

        except Exception as e:
            await callback_query.message.answer("❔ Что-то пошло не так. Пожалуйста, свяжитесь с поддержкой напрямую")
            print(e, datetime.datetime.now().time(), sep='\n')

    elif callback_query.data == 'cancel_ticket':
        user_data[callback_query.from_user.id]['complaint'] = {}
        await callback_query.message.edit_text("Вы отменили создание тикета.")


@dp.message(Command('help'))
async def help_command(message: Message):
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


@dp.message(Command('myorders'))
async def my_orders_command(message: Message):
    user_id = message.from_user.id
    orders = get_orders_by_user_id(user_id)

    if orders:
        orders_text = "Ваши ордера:\n\n"
        for order in orders:
            order_id, _, action, project, server, amount, status, created_at = order
            orders_text += f"├ ID ордера: {order_id}\n" \
                           f"├ Действие: {action}\n" \
                           f"├ Проект: {project}\n" \
                           f"├ Сервер: {server}\n" \
                           f"├ Сумма: {amount}\n" \
                           f"├ Статус: {status}\n" \
                           f"└Дата создания: {created_at}\n\n"

        await message.answer(orders_text)
    else:
        await message.answer("❔ У вас пока нет ордеров.")


@dp.message(Command('support'))
async def support_command(message: Message):
    support_info = "Для связи с поддержкой используйте следующие контактные данные:\n\n" \
                   "Email: support@example.com\n" \
                   "Телефон: +1234567890\n" \
                   "Telegram: @support_username\n"

    await message.answer(support_info, reply_markup=kb.support_kb())


@dp.callback_query(lambda callback: callback.data == 'contact_support')
async def contact_support_handler(callback: CallbackQuery):
    await callback.message.edit_text('Напиши мне, я объясню @Miros49')


@dp.message(Command('info'))
async def info_command(message: Message):
    bot_info = "Это бот для управления заказами и общения с поддержкой.\n" \
               "Он предоставляет различные функции, такие как управление ордерами и связь с поддержкой."

    await message.answer(bot_info)


# @dp.callback_query(lambda callback: callback.data == '')
# async def orders_command(message: Message):
#     user_data[message.from_user.id]: dict = {}
#     user_data[message.from_user.id]['watched_orders']: list = []
#
#     await message.answer(f"Выберите проект", reply_markup=kb.projects_kb())
#
#
# @dp.callback_query(
#     lambda callback: callback.data in [f'project_{x}' for x in ['GTA5RP', 'Majestic', 'Radmir GTA5']])
# async def handle_project_orders_callback(query: CallbackQuery, callback_data: dict):
#     user_id = query.from_user.id
#     project_name: str = callback_data['name']
#
#     user_data[user_id] = {}
#     user_data[user_id]['project'] = project_name.split('_')[0]
#
#     if project_name == 'GTA5RP_orders':
#         servers_for_project = GTA5RP_SERVERS
#     elif project_name == 'Majestic_orders':
#         servers_for_project = MAJESTIC_GTA5_SERVERS
#     elif project_name == 'Radmir GTA5_orders':
#         servers_for_project = RADMIR_GTA5_SERVERS
#     else:
#         return await query.message.edit_text("❔ Я не могу найти выбранный проект")
#
#     await query.message.edit_text(
#         f"Вы выбрали проект {project_name.split('_')[0]}. Теперь выберите сервер",
#         reply_markup=kb.orders_servers_kb(servers_for_project))
#
#
# @dp.callback_query(lambda callback: callback.data == 'back_to_projects')
# async def handle_orders_back_to_projects_callback(callback: CallbackQuery):
#     await callback.message.edit_text(f"Выберите проект", reply_markup=kb.orders_project_kb())
#
#
# @dp.callback_query(lambda callback: callback.data.startswith('orders_servers'))
# async def handle_orders_server_callback(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     server = callback.data.split('_')[-1]
#     project = user_data[user_id]['project']
#
#     orders = get_pending_sell_orders(user_id, project, server)
#
#     if not orders:
#         return await callback.message.edit_text(
#             "❔ Я не могу найти свободных ордеров, вы можете создать ордер самостоятельно, "
#             "нажав в главном меню кнопку - 'Создать заявку' ")
#
#     await callback.message.delete()
#
#     watched_orders = []
#     orders_num = 0
#     for order in orders:
#         order_id, user_id, username, action, project, server, amount, status, created_at = order
#
#         price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
#         price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) *
#         (price_per_million / 1000000))
#
#         # orders_text = f"├ ID ордера: {order_id}\n\n" \    # TODO: доделать
#         orders_text = f"├  Операция: Продажа\n" \
#                       f"├ Проект: {project}\n" \
#                       f"├ Сервер: {server}\n" \
#                       f"├ Кол-во валюты: {math.ceil(amount)}\n" \
#                       f"└ Дата создания: {convert_datetime(created_at)}\n\n" \
#                       f"Цена: {price}руб"
#
#         kb = InlineKeyboardMarkup(row_width=1)
#         kb.add(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(order_id)}'))
#
#         watched_orders.append(order_id)
#
#         if orders_num == 4:
#             kb.add(InlineKeyboardButton(
#                 text='⏬ Посмотреть ещё',
#                 callback_data=f'watch-other_{project}_{server}_{"-".join([str(el) for el in watched_orders])}')
#             )
#             return await callback.message.answer(orders_text, reply_markup=kb)
#
#         await callback.message.answer(orders_text, reply_markup=kb)
#
#         orders_num += 1
#
#
# @dp.callback_query(lambda query: query.data.startswith('watch-other_'))
# async def watch_other_callback(query: CallbackQuery):
#     user_id = query.from_user.id
#     _, project, server, watched_orders = query.data.split('_')
#     watched_orders = list(map(int, watched_orders.split('-')))
#     print(watched_orders)
#
#     kb = InlineKeyboardMarkup(row_width=1)
#     kb.add(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(watched_orders[-1])}'))
#     await query.message.edit_text(query.message.text, reply_markup=kb)
#
#     orders = get_pending_sell_orders(user_id, project, server)
#
#     if not orders:
#         return await query.message.edit_text("Выше я предоставил все ордера по вашему запросу.")
#
#     orders_num = 0
#     for order in orders:
#         order_id, user_id, username, action, project, server, amount, status, created_at = order
#
#         if order_id in watched_orders:
#             continue
#
#         price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
#         price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) *
#         (price_per_million / 1000000))
#
#         orders_text = f"├ ID ордера: {order_id}\n\n" \
#                       f"├ Операция: Продажа\n" \
#                       f"├ Проект: {project}\n" \
#                       f"├ Сервер: {server}\n" \
#                       f"├ Кол-во валюты: {math.ceil(amount)}\n" \
#                       f"└ Дата создания: {convert_datetime(created_at)}\n\n" \
#                       f"Цена: {price}руб"
#
#         kb = InlineKeyboardMarkup(row_width=1)
#         kb.add(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(order_id)}'))
#
#         if orders_num == 4:
#             kb.add(InlineKeyboardButton(
#                 text='⏬ Посмотреть ещё',
#                 callback_data=f'watch_other_{project}_{server}_{"-".join(user_data[user_id]["watched_orders"])}')
#             )
#             return await query.message.answer(orders_text, reply_markup=kb)
#
#         await query.message.answer(orders_text, reply_markup=kb)
#
#         watched_orders.append(order_id)
#         orders_num += 1
#
#
# @dp.callback_query(lambda query: query.data.startswith('buy_order_'),
#                    lambda query: query.from_user.id not in active_chats)
# async def buy_order(query: CallbackQuery):
#     kb = InlineKeyboardMarkup(row_width=1)
#     kb.add(InlineKeyboardButton(text="🤝 Да, начать чат с продавцом",
#                                 callback_data=f'confirmation_of_buying_{str(query.data.split("_")[-1])}'))
#     await query.message.edit_text(query.message.text + '\n\n🤔 Вы уверены?', reply_markup=kb)


@dp.callback_query(lambda query: query.data.startswith('confirmation_of_buying_'),
                   lambda query: query.from_user.id not in active_chats)
async def confirmation_of_buying(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]
    buyer_id = callback.from_user.id
    seller_id = get_user_id_by_order(order_id)
    matched_orders_id = create_matched_order(buyer_id, 0, seller_id, int(order_id))

    await callback.message.edit_text(callback.message.text[:-13] + '✅ Начался чат с продавцом')
    await notify_users_of_chat(matched_orders_id, buyer_id, seller_id, order_id)


@dp.callback_query(
    lambda callback: callback.data == 'admin_reports' and callback.from_user.id in admin_ids)
async def admin_reports(callback: CallbackQuery):
    complaints = get_open_reports()
    if not complaints:
        return await callback.message.edit_text("✅ Нет необработанных жалоб")
    await callback.message.delete()

    for complaint in complaints:
        _, order_id, complainer_id, offender_id, complaint_text = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        text = (f'📋 <i><u>Репорт по заказу: {str(order_id)}</u></i>\n\n'
                f'👤 Автор: {complainer_username} (<code>{complainer_id}</code>)\n'
                f'💢 Жалуется на: {offender_username} (<code>{offender_id}</code>)\n\n'
                f'<b>📝 Причина:</b>\n{complaint_text}')

        await callback.message.answer(text, parse_mode='HTML')
        # TODO: добавить кнопку для того, чтобы отреагировать на репорт


# @dp.message(
#     lambda message: message.from_user.id in user_data and 'amount' not in user_data[
#         message.from_user.id] and '/orders' != message.text and message.from_user.id not in active_chats)
# async def handle_custom_amount(message: Message):
#     user_id = message.from_user.id
#     try:
#         amount = int(message.text.replace(".", "").replace(",", ""))
#         if amount < 500000 or amount > 1000000000000:
#             await message.answer("❔ Минимальное кол-во виртуальной валюты: 500.000 ")
#             return
#
#         user_data[user_id]['amount'] = amount
#
#         action_type = user_data[user_id]['action']
#         project = user_data[user_id]['project']
#         server = user_data[user_id]['server']
#
#         price_per_million = PRICE_PER_MILLION_VIRTS[project][action_type.lower()]
#         price = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) *
#         (price_per_million / 1000000))
#
#         if action_type == 'buy':
#             action_text = "Купить"
#         elif action_type == 'sell':
#             action_text = "Продать"
#         else:
#             action_text = ""
#
#         confirm_text = (f"Ваш заказ:\n"
#                         f"├ Операция: {action_text}\n"
#                         f"├ Проект: {project}\n"
#                         f"├ Сервер: {server}\n"
#                         f"└ Количество виртов: {'{:,}'.format(amount)}\n\n"
#                         f"Итоговая цена: {'{:,}'.format(price)} руб.\n\n"
#                         f"Подтвердить?")
#
#         await message.answer(confirm_text, reply_markup=kb.confirmation_of_creation_kb())
#     except ValueError:
#         await message.answer("❔ Я не знаю таких чисел, введите пожалуйста корректное число")


def todo() -> None:
    # TODO: починить репорты (админу высылается список, в котором на 1 и тот же Id могут быть 2 разные жалобы)

    # TODO: Перед выбором проекта (где это есть) добавь выбор платформы. 2 кнопки -
    #       GTA5 и SAMP, CRMP, MTA. При выборе платформы будет перекидывать на соответствующие проекты.

    # TODO: (по технологии /orders)
    #       /ordersbiz - Выбор платформы, проекта => выдает ордера
    #       /ordersacc - Выбор платформы, проекта, сервера => выдает ордера

    # TODO: Исправить user id. На один ТГ аккаунт будет 1 user id.

    # TODO: /report
    #       ID заказа на которы подается жалоба - соединение двух ордеров, которые взаимодействуют.
    #       (это не ID order не путай!, у каждого ордера свой ордер id)
    #       Репорт будет выглядеть так - Ввод ID заказа, ввод проблемы, подтверждение.
    #       (без user id, при подачи жалобы автоматически будет браться user id противоположного человека в заказе)
    #       Пользователь может подать репорт только на свой заказ в котором он принимал или принимает участие.

    # TODO: /admin
    #       Вместе с username пользователей выводи user id обоих, выводи время создание репорта и добавь кнопки:
    #       Ответить, закрыть, забанить 1д,7д,30д, навсегда,
    #       Кнока присоединения к переписке (сделай возможность выходить из нее),
    #       Кнопки подветрждения и отмена сделки. + Кнопки с необходимой инфой.
    #       С инфой об самом ордере, об обоих пользователях, переписка.

    # TODO: support увидишь в ЛС (по аналогии с ГБ)

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

    # TODO: Баланс, платежка, fsm и тп

    pass


async def main():
    database.init_db()

    await bot.delete_webhook(drop_pending_updates=True)
    polling_task = asyncio.create_task(dp.start_polling(bot))

    await asyncio.gather(polling_task)


if __name__ == '__main__':
    asyncio.run(main())
