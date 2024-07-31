import math

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup

import utils
from core import *
from database import *
from keyboards import UserKeyboards as User_kb
from lexicon import *
from states import UserStates
from utils import determine_game

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

    cost = str(utils.get_price(order_id, 'buy'))
    buyer_order_ifo = LEXICON['order_info_text'].format(buyer_message, str(matched_orders_id), 'Покупка', project,
                                                        server, item_message, cost)

    await bot.send_photo(buyer_id, FSInputFile('img/to_buyer.png'), caption=buyer_order_ifo)

    cost = str(utils.get_price(order_id, 'sell'))
    seller_order_ifo = LEXICON['order_info_text'].format(seller_message, str(matched_orders_id), 'Продажа', project,
                                                         server, item_message, cost)
    await bot.send_photo(seller_id, FSInputFile('img/to_seller.png'), caption=seller_order_ifo)


async def notify_users_of_chat(bot: Bot, matched_orders_id: int | str, buyer_id: int | str, seller_id: int | str,
                               order_id: int | str):
    action_message = "Выберите действие:"
    chat_id = f"{buyer_id}_{seller_id}"
    active_chats[buyer_id] = chat_id
    active_chats[seller_id] = chat_id
    cancel_requests[chat_id] = {buyer_id: False, seller_id: False}

    buyer_state = FSMContext(storage, StorageKey(bot_id=7324739366, chat_id=buyer_id, user_id=buyer_id))
    seller_state = FSMContext(storage, StorageKey(bot_id=7324739366, chat_id=seller_id, user_id=seller_id))

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


async def show_projects(callback: CallbackQuery, item: str, game: str, action_type: str):
    if action_type == 'sell':
        text = orders_lexicon['project'].format('📘', 'Продажа', utils.get_item_text(item), utils.get_game_text(game))
    else:
        text = show_lexicon['project'].format(utils.get_item_text(item),
                                              utils.get_game_text(game))

    await callback.message.edit_text(text, reply_markup=User_kb.projects_kb(item, game, action_type))


async def show_servers(callback: CallbackQuery, item: str, project: str, action_type: str):
    game = determine_game(project)
    if action_type == 'sell':
        text = orders_lexicon['server'].format('📘', 'Продажа', utils.get_item_text(item), utils.get_game_text(game),
                                               project)
    else:
        text = show_lexicon['server'].format(utils.get_item_text(item),
                                             utils.get_game_text(game), project)

    await callback.message.edit_text(text, reply_markup=User_kb.servers_kb(item, game, project, action_type))


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
            text = show_lexicon['no_orders'].format(
                utils.get_item_text(item), utils.get_game_text(utils.determine_game(project)), project, server)
            key = False
            if item == 'virt':
                text += show_lexicon['create_order']
                key = True

            data = {
                'project': project, 'server': server, 'action_type': 'sell', 'attempt': True,
                'mes_original': await callback.message.edit_text(
                    text=text,
                    reply_markup=User_kb.create_ordeer_kb(key, project, server)
                )
            }

            return await state.update_data(data)

        watched_orders = []
        await callback.message.delete()

    orders_num = 0
    for order in orders:
        order_id, _, _, _, item, project, server, amount, description, price_, status, created_at = order

        if order_id in watched_orders:
            continue

        if item == 'virt':
            item_text = f"Кол-во валюты: {math.ceil(amount)}"

        elif item == 'business':
            item_text = f"Название бизнеса: {description}"
            price_ *= 1.3
        else:
            item_text = f"Описание аккаунта: {description}"
            price_ *= 1.3

        orders_text = LEXICON['orders_message'].format(
            id=order_id,
            project=project,
            server=server,
            item_text=item_text,
            created_at=created_at,
            price=price_
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
        message_text = LEXICON['account_message'].format(user_id, created_at.split()[0], '{0:,}'.format(round(balance)))
        reply_markup = User_kb.account_kb()
    else:
        message_text = "❔ Я не могу найти ваши данные"
        reply_markup = None

    if isinstance(update, Message):
        await update.answer(message_text, reply_markup=reply_markup)
    else:
        await update.message.edit_text(message_text, reply_markup=reply_markup)


async def send_my_orders(update: CallbackQuery | Message):
    orders = get_orders_by_user_id(update.from_user.id)

    async def send_order_message(update_method, order):
        order_id, _, _, action, item, project, server, amount, description, price, status, created_at = order
        action_text = 'Продажа' if action == 'sell' else 'Покупка'
        item_text = 'Вирты' if item == 'virt' else 'Бизнес' if item == 'business' else 'Аккаунт'
        status_text = 'Создано 🌀' if status == 'pending' else ''
        kb = User_kb.cancel_order_kb(order_id) if status == 'pending' else User_kb.hide_order_kb()
        aditional = (LEXICON[f'aditional_{item}'].format(description) if item != 'virt' else
                     LEXICON['aditional_virt'].format('{0:,}'.format(int(amount))))
        message_text = LEXICON['my_orders_message'].format(order_id, created_at, status_text, action_text, item_text,
                                                           project, server, '{0:,}'.format(int(price)), aditional)
        await update_method(message_text, reply_markup=kb)

    if orders:
        if isinstance(update, CallbackQuery):
            await update.message.delete()
            update_method = update.message.answer
        else:
            update_method = update.answer

        for order in orders:
            await send_order_message(update_method, order)
    else:
        if isinstance(update, CallbackQuery):
            await update.message.edit_text("❕ Вы не создавали заказов.")
        else:
            await update.answer("❕ Вы не создавали заказов.")


#
#
#
#
#
# ----------  Функции управления кнопками в чате между продавцом и покупателем  -----------
#
#
#
#

async def handle_cancel_action(callback: CallbackQuery, user_id: int, buyer_id: int, seller_id: int, other_user_id: int,
                               chat_id: str, seller_order_id: int, buyer_order_id: int):
    cancel_requests[chat_id][user_id] = True
    await callback.answer()

    if user_id == seller_id:
        await cancel_deal_for_seller(buyer_id, seller_id, chat_id, seller_order_id, buyer_order_id)
    else:
        await request_buyer_cancellation(user_id, other_user_id, chat_id, buyer_id, seller_id, seller_order_id,
                                         buyer_order_id)


async def cancel_deal_for_seller(bot: Bot, buyer_id: int, seller_id: int, chat_id: str, seller_order_id: int,
                                 buyer_order_id: int):
    clear_active_chats(buyer_id, seller_id)
    await clear_states(buyer_id, seller_id)
    edit_balance(buyer_id, utils.get_price(seller_order_id, 'buy'))

    await bot.send_message(buyer_id, "🚫 Сделка отменена продавцом.")
    await bot.send_message(seller_id, "🚫 Сделка отменена.")

    try:
        await bot.delete_message(buyer_id, cancel_requests[chat_id]['buyer_message_id'])
    except Exception:
        pass
    del cancel_requests[chat_id]

    update_order_status_safe(seller_order_id, buyer_order_id, 'pending')


async def request_buyer_cancellation(bot: Bot, user_id: int, other_user_id: int, chat_id: str, buyer_id: int,
                                     seller_id: int, seller_order_id: int, buyer_order_id: int):
    await bot.send_message(user_id, LEXICON['I_want_to_cancel_deal'])
    await bot.send_message(other_user_id, LEXICON['buyer_want_to_cancel_deal'])

    if cancel_requests[chat_id][other_user_id]:
        await cancel_deal_for_seller(buyer_id, seller_id, chat_id, seller_order_id, buyer_order_id)


async def handle_confirm_action(bot: Bot, callback: CallbackQuery, user_id: int, buyer_id: int, seller_id: int,
                                chat_id: str, seller_order_id: int, buyer_order_id: int):
    if user_id == buyer_id:
        edit_balance(seller_id, utils.get_price(seller_order_id, 'sell'))
        cancel_requests[chat_id][user_id] = True

        await bot.delete_message(buyer_id, callback.message.message_id)
        await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])

        await bot.send_message(buyer_id, "✅ Сделка подтверждена вами.")
        await bot.send_message(seller_id, "✅ Покупатель подтвердил сделку. Сделка завершена.")

        update_order_status_safe(seller_order_id, buyer_order_id, 'confirmed')
        clear_active_chats(buyer_id, seller_id)
        del cancel_requests[chat_id]
        await clear_states(buyer_id, seller_id)


def clear_active_chats(buyer_id: int, seller_id: int):
    del active_chats[buyer_id]
    del active_chats[seller_id]


async def clear_states(buyer_id: int, seller_id: int):
    buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
    seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

    await buyer_state.clear()
    await seller_state.clear()


def update_order_status_safe(seller_order_id: int, buyer_order_id: int, status: str):
    try:
        update_order_status(seller_order_id, status)
        if buyer_order_id != 0:
            update_order_status(buyer_order_id, status)
    except sqlite3.Error as e:
        print(f"Error updating order status to '{status}': {e}")


async def modify_message(message: Message, state: FSMContext, text: str, kb: InlineKeyboardMarkup):
    data = await state.get_data()

    data['mes_original'] = await message.edit_text(
        text.format(orders_lexicon['account_2'] + LEXICON['text_needed']),
        reply_markup=kb
    )
    print(2)

    return await state.update_data(data)

    # except TelegramBadRequest:
    #     pass
