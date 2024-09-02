import asyncio

from aiogram import Bot, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message

from core import config, bot
from database import *
from keyboards import UserKeyboards as User_kb
from lexicon import *
from states import UserStates
import utils

router: Router = Router()


@router.message(Command('cls'))
async def cls(message: Message, state: FSMContext):
    await state.clear()

    await bot.delete_message(message.chat.id, message.message_id)

    mes = await message.answer('⚙️🔧 Ваше состояние очищено')
    await asyncio.sleep(1)
    await mes.delete()


@router.message(Command('menu', 'start'), ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def start_handler(message: Message, state: FSMContext):
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


@router.callback_query(F.data.startswith('send_main_menu'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
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


@router.callback_query(F.data == 'shop_button', ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def shop_button(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['shop_message'], disable_web_page_preview=True,
                                     reply_markup=User_kb.shop_kb())


@router.callback_query(F.data == 'account_button',
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def account_button(callback: CallbackQuery, state: FSMContext):
    await utils.send_account_info(callback)
    await state.clear()


@router.callback_query(F.data == 'from_top_up_to_account',
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def from_top_up_to_account(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    user_id, tg_id, username, phone_number, balance, created_at = get_user(callback.from_user.id)
    message_text = LEXICON['account_message'].format(user_id, created_at.split()[0],
                                                     '{0:,}'.format(round(balance)).replace(',', ' '))

    await callback.message.answer(message_text, reply_markup=User_kb.account_kb())

    await state.clear()


@router.callback_query(F.data == 'shop_buy_button',
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def start_buy_button(callback: CallbackQuery):
    await callback.message.edit_text(show_lexicon['item'], reply_markup=User_kb.action_kb('show'))


@router.callback_query(F.data == 'shop_sell_button', StateFilter(default_state))
async def start_sell_button(callback: CallbackQuery):
    await callback.message.edit_text(orders_lexicon['item'].format('📘', 'Продажа'),
                                     reply_markup=User_kb.action_kb('sell'))


@router.callback_query(F.data == 'shop_create_order_button', StateFilter(default_state))
async def start_create_order_button(callback: CallbackQuery):
    await callback.message.edit_text(orders_lexicon['game'].format('📗', 'Покупка', 'Вирты'),
                                     reply_markup=User_kb.co_game_kb())


@router.callback_query(F.data.startswith('co_game'), StateFilter(default_state, UserStates.input_amount))
async def co_game(callback: CallbackQuery, state: FSMContext):
    game = callback.data.split('_')[-1]
    game_text = utils.get_game_text(game)
    await callback.message.edit_text(orders_lexicon['project'].format('📗', 'Покупка', 'Вирты', game_text),
                                     reply_markup=User_kb.co_project_kb(game))

    await state.clear() if await state.get_state() == UserStates.input_amount else None


@router.callback_query(F.data.startswith('co_project'), StateFilter(default_state))
async def co_project(callback: CallbackQuery, state: FSMContext):
    project = callback.data.split('_')[-1]
    game_text = utils.get_game_text(utils.determine_game(project))

    if project in ['Quant RP', 'SMOTRArage']:
        game_text = utils.get_game_text(utils.determine_game(project))
        await callback.message.edit_text(
            orders_lexicon['special_1'].format('📗', 'Покупка', 'Вирты', game_text, project, '#1',
                                               orders_lexicon['virt_1'],
                                               orders_lexicon['virt_2']),
            reply_markup=User_kb.co_amount_kb(project, '#1', True))
        return await state.clear()

    await callback.message.edit_text(orders_lexicon['server'].format('📗', 'Покупка', 'Вирты', game_text, project),
                                     reply_markup=User_kb.co_server_kb(project))


@router.callback_query(F.data.startswith('co_server'))
async def co_server(callback: CallbackQuery, state: FSMContext):
    project, server = callback.data.split('_')[-2], callback.data.split('_')[-1]
    game_text = utils.get_game_text(utils.determine_game(project))
    await callback.message.edit_text(
        orders_lexicon['special_1'].format('📗', 'Покупка', 'Вирты', game_text, project, server,
                                           orders_lexicon['virt_1'],
                                           orders_lexicon['virt_2']),
        reply_markup=User_kb.co_amount_kb(project, server, project in ['Quant RP', 'SMOTRArage']))
    await state.clear()


@router.callback_query(F.data.startswith('co_amount'))
async def co_amount(callback: CallbackQuery, state: FSMContext):
    _, _, project, server, amount = callback.data.split('_')
    game_text = utils.get_game_text(utils.determine_game(project))

    if amount == 'custom':
        mes = await callback.message.edit_text(
            orders_lexicon['special_1'].format('📗', 'Покупка', 'Вирты', game_text, project, server,
                                               orders_lexicon['virt_1'],
                                               orders_lexicon['virt_custom']),
            reply_markup=User_kb.co_back_to_amount(project, server, project in ['Quant RP', 'SMOTRArage'])
        )
        await state.set_state(UserStates.input_amount)
        return await state.update_data({
            'project': project, 'server': server, 'action_type': 'buy',
            'original_message_id': mes.message_id, 'attempt': True
        })

    price_ = utils.calculate_virt_price(amount, get_price_db(project, server, 'buy'))

    await callback.message.edit_text(
        text=orders_lexicon['show_order'].format('📗', 'Покупка', 'Вирты', project, server,
                                                 orders_lexicon['virt_1'], '{:,}'.format(int(amount)),
                                                 '{:,}'.format(price_).replace(',', ' '), orders_lexicon['confirm']),
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
async def handle_project_callback(callback: CallbackQuery, state: FSMContext):
    item = callback.data.split('_')[1]
    project_name = callback.data.split('_')[2]
    action_type = callback.data.split('_')[-1]

    await utils.show_servers(callback, state, item, project_name, action_type)


@router.callback_query(F.data.startswith('back_to_projects_'),
                       StateFilter(default_state, UserStates.input_business_name, UserStates.input_account_description,
                                   UserStates.input_amount))
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    _, _, _, item, game, action_type = callback.data.split('_')

    await utils.show_projects(callback, item, game, action_type)
    current_state = await state.get_state()

    if current_state in [UserStates.input_business_name, UserStates.input_account_description, UserStates.input_amount]:
        await state.clear()


@router.callback_query(F.data.startswith('back_to_servers'), StateFilter(default_state))
async def back_to_servers_handler(callback: CallbackQuery, state: FSMContext):
    _, _, _, item, project, action_type = callback.data.split('_')

    data = await state.get_data()

    await utils.show_servers(callback, state, item, project, action_type)
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
    emoji = '📘' if action_type == 'sell' else '📗'
    action_text = 'Продажа' if action_type == 'sell' else 'Покупка'

    text = orders_lexicon['special_1'].format(emoji, action_text, utils.get_item_text(item),
                                              utils.get_game_text(utils.determine_game(project)),
                                              project, server, '{}', '{}')

    if item == 'virt':
        kb = User_kb.amount_kb(project, server, action_type) if action_type == 'sell' \
            else User_kb.co_amount_kb(project, server, project in ['Quant RP', 'SMOTRArage'])
        return await callback.message.edit_text(text.format(orders_lexicon['virt_1'], orders_lexicon['virt_2']),
                                                reply_markup=kb)
    elif item == 'business':
        mes = await callback.message.edit_text(text.format(orders_lexicon['business_1'], orders_lexicon['business_2']),
                                               reply_markup=User_kb.order_back_to_servers(item, project, action_type))
        await state.set_state(UserStates.input_business_name)
    else:
        mes = await callback.message.edit_text(text.format(orders_lexicon['account_1'], orders_lexicon['account_2']),
                                               reply_markup=User_kb.order_back_to_servers(item, project, action_type))
        await state.set_state(UserStates.input_account_description)

    await state.update_data({'item': item, 'project': project, 'server': server, 'action_type': action_type,
                             'original_message_id': mes.message_id, 'attempt': True})


@router.callback_query(F.data.startswith('server_'), F.data.endswith('show'), StateFilter(default_state))
async def handle_server_show_callback(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, _ = callback.data.split('_')

    await utils.show_orders(callback, state, item, project, server)


@router.callback_query(F.data.startswith('show_orders_management'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def show_orders_management(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if 'watched_orders' not in data:
        await callback.message.delete()
        return await callback.answer('Эта кнопка устарела. Попробуйте ещё раз', show_alert=True)

    if callback.data.split('_')[-1] == 'back':

        if data['project'] not in ['Quant RP', 'SMOTRArage']:
            await utils.show_servers(callback, state, data['item'], data['project'], 'show')
        else:
            await utils.show_projects(callback, data['item'], utils.determine_game(data['project']), 'show')

        for message_id in data['watched_orders'].keys():
            try:
                await bot.delete_message(callback.from_user.id, message_id)
            except TelegramBadRequest:
                pass
    else:
        await utils.show_orders(callback, state, data['item'], data['project'], data['server'], True)


@router.callback_query(F.data.startswith('amount'), StateFilter(default_state, UserStates.input_amount))
async def handle_amount_callback(callback: CallbackQuery, state: FSMContext):
    _, amount, project, server = callback.data.split('_')

    if amount == 'custom':
        data = {'project': project, 'server': server, 'action_type': 'sell', 'attempt': True}
        text = orders_lexicon['special_1'].format(
            '📘', 'Продажа', 'Вирты', utils.get_game_text(utils.determine_game(project)),
            project, server, orders_lexicon['virt_1'], orders_lexicon['virt_custom']
        )
        kb = User_kb.order_back_to_servers('virt', project, 'sell', project in ['Quant RP', 'SMOTRArage'])

        data['original_message_id'] = (await callback.message.edit_text(text=text, reply_markup=kb)).message_id

        await state.set_state(UserStates.input_amount)
        return await state.update_data(data)

    price_ = utils.calculate_virt_price(amount, get_price_db(project, server, 'sell'))
    price_, amount = '{:,}'.format(price_).replace(',', ' '), '{:,}'.format(int(amount))

    await callback.message.edit_text(
        text=orders_lexicon['show_order'].format(
            '📘', 'Продажа', 'Вирты', project, server, 'Кол-во валюты', amount, price_, orders_lexicon['confirm']),
        reply_markup=User_kb.confirmation_of_creation_kb('virt', project, server, 'sell')
    )


@router.message(StateFilter(UserStates.input_amount))
async def input_amount(message: Message, state: FSMContext):
    data = await state.get_data()

    action_text = 'Покупка' if data['action_type'] == 'buy' else 'Продажа'
    emoji = '📘' if action_text == 'Продажа' else '📗'
    amount = message.text

    await bot.delete_message(message.chat.id, message.message_id)

    kb = User_kb.order_back_to_servers(
        'virt', data['project'], data['action_type'],
        data['project'] in ['Quant RP', 'SMOTRArage']) if data['action_type'] == 'sell' \
        else User_kb.co_back_to_amount(data['project'], data['server'], data['project'] in ['Quant RP', 'SMOTRArage'])

    if amount.isnumeric():
        if int(amount) < 500000:
            additional = orders_lexicon['virt_custom'] + orders_lexicon['virt_amount_below']
        elif int(amount) > 100000000000000:
            additional = orders_lexicon['virt_custom'] + orders_lexicon['virt_amount_above']

        else:
            price_ = utils.calculate_virt_price(amount,
                                                get_price_db(data['project'], data['server'], data['action_type']))
            price_, amount = '{:,}'.format(price_).replace(',', ' '), '{:,}'.format(int(amount))

            await bot.edit_message_text(
                text=orders_lexicon['show_order'].format(
                    emoji, action_text, 'Вирты', data['project'], data['server'], orders_lexicon['virt_1'],
                    amount, price_, orders_lexicon['confirm']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.confirmation_of_creation_kb('virt', data['project'], data['server'],
                                                                 data['action_type'])
            )
            return await state.clear()

        await bot.edit_message_text(
            text=orders_lexicon['special_1'].format(
                emoji, action_text, 'Вирты', utils.get_game_text(utils.determine_game(data['project'])),
                data['project'], data['server'], orders_lexicon['virt_1'], additional),
            chat_id=message.chat.id, message_id=data['original_message_id'],
            reply_markup=kb
        )

    else:
        attempt_text = orders_lexicon['virt_custom'] + orders_lexicon['attempt_1'] if data['attempt'] else \
            orders_lexicon['virt_custom'] + orders_lexicon['attempt_2']
        data['attempt'] = not data['attempt']

        await bot.edit_message_text(
            text=orders_lexicon['special_1'].format(
                emoji, action_text, 'Вирты', utils.get_game_text(utils.determine_game(data['project'])),
                data['project'], data['server'], orders_lexicon['virt_1'], attempt_text),
            chat_id=message.chat.id, message_id=data['original_message_id'],
            reply_markup=kb
        )

        await state.update_data(data)


@router.message(StateFilter(UserStates.input_business_name))
async def business_name(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.from_user.id, message.message_id)

    text = orders_lexicon['special_1'].format('📘', 'Продажа', utils.get_item_text(data['item']),
                                              utils.get_game_text(utils.determine_game(data['project'])),
                                              data['project'], data['server'], orders_lexicon['business_1'], '{}')
    kb = User_kb.order_back_to_servers('business', data['project'], 'sell',
                                       data['project'] in ['Quant RP', 'SMOTRArage'])

    if not message.text:
        try:
            await bot.edit_message_text(
                text=text.format(orders_lexicon['business_2'] + LEXICON['text_needed']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=kb
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    elif len(message.text) > 50:
        try:
            await bot.edit_message_text(
                text=text.format(
                    orders_lexicon['business_2'] + LEXICON['name_limit'].format(len(message.text), message.text)),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=kb
            )
        except TelegramBadRequest:
            pass
        return await state.update_data(data)

    text = orders_lexicon['special_2'].format(
        '📘', 'Продажа', 'Бизнес', utils.get_game_text(utils.determine_game(data['project'])), data['project'],
        data['server'], orders_lexicon['business_1'], message.text, '   ', orders_lexicon['business_3'])

    await bot.edit_message_text(
        text=text, chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.back_to_filling()
    )

    data['name'] = message.text

    await state.set_state(UserStates.input_business_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_business_price))
async def business_price(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.from_user.id, message.message_id)

    try:
        price_ = int(message.text)
    except ValueError:
        additional = orders_lexicon['business_3'] + orders_lexicon['attempt_1'] if data['attempt'] \
            else orders_lexicon['business_3'] + orders_lexicon['attempt_2']

        await bot.edit_message_text(
            text=orders_lexicon['special_2'].format(
                '📘', 'Продажа', 'Бизнес', utils.get_game_text(utils.determine_game(data['project'])),
                data['project'], data['server'], orders_lexicon['business_1'], data['name'], '____', additional),
            chat_id=message.chat.id, message_id=data['original_message_id'],
            reply_markup=User_kb.back_to_filling()
        )

        data['attempt'] = not data['attempt']

        return await state.update_data(data)

    await bot.edit_message_text(
        text=orders_lexicon['show_order'].format('📘', 'Продажа', 'Бизнес', data['project'],
                                                 data['server'], orders_lexicon['business_1'], data['name'],
                                                 '{:,}'.format(price_).replace(',', ' '), orders_lexicon['confirm']),
        chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.confirmation_of_creation_kb('business', data['project'], data['server'], 'sell')
    )

    await state.clear()
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_account_description))
async def account_description(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.from_user.id, message.message_id)

    text = orders_lexicon['special_1'].format('📘', 'Продажа', utils.get_item_text(data['item']),
                                              utils.get_game_text(utils.determine_game(data['project'])),
                                              data['project'], data['server'], orders_lexicon['account_1'], '{}')

    if not message.text:
        try:
            await bot.edit_message_text(
                text=text.format(orders_lexicon['account_2'] + LEXICON['text_needed']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.order_back_to_servers('account', data['project'], 'sell')
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    elif len(message.text) > 300:
        try:
            await bot.edit_message_text(
                text=text.format(
                    orders_lexicon['account_2'] + LEXICON['description_limit'].format(len(message.text), message.text)),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.order_back_to_servers('account', data['project'], 'sell')
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    text = orders_lexicon['special_2'].format('📘', 'Продажа', 'Аккаунт',
                                              utils.get_game_text(utils.determine_game(data['project'])),
                                              data['project'],
                                              data['server'], orders_lexicon['account_1'], message.text, '    ',
                                              orders_lexicon['account_3'])

    await bot.edit_message_text(
        text=text, chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.back_to_filling()
    )

    data['description'] = message.text

    await state.set_state(UserStates.input_account_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_account_price))
async def account_price(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.from_user.id, message.message_id)

    try:
        price_ = int(message.text)
    except ValueError:
        additional = orders_lexicon['account_3'] + orders_lexicon['attempt_1'] if data['attempt'] \
            else orders_lexicon['account_3'] + orders_lexicon['attempt_2']

        await bot.edit_message_text(
            text=orders_lexicon['special_2'].format(
                '📘', 'Продажа', 'Аккаунт', utils.get_game_text(utils.determine_game(data['project'])),
                data['project'], data['server'], orders_lexicon['account_1'], data['description'], '____', additional),
            chat_id=message.chat.id, message_id=data['original_message_id'],
            reply_markup=User_kb.back_to_filling()
        )

        data['attempt'] = not data['attempt']

        return await state.update_data(data)

    await bot.edit_message_text(
        text=orders_lexicon['show_order'].format('📘', 'Продажа', 'Аккаунт', data['project'],
                                                 data['server'], orders_lexicon['account_1'], data['description'],
                                                 price_, orders_lexicon['confirm']),
        chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.confirmation_of_creation_kb('account', data['project'], data['server'], 'sell')
    )

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data.startswith('confirmation_of_creation_'), StateFilter(default_state))
async def handle_deal_confirmation_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if callback.data.split('_')[-1] == 'confirm':
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

            if action_type == 'buy':
                if get_balance(user_id) < price_:
                    return await callback.message.edit_text('❕ Недостаточно средств',
                                                            reply_markup=User_kb.not_enough_money_kb())
                else:
                    edit_balance(user_id, -price_, 'buy', buy_order_creation=True)

            opposite_action_type = 'buy' if action_text == 'Продажа' else 'sell'
            opposite_price = utils.calculate_virt_price(amount, get_price_db(project, server, opposite_action_type))

            order_id = add_order(user_id, username, action_type, 'virt', project, server, amount, opposite_price,
                                 price_)

            if action_type == 'buy':
                add_transaction(user_id, amount, action_type, order_id=order_id)

            price_, amount_text = '{:,}'.format(price_), '{:,}'.format(int(amount))
            text += orders_lexicon['show_order'].format(emoji, action_text, item, project, server,
                                                        orders_lexicon['virt_1'], amount_text, price_, '')

            await callback.message.edit_text(text, reply_markup=User_kb.to_main_menu(True))

            matched_order = await match_orders(user_id, action_type, project, server, amount)
            if matched_order:
                matched_order_id, other_user_id = matched_order

                buyer_id = user_id if action_type == 'buy' else other_user_id
                seller_id = user_id if action_type == 'sell' else other_user_id
                buyer_order_id = order_id if action_type == 'buy' else matched_order_id
                seller_order_id = order_id if action_type == 'sell' else matched_order_id
                deal_id = create_deal(buyer_id, buyer_order_id, seller_id, seller_order_id)

                await utils.notify_users_of_chat(deal_id, buyer_id, seller_id, order_id, project)

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
        await callback.message.edit_text("🚫 Ваш заказ отменен.", reply_markup=User_kb.to_shop_kb())


@router.callback_query(F.data.startswith('report_'), StateFilter(UserStates.in_chat))
async def report_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    _, offender_id, order_id = callback.data.split('_')

    kb = utils.get_deal_kb(order_id, callback.from_user.id, False, data.get('show_cancel', True))
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=data['in_chat_message_id'],
                                        reply_markup=kb)

    mes = await callback.message.answer(complaint_lexicon['description'].format(order_id, ''),
                                        reply_markup=User_kb.cancel_complaint_creation_kb())
    await state.set_state(UserStates.in_chat_waiting_complaint)

    data['show_complaint']: bool = False
    data['offender_id'] = offender_id
    data['order_id'] = order_id
    data['original_message_id'] = mes.message_id
    data['in_chat_message_id'] = callback.message.message_id
    await state.update_data(data)


@router.message(StateFilter(UserStates.in_chat_waiting_complaint))
async def complaint_in_chat_callback(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if not message.text:
        try:
            await bot.edit_message_text(
                text=complaint_lexicon['description'].format(data['order_id']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.cancel_complaint_creation_kb()
            )
        except TelegramBadRequest:
            pass

        return state.update_data(data)

    if len(message.text.strip()) > 350:
        try:
            await bot.edit_message_text(
                text=complaint_lexicon['description'].format(data['order_id'],
                                                             complaint_lexicon['limit_above'].format(
                                                                 message.text[:3800])),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.back_to_complaint_kb()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    await bot.edit_message_text(
        text=complaint_lexicon['info'].format(data['order_id'], message.text),
        chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.send_complaint_kb()
    )

    data['complaint_text'] = message.text

    await state.set_state(UserStates.in_chat)
    await state.update_data(data)


@router.callback_query(F.data == 'back_to_complaint_description',
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def back_to_complaint_description_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await callback.message.edit_text(
        text=complaint_lexicon['description'].format(data['order_id']),
        reply_markup=User_kb.cancel_complaint_creation_kb()
    )

    await state.set_state(UserStates.in_chat_waiting_complaint)
    await state.update_data(data)


@router.callback_query(F.data.startswith('confirmation_of_deal'),
                       StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def handle_chat_action_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    user_id = callback.from_user.id
    deal_id = callback.data.split('_')[-1]

    buyer_id, seller_id = (user_id, data['in_chat_with']) if data['role'] == 'buyer' \
        else (data['in_chat_with'], user_id)
    other_user_id = buyer_id if user_id == seller_id else seller_id
    seller_order_id = get_deal(int(callback.data.split('_')[-1]))[4]
    buyer_order_id = get_deal(int(callback.data.split('_')[-1]))[2]

    buyer_state = utils.get_user_state(buyer_id)
    seller_state = utils.get_user_state(seller_id)

    buyer_data = await buyer_state.get_data()
    seller_data = await seller_state.get_data()

    if callback.data.split('_')[-2] == 'cancel':
        await callback.answer()

        if user_id == seller_id:
            edit_balance(buyer_id, utils.get_price(seller_order_id, 'buy'), 'buy_canceled', deal_id=deal_id)
            delete_transaction(user_id=buyer_id, deal_id=deal_id)

            await bot.send_message(buyer_id, '<b>❌ Сделка отменена продавцом.\nДеньги зачислены вам на аккаунт</b>',
                                   reply_markup=User_kb.to_main_menu_hide_kb())
            await bot.send_message(seller_id, '<b>❌ Вы отменили сделку, чат завершен</b>',
                                   reply_markup=User_kb.to_main_menu_hide_kb())

            await bot.edit_message_reply_markup(chat_id=buyer_id,
                                                message_id=buyer_data['in_chat_message_id'],
                                                reply_markup=None)
            await bot.edit_message_reply_markup(chat_id=seller_id,
                                                message_id=seller_data['in_chat_message_id'],
                                                reply_markup=None)

            try:
                update_deal_status(deal_id, 'canceled')
                update_order_status(seller_order_id, 'pending')
                if buyer_order_id != 0:
                    update_order_status(buyer_order_id, 'pending')
            except sqlite3.Error as e:
                print(f"Error updating order status to 'deleted': {e}")

        else:
            await bot.send_message(user_id, "<b>‼️ Вы предложили продавцу отменить сделку</b>")
            await bot.send_message(other_user_id, "<b>‼️ Покупатель предлагает вам отменить сделку</b>")

            kb = utils.get_deal_kb(deal_id, user_id, buyer_data.get('show_complaint', True), False)

            try:
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=callback.message.message_id,
                                                    reply_markup=kb)
            except TelegramBadRequest:
                pass

            buyer_data['show_cancel'] = False
            return await buyer_state.update_data(buyer_data)

    else:
        edit_balance(seller_id, utils.get_price(seller_order_id, 'sell'), 'sell', deal_id=deal_id)

        await bot.edit_message_reply_markup(chat_id=buyer_id, message_id=buyer_data['in_chat_message_id'],
                                            reply_markup=None)
        await bot.edit_message_reply_markup(chat_id=seller_id, message_id=seller_data['in_chat_message_id'],
                                            reply_markup=None)

        await bot.send_message(buyer_id, "<b>✅ Вы подтвердили сделку, приятной игры!</b>",
                               reply_markup=User_kb.to_main_menu_hide_kb())
        await bot.send_message(seller_id, "<b>✅ Покупатель подтвердил сделку. Деньги зачислены вам на аккаунт</b>",
                               reply_markup=User_kb.to_main_menu_hide_kb())

        utils.deal_completion(deal_id, seller_order_id, buyer_order_id)

        add_income('deal', deal_id, 'income', utils.get_income_amount(seller_order_id))

    await buyer_state.clear()
    await seller_state.clear()


@router.callback_query(F.data == 'to_main_menu_hide_kb')
async def to_main_menu_hide_handler(callback: CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        reply_markup=None)

    await callback.message.answer(LEXICON['start_message'], reply_markup=User_kb.start_kb())


@router.message(Command('report'), ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def report_command(message: Message, state: FSMContext):
    await message.answer(LEXICON['report_message'], reply_markup=User_kb.report_kb())
    await state.clear()


@router.message(StateFilter(UserStates.in_chat))
async def handle_chat_message(message: Message, state: FSMContext):
    data = await state.get_data()

    user_id = message.from_user.id
    bot_user_id = get_bot_user_id(user_id)
    buyer_id, seller_id = (user_id, data['in_chat_with']) if data['role'] == 'buyer' else (
        data['in_chat_with'], user_id)
    recipient_id = buyer_id if user_id == seller_id else seller_id

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

    save_chat_message(data['deal_id'], user_id, recipient_id, message_type, item)

    if message.text:
        return await bot.send_message(recipient_id, f"<b>Сообщение от ID {bot_user_id}:</b> {item}")

    send_method = {
        'photo': bot.send_photo,
        'video': bot.send_video,
        'sticker': bot.send_sticker,
        'voice': bot.send_voice,
        'video_note': bot.send_video_note,
        'animation': bot.send_animation,
    }

    if not caption:
        await bot.send_message(recipient_id, f"<b>Сообщение от ID {bot_user_id}:</b>")
        await send_method[message_type](recipient_id, item)

        if 'admin_id' in data:
            await bot.send_message(data[''], f"<b>Сообщение от ID {bot_user_id}:</b>")
            await send_method[message_type](recipient_id, item)

    else:
        await send_method[message_type](recipient_id, item, caption=f'<b>Сообщение от ID {bot_user_id}:</b> ' + caption)


@router.message(Command('account'), StateFilter(default_state))
async def account_info(message: Message):
    await utils.send_account_info(message)


@router.callback_query(F.data == 'my_orders', StateFilter(default_state))
async def process_my_orders(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['my_orders_message'], reply_markup=User_kb.my_orders_kb())


@router.callback_query(F.data.startswith('my_orders_management'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def my_orders_management_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if 'my_watched_orders' not in data:
        await callback.message.delete()
        return await callback.answer('Эта кнопка устарела. Попробуйте ещё раз', show_alert=True)

    if callback.data.split('_')[-1] == 'back':
        await callback.message.edit_text(LEXICON['my_orders_message'], reply_markup=User_kb.my_orders_kb())
        for message_id in data['my_watched_orders'].keys():
            try:
                await bot.delete_message(callback.from_user.id, message_id)
            except TelegramBadRequest:
                pass
        return await state.clear()

    await callback.message.delete()
    await utils.send_my_orders(callback, state, callback.data.split('_')[-1], True)


@router.callback_query(F.data.startswith('my_orders'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def my_orders_handler(callback: CallbackQuery, state: FSMContext):
    await utils.send_my_orders(callback, state, callback.data.split('_')[2], False)


@router.callback_query(F.data.startswith('transactions_management'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def transactions_button_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    transactions = get_transactions(callback.from_user.id)

    if not transactions:
        return await callback.message.edit_text('У вас ещё нет транзакций',
                                                reply_markup=User_kb.payment_back_to_account())

    max_message_length = 4096
    max_dates_per_message = 5
    messages = []
    current_message = ""
    dates_count = 0

    data['watched_transactions'] = []

    for date, trans_list in transactions:
        date_header = f"\n<b>• {date}</b>\n"
        transaction_lines = []

        for trans in trans_list:
            transaction_id, user_id, amount, action, deal_id, created_at = trans

            action_text = {
                'top_up': 'Пополнение',
                'cashout': 'Вывод средств',
                'sell': f'Покупка заказа №{deal_id}' if deal_id else 'Продажа',
                'buy': f'Продажа, заказ №{deal_id}' if deal_id else 'Покупка',
                'buy_canceled': 'Отмена продажи',
                'reduction': 'Штраф',
                'increase': 'Начисление'
            }.get(action, 'Неизвестное действие')

            if action_text == 'Неизвестное действие':  # Отлов багов
                print(f'\nОшибка в форматировании action_text транзакции №{transaction_id}\n')

            amount_str = f"{'+' if action in ['top_up', 'sell'] else ''}{amount}₽"
            transaction_str = f"<i>{created_at}</i> <code>{amount_str}</code> - <i>{action_text}</i> - (№<code>{transaction_id}</code>)\n"
            transaction_lines.append(transaction_str)

        date_section = date_header + ''.join(transaction_lines)

        if len(current_message + date_section) > max_message_length or dates_count >= max_dates_per_message:
            messages.append(current_message)
            current_message = ""
            dates_count = 0

        current_message += date_section
        dates_count += 1

    if current_message:
        messages.append(current_message)

    for text in messages:
        sent_message = await callback.message.answer(text)
        data['watched_transactions'].append(sent_message.message_id)

    await callback.message.answer('<b>Выберите действие:</b>', reply_markup=User_kb.transactions_management())

    await state.update_data(data)


@router.callback_query(F.data == 'complaints_button', StateFilter(default_state))
async def complaints_button_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(LEXICON['report_message'], reply_markup=User_kb.report_kb())
    await state.clear()


@router.callback_query(F.data == 'my_complaints', StateFilter(default_state))
async def my_complaints_handler(callback: CallbackQuery, state: FSMContext, watched_complains: list = []):
    complaints = get_complaints(callback.from_user.id)

    if not complaints:
        return await callback.message.edit_text(
            '❕  У вас нет жалоб',
            reply_markup=User_kb.back_to_complaint_kb()
        )

    await callback.message.delete()
    data = await state.get_data()

    complaints_counter, data = 0, data if 'watched_complaints' in data else {'watched_complaints': {}}
    for complaint in complaints:
        if complaint[0] in watched_complains:
            continue

        status_text = 'На рассмотрении 🌀' if complaint[5] == 'open' else 'Рассмотрено ✅'
        answer = '' if complaint[5] == 'open' else complaint_lexicon['answer'].format(complaint[6])

        text = complaint_lexicon['show_complaint'].format(
            complaint[0], complaint[7], status_text, complaint[1], complaint[4], answer
        )
        kb = User_kb.cancel_complaint_kb(complaint[0]) if complaint[5] == 'open' else None

        mes = await callback.message.answer(text, reply_markup=kb)
        data['watched_complaints'][mes.message_id] = complaint[0]

        complaints_counter += 1
        if complaints_counter == 4:
            await callback.message.answer('<b>Выберите действие:</b>', reply_markup=User_kb.complaints_management_kb(
                len(complaints) > len(data['watched_complaints'])))
            await state.update_data(data)
            break

    if complaints_counter == 0:
        await callback.answer('У вас больше нет жалоб', show_alert=True)
        await callback.message.answer('<b>Выберите действие:</b>',
                                      reply_markup=User_kb.complaints_management_kb(show_scroll=False))
        await state.update_data(data)
    elif complaints_counter != 4:
        await callback.message.answer('<b>Выберите действие:</b>',
                                      reply_markup=User_kb.complaints_management_kb(show_scroll=False))
        await state.update_data(data)


@router.callback_query(F.data.startswith('delete_complaint'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def delete_complaint_handler(callback: CallbackQuery, state: FSMContext):
    complaint_id = callback.data.split('_')[-1]

    if callback.data.split('_')[2] == 'ask':
        return await bot.edit_message_reply_markup(chat_id=callback.from_user.id,
                                                   message_id=callback.message.message_id,
                                                   reply_markup=User_kb.cancel_complaint_kb(complaint_id, True))

    if not get_complaint(complaint_id):
        await callback.message.delete()
        return await callback.answer('✅ Эта жалоба уже удалена')

    try:
        delete_complaint(complaint_id)
        await callback.answer('✅ Жалоба успешно удалена', show_alert=True)
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.answer('🤕 Что-то пошло не так, попробуйте ещё раз', show_alert=True)
        try:
            await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                                reply_markup=None)
        except TelegramBadRequest:
            pass


@router.callback_query(F.data.startswith('complaints_management'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def process_complaints_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if 'watched_complaints' not in data:
        await callback.message.delete()
        return await callback.message.answer(LEXICON['report_message'], reply_markup=User_kb.report_kb())

    watched_complaints = data['watched_complaints']

    if callback.data.split('_')[-1] == 'back':
        await callback.message.edit_text(LEXICON['report_message'], reply_markup=User_kb.report_kb())

        for message_id in watched_complaints.keys():
            try:
                await bot.delete_message(callback.from_user.id, message_id)
            except TelegramBadRequest:
                pass

        return await state.clear()

    await my_complaints_handler(callback, state, watched_complaints.values())


@router.callback_query(F.data == 'write_complaint',
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def process_write_ticket_callback(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    if get_user_deals(callback.from_user.id):
        await callback.message.delete()
        mes = await callback.message.answer(complaint_lexicon['order_id'].format(''),
                                            reply_markup=User_kb.back_to_complaint_kb())
        await state.set_state(UserStates.waiting_for_order_id)
        await state.update_data({'original_message_id': mes.message_id, 'attempt': True})

    else:
        return await callback.message.edit_text('❕ Вы не участвовали в сделках, чтобы написать жалобу.',
                                                reply_markup=User_kb.back_to_complaint_kb())


@router.message(StateFilter(UserStates.waiting_for_order_id))
async def process_order_id(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if not message.text:
        try:
            await bot.edit_message_text(
                text=complaint_lexicon['order_id'].format(LEXICON['text_needed']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.back_to_complaint_kb()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    try:
        order_id = int(message.text.strip())
    except ValueError:
        try:
            additional = complaint_lexicon['id_attempt_1'] if data['attempt'] else complaint_lexicon['id_attempt_2']
            await bot.edit_message_text(
                text=complaint_lexicon['order_id'].format(additional),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.back_to_complaint_kb()
            )

            data['attempt'] = not data['attempt']
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if not check_deal(order_id, message.from_user.id):
        try:
            await bot.edit_message_text(
                text=complaint_lexicon['order_id'].format(complaint_lexicon['no_order']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.back_to_complaint_kb()
            )
        except TelegramBadRequest:
            pass
        return await state.update_data(data)

    if user_has_complaint_on_order(message.from_user.id, order_id):
        await bot.edit_message_text(
            text=complaint_lexicon['order_id'].format(complaint_lexicon['already_exists']),
            chat_id=message.chat.id, message_id=data['original_message_id'],
            reply_markup=User_kb.back_to_complaint_kb()
        )
        return await state.update_data(data)

    await bot.edit_message_text(
        text=complaint_lexicon['description'].format(order_id, ''),
        chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.back_to_complaint_order_id()
    )

    data['order_id'] = order_id

    await state.set_state(UserStates.waiting_for_problem_description)
    await state.update_data(data)


@router.callback_query(F.data == 'back_to_complaint_order_id', StateFilter(UserStates.waiting_for_problem_description))
async def back_to_complaint_order_id_handler(callback: CallbackQuery, state: FSMContext):
    mes = await callback.message.edit_text(
        text=complaint_lexicon['order_id'].format(''),
        reply_markup=User_kb.back_to_complaint_kb()
    )

    await state.set_state(UserStates.waiting_for_order_id)
    await state.update_data({'original_message_id': mes.message_id, 'attempt': True})


@router.message(StateFilter(UserStates.waiting_for_problem_description))
async def process_problem_description(message: Message, state: FSMContext):
    data = await state.get_data()

    await bot.delete_message(message.chat.id, message.message_id)

    if not message.text:
        try:
            await bot.edit_message_text(
                text=complaint_lexicon['description'].format(data['order_id'], LEXICON['text_needed']),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.back_to_complaint_kb()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    if len(message.text.strip()) > 350:
        try:
            await bot.edit_message_text(
                text=complaint_lexicon['description'].format(
                    data['order_id'], complaint_lexicon['limit_above'].format(message.text[:3800])),
                chat_id=message.chat.id, message_id=data['original_message_id'],
                reply_markup=User_kb.back_to_complaint_kb()
            )
        except TelegramBadRequest:
            pass

        return await state.update_data(data)

    await bot.edit_message_text(
        text=complaint_lexicon['info'].format(data['order_id'], message.text) + complaint_lexicon['confirm'],
        chat_id=message.chat.id, message_id=data['original_message_id'],
        reply_markup=User_kb.send_complaint_kb()
    )

    data['complaint_text'] = message.text

    await state.clear()
    await state.update_data(data)


@router.callback_query(F.data.in_(['send_complaint', 'cancel_complaint']))
async def process_ticket_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.answer()

    if callback.data == 'send_complaint':
        complaint = get_deal(data['order_id'])
        complainer_id = callback.from_user.id
        offender_id = complaint[1] if complaint[1] != complainer_id else complaint[3]
        create_report(data['order_id'], complainer_id, offender_id, data['complaint_text'])

        text = complaint_lexicon['saved'] + complaint_lexicon['info'].format(data['order_id'], data['complaint_text'])

        await callback.message.edit_text(
            text=text,
            reply_markup=None if 'in_chat_message_id' in data else User_kb.complaints_to_main_menu()
        )

        if await state.get_state() != UserStates.in_chat:
            await state.clear()

        for admin_id in config.tg_bot.admin_ids:
            try:
                await bot.send_message(admin_id, '‼️ Поступил репорт\n/admin')
            except Exception as e:
                print(f'Ошибка при попытке оповещения админа о новой жалобе: {str(e)}')

    else:
        if await state.get_state() != UserStates.in_chat:
            return await callback.message.edit_text("Вы отменили создание жалобы.",
                                                    reply_markup=User_kb.back_to_complaint_kb())

        kb = utils.get_deal_kb(data['order_id'], callback.from_user.id, True, data.get('show_cancel', True))

        await bot.edit_message_reply_markup(
            chat_id=callback.from_user.id, message_id=data['in_chat_message_id'], reply_markup=kb
        )
        await callback.message.delete()
        await callback.answer('Создание жалобы отменено')

        data['show_complaint']: bool = True

        await state.update_data(data)


@router.callback_query(F.data.startswith('complaints_to_main_menu'),
                       ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def process_complaints_to_main_menu(callback: CallbackQuery, state: FSMContext):
    data = utils.parse_complaint(callback.message.text)

    await callback.message.edit_text(
        complaint_lexicon['saved'] + complaint_lexicon['info'].format(data['deal_id'], data['description']))

    await start_handler(callback.message, state)


@router.callback_query(F.data == 'cancel_complaint_button')
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    data = await state.get_data()

    kb = utils.get_deal_kb(data['order_id'], callback.from_user.id, True, data.get('show_cancel', True))
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=data['in_chat_message_id'],
                                        reply_markup=kb)
    data['show_complaint']: bool = True
    await state.update_data(data)

    await callback.message.delete()
    await callback.answer('✅ Отправка жалобы отменена', show_alert=True)

    await state.set_state(UserStates.in_chat)
    await state.update_data(data)


@router.message(Command('myorders'), StateFilter(default_state))
async def my_orders_command(message: Message):
    await message.answer(LEXICON['my_orders_message'], reply_markup=User_kb.my_orders_kb())


@router.callback_query(F.data == 'support_button', StateFilter(default_state))
async def support_callback(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['support_message'], reply_markup=User_kb.support_kb())


@router.message(Command('support', 'help'), ~StateFilter(UserStates.in_chat, UserStates.in_chat_waiting_complaint))
async def support_command(message: Message):
    await message.answer(LEXICON['support_message'], reply_markup=User_kb.support_kb())


@router.callback_query(F.data.startswith('buy_order_'), StateFilter(default_state))
async def buy_order(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]

    if utils.get_price(order_id, 'buy') > get_balance(callback.from_user.id):
        await callback.answer()
        return await callback.message.answer(f'❕ Недостаточно средств', reply_markup=User_kb.not_enough_money_kb(False))

    await callback.message.edit_text(
        text=callback.message.text + '\n\n🤔 Вы уверены?',
        reply_markup=User_kb.buy_order_kb(order_id)
    )


@router.callback_query(F.data.startswith('confirmation_of_buying_'), StateFilter(default_state))
async def confirmation_of_buying(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split('_')[-1]
    seller_id = get_user_id_by_order(order_id)
    data = await state.get_data()
    seller_state = await utils.get_user_state(seller_id).get_state()

    if seller_state == UserStates.in_chat or seller_state == UserStates.in_chat_waiting_complaint:
        return await callback.answer(LEXICON['seller_busy'], show_alert=True)

    if 'watched_orders' in data:
        for message_id in data['watched_orders'].keys():
            await bot.delete_message(callback.from_user.id, message_id)
        await bot.delete_message(callback.from_user.id, data['service'])

    if utils.get_price(order_id, 'buy') > get_balance(callback.from_user.id):
        await callback.answer()
        return await callback.message.answer('❕ Недостаточно средств', reply_markup=User_kb.not_enough_money_kb())

    buyer_id = callback.from_user.id

    deal_id = create_deal(buyer_id, 0, seller_id, int(order_id))

    edit_balance(buyer_id, -utils.get_price(order_id, 'buy'), 'buy', deal_id=deal_id)

    await utils.notify_users_of_chat(deal_id, buyer_id, seller_id, order_id, data['project'])


@router.callback_query(F.data.startswith('cancel_order_'), StateFilter(default_state))
async def cancel_order_handler(callback: CallbackQuery):
    order = get_order(int(callback.data.split('_')[-1]))
    await utils.send_information_about_order(callback, order, True, confirm='\n\nПодтвердите удаление')


@router.callback_query(F.data.startswith('confirmation_of_deleting_'), StateFilter(default_state))
async def confirmation_of_deleting(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]
    order = get_order(order_id)

    try:
        delete_order(callback.data.split('_')[-1])
        await callback.message.delete()
        await callback.answer('✅ Ваш заказ удалён', show_alert=True)

        if order[3] == 'buy':
            delete_transaction(user_id=callback.from_user.id, order_id=order_id)

    except Exception as e:
        await callback.answer('Что-то пошло не так...')
        print(f'Ошибка при попытке удаления заказа: {str(e)}')
        print(callback)


@router.callback_query(F.data == 'back_to_filling')
async def back_to_filling_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    text = orders_lexicon['special_1'].format('📘', 'Продажа', utils.get_item_text(data['item']),
                                              utils.get_game_text(utils.determine_game(data['project'])),
                                              data['project'], data['server'], '{}', '{}')
    kb = User_kb.order_back_to_servers(data['item'], data['project'], data['action_type'],
                                       data['project'] in ['Quant RP', 'SMOTRArage'])

    if data['project'] not in ['Quant RP', 'SMOTRArage']:
        if await state.get_state() == UserStates.input_business_price:
            await callback.message.edit_text(
                text=text.format(orders_lexicon['business_1'], orders_lexicon['business_2']),
                reply_markup=kb
            )

            await state.set_state(UserStates.input_business_name)

        else:
            await callback.message.edit_text(
                text=text.format(orders_lexicon['account_1'], orders_lexicon['account_2']),
                reply_markup=kb
            )

            await state.set_state(UserStates.input_account_description)

    else:
        if data['item'] == 'business':
            await callback.message.edit_text(
                text.format(orders_lexicon['business_1'], orders_lexicon['business_2']),
                reply_markup=kb
            )

            await state.set_state(UserStates.input_business_name)

        else:
            await callback.message.edit_text(
                text.format(orders_lexicon['account_1'], orders_lexicon['account_2']),
                reply_markup=kb
            )

            await state.set_state(UserStates.input_account_description)

    await state.update_data(data)


@router.callback_query(F.data.startswith('btls'), StateFilter(default_state))
async def back_to_last_step_handler(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, action_type = callback.data.split('_')
    data = await state.get_data()

    text = orders_lexicon['special_2'].format(
        '📘', 'Продажа', utils.get_item_text(data['item']),
        utils.get_game_text(utils.determine_game(data['project'])),
        data['project'], data['server'], '{}', '{}', '    ', '{}')

    if item == 'business':
        await callback.message.edit_text(
            text=text.format(orders_lexicon['business_1'], data['name'], orders_lexicon['business_3']),
            reply_markup=User_kb.back_to_filling()
        )

        await state.set_state(UserStates.input_business_price)

    else:
        await callback.message.edit_text(
            text=text.format(orders_lexicon['account_1'], data['description'], orders_lexicon['account_3']),
            reply_markup=User_kb.back_to_filling()
        )

        await state.set_state(UserStates.input_account_price)

    await state.update_data(data)


@router.callback_query(F.data.startswith('view_answer'), StateFilter(default_state))
async def view_answer_handler(callback: CallbackQuery):
    complaint = get_complaint(callback.data.split('_')[-1])

    text = complaint_lexicon['show_complaint'].format(
        complaint[0], complaint[7], 'Рассмотрено ✅', complaint[1], complaint[4],
        complaint_lexicon['answer'].format(complaint[6])
    )

    await callback.message.edit_text(text)


def todo() -> None:
    # TODO: /admin
    #       Вместе с username пользователей выводи user id обоих, выводи время создание репорта и добавь кнопки:
    #       Ответить, закрыть, забанить 1д,7д,30д, навсегда,
    #       Кнока присоединения к переписке (сделай возможность выходить из нее),
    #       Кнопки подветрждения и отмена сделки. + Кнопки с необходимой инфой.
    #       С инфой об самом ордере, об обоих пользователях, переписка.

    # TODO: говнокод в F.data == back_to_filling

    # TODO: не могу пользоваться старой кнопкой, после перезаписи юзердаты

    pass
