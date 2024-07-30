from aiogram import Bot, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.base import StorageKey

import utils
from database import *
from filters import *
from keyboards import UserKeyboards as User_kb
from lexicon import *
from states import UserStates

config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)

router: Router = Router()


@router.message(Command('menu', 'start'))
async def start(message: Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    await message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())
    await state.clear()

    if not get_user(message.from_user.id):
        user = message.from_user
        phone_number = None
        database.add_user(user.id, user.username, phone_number)


@router.message(Command('shop'), StateFilter(default_state))
async def shop_command_handler(message: Message):
    await message.answer(LEXICON['shop_message'], disable_web_page_preview=True, reply_markup=User_kb.shop_kb())


@router.callback_query(F.data == 'hide_button')
async def hide_button_handler(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(F.data == 'back_to_menu', StateFilter(default_state))
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['start_message'], reply_markup=User_kb.start_kb())


@router.callback_query(F.data.startswith('send_main_menu'))
async def send_main_menu_handler(callback: CallbackQuery):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    key = callback.data.split('_')[-1]
    if key == 'True':
        data = utils.parse_message_order(callback.message.text)
        if not data:
            await callback.message.edit_text(callback.message.text)
            return await callback.message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())

        await callback.message.edit_text(utils.get_order_seved_text(data))
        await callback.message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())
    else:
        await callback.message.edit_text(LEXICON['start_message'], reply_markup=User_kb.start_kb())


@router.callback_query(F.data == 'shop_button', StateFilter(default_state))
async def shop_button(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['shop_message'], disable_web_page_preview=True,
                                     reply_markup=User_kb.shop_kb())


@router.callback_query(F.data == 'account_button', StateFilter(default_state))
async def account_button(callback: CallbackQuery):
    await utils.send_account_info(callback)


@router.callback_query(F.data == 'shop_buy_button', StateFilter(default_state))
async def start_buy_button(callback: CallbackQuery):
    await callback.message.edit_text(show_lexicon['item'], reply_markup=User_kb.action_kb('show'))


@router.callback_query(F.data == 'shop_sell_button', StateFilter(default_state))
async def start_sell_button(callback: CallbackQuery):
    await callback.message.edit_text(orders_lexicon['item'].format('📘', 'Продажа'), reply_markup=User_kb.action_kb('sell'))


@router.callback_query(F.data == 'shop_create_order_button', StateFilter(default_state))
async def start_create_order_button(callback: CallbackQuery):
    await callback.message.edit_text(orders_lexicon['game'].format('📗', 'Покупка', 'Вирты'),
                                     reply_markup=User_kb.co_game_kb())


@router.callback_query(F.data.startswith('co_game'), StateFilter(default_state))
async def co_game(callback: CallbackQuery):
    game = callback.data.split('_')[-1]
    game_text = utils.get_game_text(game)
    await callback.message.edit_text(orders_lexicon['project'].format('📗', 'Покупка', 'Вирты', game_text),
                                     reply_markup=User_kb.co_project_kb(game))


@router.callback_query(F.data.startswith('co_project'), StateFilter(default_state))
async def co_project(callback: CallbackQuery):
    project = callback.data.split('_')[-1]
    game_text = utils.get_game_text(utils.determine_game(project))
    await callback.message.edit_text(orders_lexicon['server'].format('📗', 'Покупка', 'Вирты', game_text, project),
                                     reply_markup=User_kb.co_server_kb(project))


@router.callback_query(F.data.startswith('co_server'), StateFilter(default_state))
async def co_server(callback: CallbackQuery):
    project, server = callback.data.split('_')[-2], callback.data.split('_')[-1]
    game_text = utils.get_game_text(utils.determine_game(project))
    await callback.message.edit_text(
        orders_lexicon['special_1'].format('📗', 'Покупка', 'Вирты', game_text, project, server,
                                           orders_lexicon['virt_1'],
                                           orders_lexicon['virt_2']),
        reply_markup=User_kb.co_amount_kb(project, server))


@router.callback_query(F.data.startswith('co_amount'), StateFilter(default_state))
async def co_amount(callback: CallbackQuery, state: FSMContext):
    _, _, project, server, amount = callback.data.split('_')
    game_text = utils.get_game_text(utils.determine_game(project))

    if amount == 'custom':
        await callback.message.edit_text(
            orders_lexicon['special_1'].format('📗', 'Покупка', 'Вирты', game_text, project, server,
                                               orders_lexicon['virt_1'],
                                               orders_lexicon['virt_custom']))
        await state.set_state(UserStates.input_amount)
        return await state.update_data({'project': project, 'server': server, 'action_type': 'buy'})

    price_ = utils.calculate_virt_price(amount, get_price_db(project, server, 'buy'))

    await callback.message.edit_text(
        text=orders_lexicon['show_order'].format('📗', 'Покупка', 'Вирты', project, server,
                                                 orders_lexicon['virt_1'], '{:,}'.format(int(amount)),
                                                 '{:,}'.format(price_), orders_lexicon['confirm']),
        reply_markup=User_kb.confirmation_of_creation_kb('virt', project, server, 'buy')
    )


@router.callback_query(F.data == 'shop_autoposter_discord_button', StateFilter(default_state))
async def autoposter_discord_button(callback: CallbackQuery):
    await callback.message.edit_text('Soon..', reply_markup=User_kb.back_to_menu_kb())


@router.callback_query(F.data == 'back_to_shop', StateFilter(default_state))
async def back_to_shop(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['shop_message'], disable_web_page_preview=True,
                                     reply_markup=User_kb.shop_kb())


@router.callback_query(F.data.startswith('virt_'), StateFilter(default_state))
async def handle_virt_callback(callback: CallbackQuery):
    text = show_lexicon['game'].format('Вирты')
    if callback.data.split('_')[-1] == 'sell':
        text = orders_lexicon['game'].format('📘', 'Продажа', 'Вирты')

    await callback.message.edit_text(
        text=text,
        reply_markup=User_kb.game_kb('virt', callback.data.split('_')[-1])
    )


@router.callback_query(F.data.startswith('business_'), StateFilter(default_state))
async def handle_business_callback(callback: CallbackQuery):
    text = show_lexicon['game'].format('Бизнес')
    if callback.data.split('_')[-1] == 'sell':
        text = orders_lexicon['game'].format('📘', 'Продажа', 'Бизнес')

    await callback.message.edit_text(
        text=text,
        reply_markup=User_kb.game_kb('business', callback.data.split('_')[-1])
    )


@router.callback_query(F.data.startswith('account_'), StateFilter(default_state))
async def handle_business_callback(callback: CallbackQuery):
    text = show_lexicon['game'].format('Аккаунт')
    if callback.data.split('_')[-1] == 'sell':
        text = orders_lexicon['game'].format('📘', 'Продажа', 'Аккаунт')

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

    text = show_lexicon['game']
    if action_type == 'sell':
        text = orders_lexicon['game'].format('📘', 'Продажа', '{}')

    await callback.message.edit_text(text.format(utils.get_item_text(item)),
                                     reply_markup=User_kb.game_kb(item, action_type))


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


@router.callback_query(F.data.startswith('back_to_servers'))
async def back_to_servers_handler(callback: CallbackQuery, state: FSMContext):
    _, _, _, item, project, action_type = callback.data.split('_')

    data = await state.get_data()
    if 'mes' in data:
        mes_to_delete: Message = data['mes']
        await mes_to_delete.delete()
        data['latest_mes'] = mes_to_delete
        del data['mes']

    await utils.show_servers(callback, item, project, action_type)
    await state.clear()
    await state.update_data(data)


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

    text = orders_lexicon['special_1'].format('📘', 'Продажа', utils.get_item_text(item),
                                              utils.get_game_text(utils.determine_game(project)),
                                              project, server, '{}', '{}')

    if item == 'virt':
        return await callback.message.edit_text(text.format(orders_lexicon['virt_1'], orders_lexicon['virt_2']),
                                                reply_markup=User_kb.amount_kb(project, server, action_type))
    elif item == 'business':
        text = text.format(orders_lexicon['business_1'], orders_lexicon['business_2'])
        mes = await callback.message.edit_text(text,
                                               reply_markup=User_kb.order_back_to_servers(item, project, action_type))
        await state.set_state(UserStates.input_business_name)
    else:
        text = text.format(orders_lexicon['account_1'], orders_lexicon['account_2'])
        mes = await callback.message.edit_text(text,
                                               reply_markup=User_kb.order_back_to_servers(item, project, action_type))
        await state.set_state(UserStates.input_account_description)

    await state.update_data({'item': item, 'project': project, 'server': server, 'action_type': action_type,
                             'mes_original': mes, 'mes_original_text': text})


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
        data = {'project': project, 'server': server, 'action_type': 'sell', 'attempt': True}
        text = orders_lexicon['special_1'].format(
            '📘', 'Продажа', 'Вирты', utils.get_game_text(utils.determine_game(project)),
            project, server, orders_lexicon['virt_1'], orders_lexicon['virt_custom']
        )
        data['mes_original'] = \
            await callback.message.edit_text(
                text=text,
                reply_markup=User_kb.order_back_to_servers('virt', project, 'sell')
            )

        await state.set_state(UserStates.input_amount)
        return await state.update_data(data)

    price_ = utils.calculate_virt_price(amount, get_price_db(project, server, 'sell'))
    price_, amount = '{:,}'.format(price_), '{:,}'.format(int(amount))

    await callback.message.edit_text(
        text=orders_lexicon['show_order'].format(
            '📘', 'Продажа', 'Вирты', project, server, 'Кол-во валюты', amount, price_, orders_lexicon['confirm']),
        reply_markup=User_kb.confirmation_of_creation_kb('virt', project, server, 'sell')
    )


@router.message(StateFilter(UserStates.input_amount))
async def input_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes_original']
    amount = message.text
    await bot.delete_message(message.chat.id, message.message_id)
    if amount.isnumeric():
        if int(amount) < 500000:
            additional = orders_lexicon['virt_custom'] + orders_lexicon['virt_amount_below']
        elif int(amount) > 100000000000000:
            additional = orders_lexicon['virt_custom'] + orders_lexicon['virt_amount_above']
        else:
            price_ = utils.calculate_virt_price(amount,
                                                get_price_db(data['project'], data['server'], data['action_type']))
            price_, amount = '{:,}'.format(price_), '{:,}'.format(int(amount))

            action_text = 'Покупка' if data['action_type'] == 'buy' else 'Продажа'
            emoji = '📘' if action_text == 'Продажа' else '📗'

            await mes.edit_text(
                text=orders_lexicon['show_order'].format(
                    emoji, action_text, 'Вирты', data['project'], data['server'], orders_lexicon['virt_1'],
                    amount, price_, orders_lexicon['confirm']),
                reply_markup=User_kb.confirmation_of_creation_kb('virt', data['project'], data['server'],
                                                                 data['action_type'])
            )
            return await state.clear()

        await mes.edit_text(orders_lexicon['special_1'].format(
            '📘', 'Продажа', 'Вирты', utils.get_game_text(utils.determine_game(data['project'])),
            data['project'], data['server'], orders_lexicon['virt_1'], additional),
            reply_markup=User_kb.order_back_to_servers('virt', data['project'], 'sell')
        )

    else:
        attempt_text = orders_lexicon['virt_custom'] + orders_lexicon['virt_attempt_1'] if data['attempt'] else \
            orders_lexicon['virt_custom'] + orders_lexicon['virt_attempt_2']
        data['attempt'] = not data['attempt']

        await mes.edit_text(orders_lexicon['special_1'].format(
            '📘', 'Продажа', 'Вирты', utils.get_game_text(utils.determine_game(data['project'])),
            data['project'], data['server'], orders_lexicon['virt_1'], attempt_text
        ), reply_markup=User_kb.order_back_to_servers('virt', data['project'], 'sell'))
        await state.update_data(data)


@router.message(StateFilter(UserStates.input_business_name))
async def business_name(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes_original']

    if 'mes' in data:
        mes_to_delete: Message = data['mes']
        await bot.delete_message(message.from_user.id, mes_to_delete.message_id + 1)
        await mes_to_delete.delete()
    else:
        if 'latest_mes' in data:
            latest_mes: Message = data['latest_mes']
            await bot.delete_message(message.from_user.id, latest_mes.message_id + 1)
        else:
            try:
                await bot.delete_message(message.from_user.id, mes.message_id + 1)
            except TelegramBadRequest:
                pass

    if not message.text:
        data['mes'] = await message.answer(LEXICON['text_needed'])
        return await state.update_data(data)
    elif len(message.text) > 50:
        data['mes'] = await message.answer(LEXICON['name_limit'].format(len(message.text), message.text))
        return await state.update_data(data)

    await mes.delete()

    text = orders_lexicon['special_2'].format('📘', 'Продажа', 'Бизнес',
                                              utils.get_game_text(utils.determine_game(data['project'])),
                                              data['project'],
                                              data['server'], orders_lexicon['business_1'], message.text, '____',
                                              orders_lexicon['business_3'])

    data['mes_original'] = await message.answer(text, reply_markup=User_kb.back_to_filling())
    # data['mes_original_text'] = text
    data['name'] = message.text
    if 'mes' in data:
        del data['mes']
    await state.clear()
    await state.set_state(UserStates.input_business_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_business_price))
async def business_price(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes_original']

    if 'mes' in data:
        mes_to_delete: Message = data['mes']
        await bot.delete_message(message.from_user.id, mes_to_delete.message_id + 1)
        await mes_to_delete.delete()
    else:
        try:
            await bot.delete_message(message.from_user.id, mes.message_id + 1)
        except TelegramBadRequest:
            pass

    try:
        price_ = int(message.text)
    except ValueError:
        data['mes'] = await message.answer('<u>Цена должна быть числом</u>')
        return await state.update_data(data)

    await mes.edit_text(
        orders_lexicon['show_order'].format('📘', 'Продажа', 'Бизнес', data['project'],
                                            data['server'], orders_lexicon['business_1'], data['name'], price_,
                                            orders_lexicon['confirm']),
        reply_markup=User_kb.confirmation_of_creation_kb('business', data['project'], data['server'], 'sell')
    )
    await state.clear()


@router.message(StateFilter(UserStates.input_account_description))
async def account_description(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes_original']

    if 'mes' in data:
        mes_to_delete: Message = data['mes']
        await bot.delete_message(message.from_user.id, mes_to_delete.message_id + 1)
        await mes_to_delete.delete()
    else:
        if 'latest_mes' in data:
            latest_mes: Message = data['latest_mes']
            await bot.delete_message(message.from_user.id, latest_mes.message_id + 1)
        else:
            try:
                await bot.delete_message(message.from_user.id, mes.message_id + 1)
            except TelegramBadRequest:
                pass

    if not message.text:
        data['mes'] = await message.answer(LEXICON['text_needed'])
        return await state.update_data(data)
    elif len(message.text) > 300:
        data['mes'] = await message.answer(LEXICON['description_limit'].format(len(message.text), message.text))
        return await state.update_data(data)

    await mes.delete()

    text = orders_lexicon['special_2'].format('📘', 'Продажа', 'Аккаунт',
                                              utils.get_game_text(utils.determine_game(data['project'])),
                                              data['project'],
                                              data['server'], orders_lexicon['account_1'], message.text, '____',
                                              orders_lexicon['account_3'])
    data['mes_original'] = await message.answer(text, reply_markup=User_kb.back_to_filling())
    data['description'] = message.text
    # data['mes_original_text'] = text
    if 'mes' in data:
        del data['mes']
    await state.clear()
    await state.set_state(UserStates.input_account_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_account_price))
async def account_price(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes_original']

    if 'mes' in data:
        mes_to_delete: Message = data['mes']
        await bot.delete_message(message.from_user.id, mes_to_delete.message_id + 1)
        await mes_to_delete.delete()
    else:
        try:
            await bot.delete_message(message.from_user.id, mes.message_id + 1)
        except TelegramBadRequest:
            pass

    try:
        price_ = int(message.text)
    except ValueError:
        data['mes'] = await message.answer('<u>Цена должна быть числом</u>')
        return await state.update_data(data)

    await mes.edit_text(
        text=orders_lexicon['show_order'].format('📘', 'Продажа', 'Аккаунт', data['project'],
                                                 data['server'], orders_lexicon['account_1'], data['description'],
                                                 price_, orders_lexicon['confirm']),
        reply_markup=User_kb.confirmation_of_creation_kb('account', data['project'], data['server'], 'sell'))
    await state.clear()


@router.callback_query(F.data == 'cancel_button')
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
        text = orders_lexicon['saved']

        if item == 'virt':
            data = utils.parse_message_order(callback.message.text)
            if not data:
                return await callback.message.edit_text("Кажется, что-то пошло не так...")
            action_text, item, project, server, price_, amount = data.values()
            action_type = 'sell' if action_text == 'Продажа' else 'buy'
            emoji = '📘' if action_type == 'sell' else '📗'

            if action_type == 'buy' and get_balance(user_id) < price_:
                return await callback.message.edit_text('Недостаточно средств')
            else:
                edit_balance(user_id, -price_)

            opposite_action_type = 'buy' if action_text == 'Продажа' else 'sell'
            opposite_price = utils.calculate_virt_price(amount, get_price_db(project, server, opposite_action_type))

            order_id = add_order(user_id, username, action_type, 'virt', project, server, amount, opposite_price,
                                 price_)

            price_, amount = '{:,}'.format(price_), '{:,}'.format(int(amount))
            text += orders_lexicon['show_order'].format(emoji, action_text, item, project, server,
                                                        orders_lexicon['virt_1'], amount, price_, '')

            await callback.message.edit_text(text, reply_markup=User_kb.to_main_menu(True))

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
            data = utils.parse_message_order(callback.message.text)
            if not data:
                return await callback.message.edit_text("Кажется, что-то пошло не так...")

            action_text, item, project, server, price_, name = data.values()
            action_type = 'sell' if action_text == 'Продажа' else 'buy'
            emoji = '📘' if action_type == 'sell' else '📗'

            add_order(user_id, username, action_type, 'business', project, server, None, name, price_)

            text += orders_lexicon['show_order'].format(
                emoji, action_text, item, project, server,
                orders_lexicon['business_1'], name, '{:,}'.format(int(price_)), ''
            )

            await callback.message.edit_text(text, reply_markup=User_kb.to_main_menu(True))

        else:
            data = utils.parse_message_order(callback.message.text)
            if not data:
                return await callback.message.edit_text("Кажется, что-то пошло не так...")

            action_text, item, project, server, price_, description, = data.values()
            action_type = 'sell' if action_text == 'Продажа' else 'buy'
            emoji = '📘' if action_type == 'sell' else '📗'

            add_order(user_id, username, action_type, 'account', project, server, None, description, price_)

            text += orders_lexicon['show_order'].format(
                emoji, action_text, item, project, server,
                orders_lexicon['account_1'], description, '{:,}'.format(int(price_)), '')

            await callback.message.edit_text(text, reply_markup=User_kb.to_main_menu(True))

    else:
        await callback.message.edit_text("🚫 Ваш заказ отменен.", reply_markup=User_kb.to_main_menu())


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

    await callback.message.answer('‼️ Подробно опишите суть проблемы:')


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
            await bot.send_message(seller_id, "🚫 Вы отменили сделку.")

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
            await bot.send_message(user_id, "‼️ Вы предложили продавцу отменить сделку.")
            await bot.send_message(other_user_id, "‼️ Покупатель предлагает вам отменить сделку.")

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

            await bot.send_message(buyer_id, "✅ Вы подтвердили сделку. Сделка успешно завершена.")
            await bot.send_message(seller_id, "✅ Покупатель подтвердил сделку. Средства начислены в ваш кошёлек.")

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
    await utils.send_my_orders(callback)


@router.callback_query(F.data == 'complaints_button')
async def handle_complaints_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(LEXICON['report_message'], reply_markup=User_kb.report_kb())
    await state.clear()


@router.message(Command('report'))
async def report_command(message: Message, state: FSMContext):
    await message.answer(LEXICON['report_message'], reply_markup=User_kb.report_kb())
    await state.clear()


@router.callback_query(F.data == 'write_ticket')
async def process_write_ticket_callback(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    if get_user_matched_orders(callback.from_user.id):
        await callback.message.delete()
        mes = await callback.message.answer("‼️ Напишите ID сделки, на которую хотите подать жалобу",
                                            reply_markup=User_kb.back_to_complaint_kb())
        await state.set_state(UserStates.waiting_for_order_id)

    else:
        mes = await callback.message.edit_text('❕ Вы не участвовали в сделках, чтобы написать на них жалобу')
    await state.update_data({'mes': mes})


@router.callback_query(F.data == 'my_tickets')
async def process_my_tickets_callback(callback: CallbackQuery):
    reports = get_complaints(callback.from_user.id)

    if not reports:
        return await callback.message.edit_text('❕ Вы не подавали жалоб.')

    text = ''
    for report in reports:
        text += LEXICON['report'].format(*report)

    await callback.message.edit_text(text)


@router.message(StateFilter(UserStates.waiting_for_order_id))
async def process_order_id(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes']
    try:
        await mes.edit_text(mes.text)
    except TelegramBadRequest:
        pass
    if not message.text:
        await message.answer('Введите, пожалуйста, id сделки', reply_markup=User_kb.back_to_complaint_kb())
    try:
        order_id = int(message.text.strip())
    except ValueError:
        data['mes'] = await message.answer("❕ Сделки с данным ID не существует. Попробуйте ещё раз",
                                           reply_markup=User_kb.back_to_complaint_kb())
        return await state.update_data(data)

    if not check_matched_order(order_id, message.from_user.id):
        data['mes'] = await message.answer("❕ Вы не принимали участие в сделке с данным ID.",
                                           reply_markup=User_kb.back_to_complaint_kb())
        return await state.update_data(data)

    await state.set_state(UserStates.waiting_for_problem_description)

    mes = await message.answer("‼️ Подробно опишите суть проблемы:", reply_markup=User_kb.back_to_complaint_kb())
    await state.update_data({'order_id': order_id, 'mes': mes})


# @router.callback_query(F.data == 'cancel_complaint_button')
# async def cancel_callback(callback: CallbackQuery, state: FSMContext):
#     await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
#     await callback.message.edit_text('🗑 Отправка жалобы отменена')
#     await state.clear()


@router.message(StateFilter(UserStates.waiting_for_problem_description))
async def process_problem_description(message: Message, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes']
    try:
        await mes.edit_text(mes.text)
    except TelegramBadRequest:
        pass
    complaint_text = message.text
    if not complaint_text:
        return await message.answer('Описание проблемы должно быть текстом. Попробуйте ещё раз',
                                    reply_markup=User_kb.back_to_complaint_kb())

    data['complaint_text'] = complaint_text
    await state.clear()
    await state.update_data(data)

    await message.answer("Выберите действие:", reply_markup=User_kb.send_report_kb())


@router.callback_query(F.data.in_(['send_ticket', 'cancel_ticket']))
async def process_ticket_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == 'send_ticket':
        data = await state.get_data()
        complaint = get_matched_order(data['order_id'])
        complainer_id = callback.from_user.id
        offender_id = complaint[1] if complaint[1] != complainer_id else complaint[3]
        create_report(data['order_id'], complainer_id, offender_id, data['complaint_text'])

        await callback.message.edit_text(
            "✅ Жалоба успешно отправлена. Ожидайте ответа от администрации.")
        await state.clear()

        for admin_id in config.tg_bot.admin_ids:
            try:
                await bot.send_message(admin_id, '‼️ Поступил репорт\n/admin')
            except Exception as e:
                print(f'Ошибка при попытке оповещения админа о новой жалобе: {str(e)}')

    elif callback.data == 'cancel_ticket':
        await callback.message.edit_text("Вы отменили создание жалобы.", reply_markup=User_kb.back_to_menu_kb())


@router.message(Command('help'), StateFilter(default_state))
async def help_command(message: Message):
    await message.answer(LEXICON['help_message'])


@router.message(Command('myorders'), StateFilter(default_state))
async def my_orders_command(message: Message):
    await utils.send_my_orders(message)


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
        return await callback.message.answer('❕ Недостаточно средств')

    buyer_id = callback.from_user.id
    edit_balance(buyer_id, -utils.get_price(order_id, 'buy'))

    seller_id = get_user_id_by_order(order_id)
    matched_orders_id = create_matched_order(buyer_id, 0, seller_id, int(order_id))

    await callback.message.edit_text(callback.message.text[:-13] + '✅ Начался чат с продавцом')
    await utils.notify_users_of_chat(bot, matched_orders_id, buyer_id, seller_id, order_id)


@router.callback_query(F.data.startswith('cancel_order_'))
async def cancel_order_handler(callback: CallbackQuery):
    await callback.message.edit_text('пока что не кликабельно :(')


@router.callback_query(F.data == 'back_to_filling')
async def back_to_filling_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mes: Message = data['mes_original']
    if 'mes' in data:
        mes_to_delete: Message = data['mes']
        await mes_to_delete.delete()

    data['mes_original'] = await mes.edit_text(
        data['mes_original_text'],
        reply_markup=User_kb.order_back_to_servers(data['item'], data['project'], data['action_type'])
    )

    if await state.get_data() == UserStates.input_business_price:
        await state.set_state(UserStates.input_business_name)
    else:
        await state.set_state(UserStates.input_account_description)


@router.callback_query(F.data.startswith('btls'))
async def back_to_last_step_handler(callback: CallbackQuery):
    _, item, project, action_type = callback.data.split('_')
    if item == 'business':
        # text = orders_lexicon['special_2'].format('Продажа', 'Бизнес',
        #                                           utils.get_game_text(utils.determine_game(data['project'])),
        #                                           data['project'],
        #                                           data['server'], orders_lexicon['business_1'], message.text, '____',
        #                                           orders_lexicon['business_3'])
        #
        # data['mes_original'] = await message.answer(text, reply_markup=User_kb.back_to_filling())

        pass


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


@router.message(StateFilter(default_state))
async def deleting_unexpected_messages(message: Message):
    await bot.delete_message(message.from_user.id, message.message_id)


@router.callback_query()
async def kalosbornik(callback: CallbackQuery, state: FSMContext):
    print(callback.data)
    print(await state.get_state(), await state.get_data(), sep='\n\n')
