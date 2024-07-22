import math

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


@router.callback_query(F.data == 'start_buy_button', StateFilter(default_state))
async def start_buy_button(callback: CallbackQuery):
    await callback.message.edit_text('текст', reply_markup=User_kb.action_kb('show'))


@router.callback_query(F.data == 'start_sell_button', StateFilter(default_state))
async def start_sell_button(callback: CallbackQuery):
    await callback.message.edit_text('Выберите позицию, которую хотите продать',
                                     reply_markup=User_kb.action_kb('sell'))


@router.callback_query(F.data == 'start_create_order_button', StateFilter(default_state))
async def start_create_order_button(callback: CallbackQuery):
    await callback.message.edit_text('Выберите позицию, для которой хотите создать заявку на покупку',
                                     reply_markup=User_kb.action_kb('buy'))


@router.callback_query(F.data == 'start_autoposter_discord_button', StateFilter(default_state))
async def autoposter_discord_button(callback: CallbackQuery):
    await callback.message.edit_text('Soon..', reply_markup=User_kb.back_to_start_kb())


@router.callback_query(F.data == 'back_to_start', StateFilter(default_state))
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['start_message'], reply_markup=User_kb.start_kb())


@router.callback_query(F.data.startswith('virt_'), StateFilter(default_state))
async def handle_virt_callback(callback: CallbackQuery):
    action_type = callback.data.split('_')[-1]
    action_text = "приобрести" if action_type in ['buy', 'show'] else "продать"

    await callback.message.edit_text(f"Выберите платформу, где хотите {action_text} виртуальную валюту.",
                                     reply_markup=User_kb.game_kb('virt', action_type))


@router.callback_query(F.data.startswith('business_'), StateFilter(default_state))
async def handle_business_callback(callback: CallbackQuery):
    action_type = callback.data.split('_')[-1]
    action_text = "приобрести" if action_type in ['buy', 'show'] else "продать"

    await callback.message.edit_text(f"Выберите платформу, где хотите {action_text} бизнес",
                                     reply_markup=User_kb.game_kb('business', action_type))


@router.callback_query(F.data.startswith('account_'), StateFilter(default_state))
async def handle_business_callback(callback: CallbackQuery):
    action_type = callback.data.split('_')[-1]
    action_text = "приобрести" if action_type in ['buy', 'show'] else "продать"
    print(action_type, action_text)
    await callback.message.edit_text(f"Выберите платформу, где хотите {action_text} аккаунт.",
                                     reply_markup=User_kb.game_kb('account', action_type))


@router.callback_query(F.data.startswith('game_'), StateFilter(default_state))
async def game_callback_handler(callback: CallbackQuery, state: FSMContext):
    action_type = callback.data.split('_')[-1]
    game = callback.data.split('_')[1]
    item = callback.data.split('_')[2]
    projects_list = PROJECTS[game]

    await callback.message.edit_text('теперь пикни проект',
                                     reply_markup=User_kb.projects_kb(item, projects_list, action_type))

    await state.clear()


@router.callback_query(F.data.startswith('back_to_games_'), StateFilter(default_state))
async def back_to_games_callback(callback: CallbackQuery):
    item = callback.data.split('_')[-2]
    action_type = callback.data.split('_')[-1]
    action_text = "приобрести" if action_type in ['buy', 'show'] else "продать"

    await callback.message.edit_text(f"Выберите проект на котором хотите {action_text}",
                                     reply_markup=User_kb.game_kb(item, action_type))


@router.callback_query(F.data.startswith('project_'), StateFilter(default_state))
async def handle_project_callback(callback: CallbackQuery, state: FSMContext):
    item = callback.data.split('_')[1]
    project_name = callback.data.split('_')[2]
    action_type = callback.data.split('_')[-1]

    await utils.show_servers(callback, item, project_name, action_type)
    await state.clear()


@router.callback_query(F.data.startswith('back_to_projects_'), StateFilter(default_state))
async def handle_main_menu_callback(callback: CallbackQuery):
    _, _, _, item, game, action_type = callback.data.split('_')
    projects_list = PROJECTS[game]
    action_text = "приобрести" if action_type in ['buy', 'show'] else "продать"
    item_text = utils.get_item_text_projects(item)

    await callback.message.edit_text(
        text=LEXICON['choose_project'].format(action_text, item_text),
        reply_markup=User_kb.projects_kb(item, projects_list, action_type))


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
    _, item, project_name, server_name, action_type = callback.data.split('_')
    action_text = "приобрести" if action_type == 'buy' else "продать"

    if item == 'virt':
        await callback.message.edit_text(
            f"Вы выбрали проект {project_name}, сервер {server_name}. "
            f"Теперь выберите количество виртуальной валюты, которое хотите {action_text}:",
            reply_markup=User_kb.amount_kb(project_name, server_name, action_type))
    elif item == 'business':
        await callback.message.edit_text(LEXICON['input_business_name'])
        await state.set_state(UserStates.input_business_name)
        await state.update_data({'project': project_name, 'server': server_name, 'action_type': action_type})
    elif item == 'account':
        await callback.message.edit_text(LEXICON['input_account_description'])
        await state.set_state(UserStates.input_account_description)
        await state.update_data({'project': project_name, 'server': server_name, 'action_type': action_type})


@router.callback_query(F.data.startswith('server_'), F.data.endswith('show'), StateFilter(default_state))
async def handle_server_show_callback(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, _ = callback.data.split('_')

    await utils.show_orders(callback, state, item, project, server)


@router.callback_query(F.data.startswith('watch-other'))
async def watch_other_handler(callback: CallbackQuery, state: FSMContext):
    _, item, project, server, _ = callback.data.split('_')

    await utils.show_orders(callback, state, item, project, server, True, callback.data.split('_')[-1])


@router.callback_query(F.data.startswith('amount_'), StateFilter(default_state))
async def handle_amount_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    amount_value = callback.data.split('_')[1]

    if amount_value == 'custom':
        await bot.send_message(callback.from_user.id, "Введите нужное количество виртуальной валюты:")
        await callback.message.delete()
    else:
        amount = int(amount_value)
        if amount < 500000 or amount > 1000000000000:
            await bot.send_message(user_id, "🤕 Количество виртуальной валюты должно быть от 500,000")
            return await callback.answer()

        action_type = callback.data.split('_')[-1]
        project = callback.data.split('_')[2]
        server = callback.data.split('_')[3]
        try:
            price_per_million = PRICE_PER_MILLION_VIRTS[project][action_type]
        except KeyError:
            price_per_million = 100
        cost = math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))

        action_text = 'Купить' if action_type == 'buy' else 'Продать'

        confirm_text = (f"Ваш заказ:\n"
                        f"├ Операция: {action_text}\n"
                        f"├ Проект: {project}\n"
                        f"├ Сервер: {server}\n"
                        f"└ Количество виртов: {'{:,}'.format(amount)}\n\n"
                        f"Итоговая цена: {'{:,}'.format(cost)} руб.\n\n"
                        f"Подтвердить?")
        await callback.message.edit_text(
            text=confirm_text,
            reply_markup=User_kb.confirmation_of_creation_kb('virt')
        )

    await callback.answer()


@router.message(StateFilter(UserStates.input_business_name))
async def business_name(message: Message, state: FSMContext):
    await message.answer(LEXICON['input_business_price'])
    data = await state.get_data()
    data['name'] = message.text
    await state.set_state(UserStates.input_business_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_business_price))
async def business_price(message: Message, state: FSMContext):
    try:
        price_ = int(message.text)
    except ValueError:
        return await message.answer(LEXICON['incorrect_price'])

    data = await state.get_data()
    await message.answer(
        text=LEXICON['confirm_text_business'].format(data['project'], data['server'], data['name'], price_),
        reply_markup=User_kb.confirmation_of_creation_kb('business')
    )
    await state.clear()


@router.message(StateFilter(UserStates.input_account_description))
async def account_description(message: Message, state: FSMContext):
    await message.answer(LEXICON['input_account_price'])
    data = await state.get_data()
    data['description'] = message.text
    await state.set_state(UserStates.input_account_price)
    await state.update_data(data)


@router.message(StateFilter(UserStates.input_account_price))
async def account_price(message: Message, state: FSMContext):
    try:
        price_ = int(message.text)
    except ValueError:
        return await message.answer(LEXICON['incorrect_price'])

    data = await state.get_data()
    await message.answer(
        text=LEXICON['confirm_text_account'].format(data['project'], data['server'], data['description'], price_),
        reply_markup=User_kb.confirmation_of_creation_kb('account')
    )
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

            action_text, project, server, amount = data.values()
            action_text = 'sell' if action_text == 'Продать' else 'buy'
            order_id = add_order(user_id, username, action_text, item, project, server, amount)

            await callback.message.edit_text("✅ Ваш заказ подтвержден и сохранен. Ожидайте ответа.")

            matched_order = match_orders(user_id, action_text, project, server, amount)
            if matched_order:
                matched_order_id, other_user_id = matched_order

                buyer_id = user_id if action_text == 'buy' else other_user_id
                seller_id = user_id if action_text == 'sell' else other_user_id
                buyer_order_id = order_id if action_text == 'buy' else matched_order_id
                seller_order_id = order_id if action_text == 'sell' else matched_order_id
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


@router.callback_query(F.data.startswith('confirmation_of_deal_'))
async def handle_chat_action_callback(callback: CallbackQuery, state: FSMContext):
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

            buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
            seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

            await buyer_state.clear()
            await seller_state.clear()

            try:
                await bot.delete_message(buyer_id, cancel_requests[chat_id]['buyer_message_id'])
            except Exception:
                pass
            del cancel_requests[chat_id]

            try:
                update_order_status(buyer_id, 'pending')
                update_order_status(seller_id, 'pending')
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

                buyer_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=buyer_id, user_id=buyer_id))
                seller_state = FSMContext(storage, StorageKey(bot_id=7488450312, chat_id=seller_id, user_id=seller_id))

                await buyer_state.clear()
                await seller_state.clear()

                await bot.delete_message(seller_id, cancel_requests[chat_id]['seller_message_id'])
                del cancel_requests[chat_id]

                try:
                    update_order_status(buyer_id, 'pending')
                    update_order_status(seller_id, 'pending')
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
    user_id = message.from_user.id
    user_db_data = get_user(user_id)

    if user_db_data:
        user_id, tg_id, username, phone_number, balance, created_at = user_db_data
        account_info_text = f"Данные вашего аккаунта:\n\n" \
                            f"├ Баланс: {balance}\n" \
                            f"├ User ID: {user_id}\n" \
                            f"├ Username: {username}\n" \
                            f"└ Дата регистрации в боте: {created_at}\n"

        await message.answer(account_info_text, reply_markup=User_kb.account_kb())

    else:
        await message.answer("❔ Я не могу найти ваши данные")


@router.callback_query(F.data == 'my_orders', StateFilter(default_state))
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
        orders_text = "🤕 У вас пока нет ордеров."

    await callback_query.answer()
    await callback_query.message.answer(orders_text)


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
    await callback.message.edit_text('✅ Отправка жалобы отменена')


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


@router.message(Command('support'))
async def support_command(message: Message):
    await message.answer(LEXICON['support_message'], reply_markup=User_kb.support_kb())


@router.callback_query(F.data == 'contact_support', StateFilter(default_state))
async def contact_support_handler(callback: CallbackQuery):
    await callback.message.edit_text('текст')


@router.message(Command('info'), StateFilter(default_state))
async def info_command(message: Message):
    await message.answer(LEXICON['info_message'])


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
#                           (price_per_million / 1000000))
#
#         orders_text = ''
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
@router.callback_query(F.data.startswith('buy_order_'), StateFilter(default_state))
async def buy_order(callback: CallbackQuery):
    await callback.message.edit_text(
        text=callback.message.text + '\n\n🤔 Вы уверены?',
        reply_markup=User_kb.buy_order_kb(callback.data.split('_')[-1])
    )


@router.callback_query(F.data.startswith('confirmation_of_buying_'), StateFilter(default_state))
async def confirmation_of_buying(callback: CallbackQuery):
    order_id = callback.data.split('_')[-1]
    buyer_id = callback.from_user.id
    seller_id = get_user_id_by_order(order_id)
    matched_orders_id = create_matched_order(buyer_id, 0, seller_id, int(order_id))

    await callback.message.edit_text(callback.message.text[:-13] + '✅ Начался чат с продавцом')
    await utils.notify_users_of_chat(bot, matched_orders_id, buyer_id, seller_id, order_id)


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
#                           (price_per_million / 1000000))
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

    # TODO: Баланс, платежка

    # TODO: gmt +3

    # TODO: Нужно везде сделать ограничение по виртам. Минимум 500000 максимум 100000000000,
    #  и так же по цене, минимум 100 рублей максимум 1000000

    pass
