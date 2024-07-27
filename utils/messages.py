import math

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message

from core import *
from database import *
from keyboards import UserKeyboards as User_kb
from lexicon import *
from states import UserStates
from utils import determine_game, get_item_text_servers

config: Config = load_config('.env')


async def send_order_info(bot: Bot, matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str,
                          order_id: int | str):
    order = get_order(order_id=order_id)

    project = order[5]
    server = order[6]
    amount = int(order[7])

    buyer_message = "‼️ Я нашел продавца по вашему заказу. Начинаю ваш чат с продавцом.\n\n"
    seller_message = "‼️ Я нашел покупателя по вашему заказу. Начинаю ваш чат с покупателем.\n\n"

    item_message = f'Кол-во виртов: <code>{amount}</code>'
    if order[4] == 'business':
        item_message = f'Название бизнеса: <i>{order[8]}</i>'
    elif order[4] == 'account':
        item_message = f'Описание аккаунта: <i>{order[8]}</i>'

    cost = str(get_db_price(order_id, 'buy'))
    buyer_order_ifo = LEXICON['order_info_text'].format(buyer_message, str(matched_orders_id), 'Покупка', project,
                                                        server, item_message, cost)
    await bot.send_message(buyer_id, buyer_order_ifo, parse_mode='HTML')

    cost = str(get_db_price(order_id, 'sell'))
    seller_order_ifo = LEXICON['order_info_text'].format(seller_message, str(matched_orders_id), 'Продажа', project,
                                                         server, item_message, cost)
    await bot.send_message(seller_id, seller_order_ifo, parse_mode='HTML')


async def notify_users_of_chat(bot: Bot, matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str,
                               order_id: int | str):
    action_message = "Выберите действие:"
    chat_id = f"{buyer_id}_{seller_id}"
    active_chats[buyer_id] = chat_id
    active_chats[seller_id] = chat_id
    cancel_requests[chat_id] = {buyer_id: False, seller_id: False}

    buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
    seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

    await buyer_state.set_state(UserStates.in_chat)
    await seller_state.set_state(UserStates.in_chat)

    await send_order_info(bot, matched_orders_id, buyer_id, seller_id, order_id)

    message_buyer = await bot.send_message(
        chat_id=buyer_id,
        text=action_message,
        reply_markup=User_kb.confirmation_of_deal_buyer_kb(seller_id, matched_orders_id)
    )

    message_seller = await bot.send_message(
        chat_id=seller_id,
        text=action_message,
        reply_markup=User_kb.confirmation_of_deal_seller_kb(buyer_id, matched_orders_id)
    )

    cancel_requests[chat_id]['buyer_message_id'] = message_buyer.message_id
    cancel_requests[chat_id]['seller_message_id'] = message_seller.message_id


async def show_servers(callback: CallbackQuery, item: str, project_name: str, action_type: str):
    try:
        servers_for_project = SERVERS[project_name]
    except KeyError:
        return await callback.message.edit_text("Нет информации о серверах")

    action_text = "покупки" if action_type in ['buy', 'show'] else "продажи"
    game = determine_game(project_name)

    await callback.message.edit_text(
        f"Вы выбрали проект {project_name}. Выберите сервер для {action_text} {get_item_text_servers(item)}:",
        reply_markup=User_kb.servers_kb(item, game, project_name, servers_for_project, action_type))


async def show_orders(callback: CallbackQuery, state: FSMContext, item, project, server, watch_other: bool = False,
                      order_id=''):
    orders = get_pending_sell_orders(callback.from_user.id, item, project, server)
    if watch_other:
        data = await state.get_data()
        await callback.message.edit_text(callback.message.text,
                                         reply_markup=User_kb.show_kb(order_id, item, project, server))
        try:
            watched_orders = data['watched_orders']
        except KeyError:
            return await callback.message.answer('Что-то пошло не так, попробуйте ещё раз')
    else:
        if not orders:
            return await callback.message.edit_text(
                text="❔ Я не могу найти свободных ордеров, вы можете создать ордер самостоятельно",
                reply_markup=User_kb.create_ordeer_kb()
            )

        await callback.message.delete()
        watched_orders = []

    orders_num = 0
    for order in orders:
        order_id, _, _, _, item, project, server, amount, description, status, created_at = order

        if order_id in watched_orders:
            continue

        if item == 'virt':
            item_text = f"Кол-во валюты: {math.ceil(amount)}"

            try:
                price_per_million = PRICE_PER_MILLION_VIRTS[project]["buy"]
            except KeyError:
                price_per_million = 100

            amount = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) *
                               (price_per_million / 1000000))
        elif item == 'business':
            item_text = f"Название бизнеса: {description}"
            amount *= 1.3
        else:
            item_text = f"Описание аккаунта: {description}"
            amount *= 1.3

        orders_text = LEXICON['orders_message'].format(
            id=order_id,
            project=project,
            server=server,
            item_text=item_text,
            created_at=created_at,
            price=amount
        )

        watched_orders.append(order_id)

        if orders_num == 4 and len(orders) > 5:
            await callback.message.answer(orders_text,
                                          reply_markup=User_kb.show_kb(order_id, item, project, server, True))
            return await state.update_data({'watched_orders': watched_orders})

        await callback.message.answer(orders_text, reply_markup=User_kb.show_kb(order_id, item, project, server))
        orders_num += 1


async def send_account_info(update: CallbackQuery | Message):
    user_id = update.from_user.id
    user_db_data = get_user(user_id)

    if user_db_data:
        user_id, tg_id, username, phone_number, balance, created_at = user_db_data
        message_text = LEXICON['account_message'].format('{0:,}'.format(round(balance)), user_id, username, created_at)
        reply_markup = User_kb.account_kb()
    else:
        message_text = "❔ Я не могу найти ваши данные"
        reply_markup = None

    if isinstance(update, Message):
        await update.answer(message_text, reply_markup=reply_markup)
    else:
        await update.message.answer(message_text, reply_markup=reply_markup)
