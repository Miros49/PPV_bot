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


async def notify_users_of_chat(deal_id: int | str, buyer_id: int | str, seller_id: int | str,
                               order_id: int | str, project: str):
    buyer_state: FSMContext = get_user_state(buyer_id)
    seller_state: FSMContext = get_user_state(seller_id)

    await buyer_state.set_state(UserStates.in_chat)
    await seller_state.set_state(UserStates.in_chat)

    order = get_order(order_id=order_id)

    item = utils.get_item_text(order[4])
    server = order[6]

    buyer_message = ('‼️ Покупатель по вашему заказу найден.\n'
                     'Начинается чат с покупателем. <a href="https://telegra.ph/Pravila-Bota-DD-07-28">Правила</a>')
    seller_message = ('‼️ Продавец по вашему заказу найден.\n'
                      'Начинается чат с продавцом. <a href="https://telegra.ph/Pravila-Bota-DD-07-28">Правила</a>')

    if order[4] == 'virt':
        item_message = f'Кол-во виртов: <code>{"{:,}".format(order[7])}</code>'
    elif order[4] == 'business':
        item_message = f'Название бизнеса: <i>{order[8]}</i>'
    else:
        item_message = f'Описание аккаунта: <i>{order[8]}</i>'

    price = utils.get_price(order_id, 'buy')
    buyer_order_ifo = LEXICON['order_info_text'].format(buyer_message, '📗', deal_id, 'Покупка',
                                                        item, project, server, item_message,
                                                        '{:,}'.format(price).replace(',', ' '))

    message_buyer = await bot.send_photo(buyer_id, FSInputFile('img/to_buyer.png'), caption=buyer_order_ifo,
                                         reply_markup=User_kb.confirmation_of_deal_buyer_kb(seller_id,
                                                                                            deal_id))

    price = utils.get_price(order_id, 'sell')
    seller_order_ifo = LEXICON['order_info_text'].format(seller_message, '📘', deal_id, 'Продажа',
                                                         item, order[5], server, item_message,
                                                         '{:,}'.format(price).replace(',', ' '))
    message_seller = await bot.send_photo(seller_id, FSInputFile('img/to_seller.png'), caption=seller_order_ifo,
                                          reply_markup=User_kb.confirmation_of_deal_seller_kb(buyer_id,
                                                                                              deal_id))

    await buyer_state.update_data({'deal_id': deal_id, 'in_chat_message_id': message_buyer.message_id,
                                   'role': 'buyer', 'in_chat_with': seller_id})
    await seller_state.update_data({'deal_id': deal_id, 'in_chat_message_id': message_seller.message_id,
                                    'role': 'seller', 'in_chat_with': buyer_id})


async def show_projects(callback: CallbackQuery, item: str, game: str, action_type: str):
    if action_type == 'sell':
        text = orders_lexicon['project'].format('📘', 'Продажа', utils.get_item_text(item), utils.get_game_text(game))
    else:
        text = show_lexicon['project'].format(utils.get_item_text(item),
                                              utils.get_game_text(game))

    await callback.message.edit_text(text, reply_markup=User_kb.projects_kb(item, game, action_type))


async def show_servers(callback: CallbackQuery, state: FSMContext, item: str, project: str, action_type: str):
    game = determine_game(project)
    if action_type == 'sell':
        if project in ['Quant RP', 'SMOTRArage']:

            text = orders_lexicon['special_1'].format('📘', 'Продажа', utils.get_item_text(item),
                                                      utils.get_game_text(utils.determine_game(project)),
                                                      project, '#1', '{}', '{}')

            if item == 'virt':
                kb = User_kb.amount_kb(project, '#1', 'sell', single_server=True)
                return await callback.message.edit_text(text.format(
                    orders_lexicon['virt_1'], orders_lexicon['virt_2']), reply_markup=kb)
            elif item == 'business':
                mes = await callback.message.edit_text(
                    text.format(orders_lexicon['business_1'], orders_lexicon['business_2']),
                    reply_markup=User_kb.order_back_to_projects(item, project, action_type))
                await state.set_state(UserStates.input_business_name)
            else:
                mes = await callback.message.edit_text(
                    text.format(orders_lexicon['account_1'], orders_lexicon['account_2']),
                    reply_markup=User_kb.order_back_to_projects(item, project, action_type))
                await state.set_state(UserStates.input_account_description)

            return await state.update_data(
                {'item': item, 'project': project, 'server': '#1', 'action_type': action_type,
                 'mes_original': mes, 'mes_original_text': text, 'attempt': True})

        text = orders_lexicon['server'].format('📘', 'Продажа', utils.get_item_text(item), utils.get_game_text(game),
                                               project)
    else:
        if project in ['Quant RP', 'SMOTRArage']:
            return await show_orders(callback, state, item, project, '#1')
        text = show_lexicon['server'].format(utils.get_item_text(item),
                                             utils.get_game_text(game), project)

    await callback.message.edit_text(text, reply_markup=User_kb.servers_kb(item, game, project, action_type))


async def show_orders(callback: CallbackQuery, state: FSMContext, item, project, server, watch_other: bool = False):
    orders = get_pending_sell_orders(callback.from_user.id, item, project, server)
    data = await state.get_data()

    if watch_other:
        await callback.message.delete()

        try:
            watched_orders = data['watched_orders']
        except KeyError:
            return await callback.answer('Эта кнопка устарела. Попробуйте ещё раз')
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
                'mes_original': (
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=User_kb.create_order_kb(key, project, server)
                    )
                ).message_id
            }

            return await state.update_data(data)

        data['watched_orders'] = {}
        await callback.message.delete()

    orders_num = 0
    for order in orders:
        order_id, _, _, _, item, _, server, amount, description, price_, status, created_at = order

        if order_id in data['watched_orders'].values():
            continue

        item_name = utils.get_item_text(item)

        if item == 'virt':
            item_text = f"Кол-во валюты: <code>{'{:,}'.format(math.ceil(amount))}</code>"

        elif item == 'business':
            item_text = f"Название бизнеса: <i>{description}</i>"
            price_ *= 1.3

        else:
            item_text = f"Описание аккаунта: <i>{description}</i>"
            price_ *= 1.3

        orders_text = LEXICON['orders_message'].format(
            id=order_id,
            item_name=item_name,
            project=project,
            server=server,
            item_text=item_text,
            price='{:,}'.format(price_).replace(',', ' ')
        )

        mes = await callback.message.answer(orders_text, reply_markup=User_kb.show_kb(order_id))

        data['watched_orders'][mes.message_id] = order_id

        orders_num += 1
        if orders_num == 4:
            mes_service = await callback.message.answer(
                text='<b>Выберите действие:</b>',
                reply_markup=User_kb.show_orders_management(len(orders) > len(data['watched_orders']))
            )
            data['service'] = mes_service.message_id
            break

    if orders_num == 0:
        print(callback.data)
        await callback.message.delete()
        await callback.answer('Эта кнопка устарела. Попробуйте ещё раз')
    elif orders_num != 4:
        mes_service = await callback.message.answer('<b>Выберите действие:</b>',
                                                    reply_markup=User_kb.show_orders_management(False))
        data['service'] = mes_service.message_id

    data['item'], data['project'], data['server'] = item, project, server
    return await state.update_data(data)


async def send_account_info(update: CallbackQuery | Message):
    user_id = update.from_user.id

    user_id, tg_id, username, phone_number, balance, created_at = get_user(user_id)
    message_text = LEXICON['account_message'].format(user_id, created_at.split()[0],
                                                     '{0:,}'.format(round(balance)).replace(',', ' '))

    if isinstance(update, Message):
        await update.answer(message_text, reply_markup=User_kb.account_kb())
    else:
        await update.message.edit_text(message_text, reply_markup=User_kb.account_kb())


async def send_information_about_order(callback: CallbackQuery, order: list, edit: bool = False,
                                       confirm: str = None):
    order_id, _, _, action, item, project, server, amount, description, price, status, created_at = order
    emoji = '📘' if action == 'sell' else '📗'
    action_text = 'Продажа' if action == 'sell' else 'Покупка'
    item_text = 'Вирты' if item == 'virt' else 'Бизнес' if item == 'business' else 'Аккаунт'
    status_text = 'Создано 🌀' if status == 'pending' else 'Выполнен ✅'
    aditional = (my_orders_lexicon[f'aditional_{item}'].format(description) if item != 'virt' else
                 my_orders_lexicon['aditional_virt'].format('{0:,}'.format(int(amount))))

    if confirm:
        kb = User_kb.confirmation_of_deleting_kb(order_id)
    else:
        kb = User_kb.cancel_order_kb(order_id) if status == 'pending' else None

    message_text = my_orders_lexicon['my_orders_message'].format(emoji, order_id, created_at, status_text,
                                                                 action_text, item_text, project, server,
                                                                 aditional,
                                                                 '{0:,}'.format(int(price)).replace(',', ' '))
    if edit:
        mes = await callback.message.edit_text(message_text, reply_markup=kb)
        return mes.message_id
    mes = await callback.message.answer(message_text, reply_markup=kb)
    return mes.message_id


async def send_my_orders(callback: CallbackQuery, state: FSMContext, target: str, watch_more: bool = False):
    orders = get_orders_by_user_id(callback.from_user.id, target)

    if orders:
        if watch_more:
            data = await state.get_data()

            if 'my_watched_orders' not in data:
                return await callback.answer('Эта кнопка уже устарела, попробуйте ещё раз', show_alert=True)

        else:
            await callback.message.delete()
            data = {'my_watched_orders': {}}

        orders_count = 0
        for order in orders:
            if order[0] in data['my_watched_orders'].values():
                continue

            data['my_watched_orders'][await send_information_about_order(callback, order)] = order[0]

            orders_count += 1
            if orders_count == 4:
                await callback.message.answer(
                    '<b>Выберите действие:</b>',
                    reply_markup=User_kb.my_orders_management(target, len(orders) > len(data['my_watched_orders']))
                )
                break

        if orders_count == 0:
            await callback.message.delete()
            await callback.answer('У вас больше нет заказов')
            await callback.message.answer('<b>Выберите действие:</b>',
                                          reply_markup=User_kb.my_orders_management(target, False))
        elif orders_count != 4:
            await callback.message.answer('<b>Выберите действие:</b>',
                                          reply_markup=User_kb.my_orders_management(target, False))

        await state.update_data(data)

    else:
        if target == 'pending':
            await callback.message.edit_text(LEXICON['no_pending_orders'], reply_markup=User_kb.to_account_kb())
        else:
            await callback.message.edit_text(LEXICON['no_confirmed_orders'], reply_markup=User_kb.to_account_kb())


def get_user_state(user_id: str | int):
    return FSMContext(
        storage, StorageKey(bot_id=int(config.tg_bot.token.split(':')[0]), chat_id=user_id, user_id=user_id)
    )
