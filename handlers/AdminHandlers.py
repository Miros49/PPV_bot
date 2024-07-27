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
from keyboards import AdminKeyboards as Admin_kb
from lexicon import *
from states import AdminStates

config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)

router: Router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command('admin'), StateFilter(default_state))
async def admin(message: Message):
    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)

    await message.answer(f'Здравствуйте, {message.from_user.username}! 😊', reply_markup=Admin_kb.menu_kb())


@router.callback_query(F.data == 'back_to_admin_menu')
async def back_to_menu(callback: CallbackQuery):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    await callback.message.edit_text(f'Здравствуйте, {callback.from_user.username}! 😊', reply_markup=Admin_kb.menu_kb())


@router.callback_query(F.data == 'admin_reports', StateFilter(default_state))
async def admin_reports(callback: CallbackQuery):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    open_complaints = get_open_complaints()

    if not open_complaints:
        return await callback.message.edit_text("✅ Нет необработанных жалоб")
    await callback.message.delete()

    for complaint in open_complaints:
        complaint_id, order_id, complainer_id, offender_id, complaint_text, created_at = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        await callback.message.answer(
            LEXICON['admin_report'].format(str(order_id), str(complaint_id), complainer_username, complainer_id,
                                           offender_username,
                                           offender_id, complaint_text, created_at))
        # TODO: добавить кнопку для того, чтобы отреагировать на репорт


@router.callback_query(F.data == 'admin_information')
async def admin_information(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)

    await callback.message.edit_text('Выберите критерий поиска:', reply_markup=Admin_kb.information_kb())
    await state.clear()


@router.callback_query(F.data.startswith('admin_information'))
async def admin_information_by(callback: CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, ChatAction.TYPING)
    argument = target_map.get(callback.data.split('_')[-1])

    await callback.message.edit_text(LEXICON['admin_information'].format(argument),
                                     reply_markup=Admin_kb.back_to_information_kb())
    await state.set_state(AdminStates.input_id)
    await state.update_data({'target': callback.data.split('_')[-1]})


@router.message(StateFilter(AdminStates.input_id))
async def send_information(message: Message, state: FSMContext):
    try:
        target_id = int(message.text)
    except ValueError:
        return await message.reply_text(LEXICON['incorrect_value'])

    data = await state.get_data()
    if data['target'] == 'user':
        user = get_user_by_id(target_id)
        await message.answer(information['user'].format(*user))
    elif data['target'] == 'order':
        order = get_order(target_id)
    elif data['target'] == 'matched-order':
        matched_order = get_matched_order(target_id)
    elif data['target'] == 'report':
        report = get_report(target_id)
    else:
        await message.answer('Will be soon')
        await state.clear()


@router.callback_query(F.data.in_(['admin_edit_price', 'back_to_games']))
async def admin_edit_price(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON['edit_price_1'], reply_markup=Admin_kb.game_kb())


@router.callback_query(AdminGameFilter())
async def admin_game(callback: CallbackQuery):
    game = callback.data.split('_')[-1]
    projects_list = PROJECTS[game]

    await callback.message.edit_text(LEXICON['edit_price_2'].format(game),
                                     reply_markup=Admin_kb.projects_kb(game, projects_list))


@router.callback_query(F.data.startswith('admin_project'))
async def admin_project(callback: CallbackQuery):
    game = callback.data.split('_')[-2]
    project = callback.data.split('_')[-1]

    await callback.message.edit_text(LEXICON['edit_price_3'].format(game, project),
                                     reply_markup=Admin_kb.items_kb(game, project))


@router.callback_query(F.data.startswith('change'))
async def admin_change(callback: CallbackQuery, state: FSMContext):
    _, game, project, item = callback.data.split('_')
    item_text = 'миллион вирты' if item == 'virt' else 'бизнес' if item == 'business' else 'аккаунт'

    text = LEXICON['edit_price_4'].format(game, project, item_text)
    old_prices = get_old_prices(item, project)
    if old_prices:
        text += LEXICON['edit_price_old'].format(old_prices[0], old_prices[1])
    text += LEXICON['edit_price_buy']

    await callback.message.edit_text(text)
    await state.set_state(AdminStates.edit_price_buy)
    await state.update_data({'item': item, 'game': game, 'project': project})


@router.message(StateFilter(AdminStates.edit_price_buy))
async def edit_price_buy(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.answer('Неверный формат ввода. Цена должна быть целым числом. Попробуйте ещё раз')

    data = await state.get_data()
    item, game, project = data['item'], data['game'], data['project']
    item_text = 'миллион вирты' if item == 'virt' else 'бизнес' if item == 'business' else 'аккаунт'

    text = LEXICON['edit_price_4'].format(game, project, item_text)
    old_prices = get_old_prices(item, project)
    if old_prices:
        text += LEXICON['edit_price_old'].format(old_prices[0], old_prices[1])
    text += LEXICON['edit_price_sell'].format(str(amount))

    await message.answer(text)
    await state.set_state(AdminStates.edit_price_sell)
    data['new_buy'] = amount
    await state.update_data(data)


@router.message(StateFilter(AdminStates.edit_price_sell))
async def edit_price_sell(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.answer('Неверный формат ввода. Цена должна быть целым числом. Попробуйте ещё раз')

    data = await state.get_data()
    item, game, project, new_buy = data['item'], data['game'], data['project'], data['new_buy']

    old_prices = get_old_prices(item, project)
    old_prices_text = LEXICON['edit_price_old'].format(old_prices[0], old_prices[1]) if old_prices else ''
    item_text = 'миллион вирты' if item == 'virt' else 'бизнес' if item == 'business' else 'аккаунт'

    text = LEXICON['edit_price_confirm'].format(game, project, item_text, old_prices_text, new_buy, str(amount))

    await message.answer(text, reply_markup=Admin_kb.confirm_editing(item, project, new_buy, str(amount)))
    await state.clear()


@router.callback_query(F.data.startswith('c-e'))
async def insert_new_price(callback: CallbackQuery):
    if callback.data[3] == 'N':
        return callback.message.edit_text('🗑 Изменения отменены')

    _, item, project, buy, sell = callback.data.split('_')

    try:
        add_prices(item, project, buy, sell)
        await callback.message.edit_text(LEXICON['price_edited'].format(buy, sell))

    except Exception as e:
        await callback.message.edit_text(f'Что-то пошло не так: {e}')
