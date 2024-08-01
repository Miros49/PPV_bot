from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import utils
from lexicon import *


def start_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='🛒 Магазин', callback_data='shop_button'),
        InlineKeyboardButton(text='👤 Аккаунт', callback_data='account_button'),
        InlineKeyboardButton(text='📢 Жалобы', callback_data='complaints_button'),
        InlineKeyboardButton(text='📕 Правила', url='https://telegra.ph/Pravila-Bota-DD-07-28'),
        InlineKeyboardButton(text='🛡 Поддержка', callback_data='support_button'),
    ).adjust(1, 2, 2)

    return kb.as_markup()


def shop_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='Купить', callback_data='shop_buy_button'),  # /ORDERS /ORDERSBIZ /ORDERSACC
        InlineKeyboardButton(text='Продать', callback_data='shop_sell_button'),
        InlineKeyboardButton(text='Создать заказ на покупку ', callback_data='shop_create_order_button'),
        # InlineKeyboardButton(text='Автопостер Discord', callback_data='shop_autoposter_discord_button'),
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_menu')
    )

    kb.adjust(1)

    return kb.as_markup()


def create_ordeer_kb(key: bool, project: str, server: str):
    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(text='Создать заказ на покупку ',
                                callback_data=f'co_server_{project}_{server}')) if key else None
    kb.add(InlineKeyboardButton(text='🛒 Магазин', callback_data=f'shop_button')).adjust(1)

    return kb.as_markup()


def action_kb(action_type: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Вирты', callback_data=f'virt_{action_type}'),
        InlineKeyboardButton(text='Бизнес', callback_data=f'business_{action_type}'),
        InlineKeyboardButton(text='Аккаунт', callback_data=f'account_{action_type}')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_shop'))

    return kb.as_markup()


def back_to_menu_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_menu'))

    return kb.as_markup()


def game_kb(item: str, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='GTA5', callback_data=f'game_gta5_{item}_{action_type}'),
        InlineKeyboardButton(text='SAMP, CRMP', callback_data=f'game_other_{item}_{action_type}')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_{action_type}'))

    return kb.as_markup()


def projects_kb(item: str, game: str, action_type: str):
    projects_list = PROJECTS[game]
    sizes = [2, 3] if game == 'gta5' else [3]
    kb = InlineKeyboardBuilder()

    kb.add(*[InlineKeyboardButton(text=project, callback_data=f'project_{item}_{project}_{action_type}') for project in
             projects_list]).adjust(*sizes)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_games_{item}_{action_type}'))

    return kb.as_markup()


def servers_kb(item: str, game: str, project: str, action_type: str):
    servers_for_project = SERVERS[project]
    kb = InlineKeyboardBuilder()

    kb.add(*[
        InlineKeyboardButton(
            text=server,
            callback_data=f'server_{item}_{project}_{server}_{action_type}') for server in servers_for_project
    ]).adjust(3)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_projects_{item}_{game}_{action_type}'))

    return kb.as_markup()


def amount_kb(project: str, server: str, action_type: str, item='virt'):
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="1.000.000", callback_data=f'amount_1000000_{project}_{server}'),
        InlineKeyboardButton(text="1.500.000", callback_data=f'amount_1500000_{project}_{server}'),
        InlineKeyboardButton(text="2.000.000", callback_data=f'amount_2000000_{project}_{server}'),
        InlineKeyboardButton(text="3.000.000", callback_data=f'amount_3000000_{project}_{server}'),
        InlineKeyboardButton(text="5.000.000", callback_data=f'amount_5000000_{project}_{server}'),
        InlineKeyboardButton(text="10.000.000", callback_data=f'amount_10000000_{project}_{server}'),
        InlineKeyboardButton(text="Другое количество", callback_data=f'amount_custom_{project}_{server}')
    )
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_servers_{item}_{project}_{action_type}'))

    return kb.as_markup()


def confirmation_of_creation_kb(item: str, project: str, server: str, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Подтвердить', callback_data=f'confirmation_of_creation_{item}_confirm'),
        InlineKeyboardButton(text="Отменить", callback_data='confirmation_of_creation_cancel'),
        InlineKeyboardButton(text='← Назад',
                             callback_data=f'{"server" if item == "virt" else "btls"}_{item}_{project}_'
                                           f'{server}_{action_type}')
    ).adjust(2)

    return kb.as_markup()


def confirmation_of_deal_buyer_kb(seller_id: str | int, matched_orders_id: str | int):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="📢 Сообщить о нарушении",
                             callback_data=f'report_{str(seller_id)}_{str(matched_orders_id)}'))
    kb.row(
        InlineKeyboardButton(text="✅ Подтвердить сделку",
                             callback_data=f'confirmation_of_deal_confirm_{str(matched_orders_id)}'),
        InlineKeyboardButton(text="❌ Отменить сделку",
                             callback_data=f'confirmation_of_deal_cancel_{str(matched_orders_id)}')
    )

    return kb.as_markup()


def confirmation_of_deal_seller_kb(buyer_id: str | int, matched_orders_id: str | int):
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="📢 Сообщить о нарушении",
                             callback_data=f'report_{str(buyer_id)}_{str(matched_orders_id)}'),
        InlineKeyboardButton(text="❌ Отменить сделку",
                             callback_data=f'confirmation_of_deal_cancel_{str(matched_orders_id)}')
    )
    kb.adjust(1)

    return kb.as_markup()


def support_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='Связаться с поддержкой', url='https://t.me/hatepizza'),
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_menu')
    ).adjust(1)

    return kb.as_markup()


def account_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="💳 Пополнить", callback_data="top_up_balance"),
        InlineKeyboardButton(text='💸 Вывести', callback_data='cashout_request'),
        InlineKeyboardButton(text="🗂 Мои ордера", callback_data="my_orders"),
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_menu')
    ).adjust(2, 1)

    return kb.as_markup()


def top_up_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance")
    )

    return kb.as_markup()


def confirm_cashout_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='Вывести деньги', callback_data='cashout_confirm'),
        InlineKeyboardButton(text='Отменить', callback_data='cashout_cancel')
    )

    return kb.as_markup()


def report_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="📝 Пожаловаться", callback_data="write_complaint"),
        InlineKeyboardButton(text="📂 Мои жалобы", callback_data="my_complaints"),
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_menu')
    ).adjust(2)

    return kb.as_markup()


def send_report_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Оставить жалобу", callback_data="send_ticket"),
        InlineKeyboardButton(text="Отменить", callback_data="cancel_ticket")
    )

    return kb.as_markup()


def cancel_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_button'))

    return kb.as_markup()


def cancel_complaint_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_complaint_button'))

    return kb.as_markup()


def show_kb(order_id: int | str, item: str, project: str, server: str, key: bool = False):
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="✅ Купить!", callback_data=f'buy_order_{str(order_id)}'))
    kb.row(InlineKeyboardButton(text='⏬ Посмотреть ещё',
                                callback_data=f'watch-other_{item}_{project}_{server}_{order_id}')) if key else None

    return kb.as_markup()


def buy_order_kb(order_id: str):
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(
        text="🤝 Да, начать чат с продавцом",
        callback_data=f'confirmation_of_buying_{order_id}')
    )

    return kb.as_markup()


def co_game_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='GTA5', callback_data=f'co_game_gta5'),
        InlineKeyboardButton(text='SAMP, CRMP', callback_data=f'co_game_other')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_shop'))

    return kb.as_markup()


def co_project_kb(game: str):
    sizes = [1, 3] if game == 'gta5' else [3]
    kb = InlineKeyboardBuilder()

    kb.add(*[InlineKeyboardButton(text=project, callback_data=f'co_project_{project}') for project in
             PROJECTS[game]]).adjust(*sizes)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'shop_create_order_button'))

    return kb.as_markup()


def co_server_kb(project: str):
    kb = InlineKeyboardBuilder()

    kb.add(*[
        InlineKeyboardButton(
            text=server,
            callback_data=f'co_server_{project}_{server}') for server in SERVERS[project]
    ]).adjust(3)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'co_game_{utils.determine_game(project)}'))

    return kb.as_markup()


def co_amount_kb(project: str, server: str):
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="1.000.000", callback_data=f'co_amount_{project}_{server}_1000000'),
        InlineKeyboardButton(text="1.500.000", callback_data=f'co_amount_{project}_{server}_1500000'),
        InlineKeyboardButton(text="2.000.000", callback_data=f'co_amount_{project}_{server}_2000000'),
        InlineKeyboardButton(text="3.000.000", callback_data=f'co_amount_{project}_{server}_3000000'),
        InlineKeyboardButton(text="5.000.000", callback_data=f'co_amount_{project}_{server}_5000000'),
        InlineKeyboardButton(text="10.000.000", callback_data=f'co_amount_{project}_{server}_10000000'),
        InlineKeyboardButton(text="Другое количество", callback_data=f'co_amount_{project}_{server}_custom')
    ).adjust(2)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'co_project_{project}'))

    return kb.as_markup()


def cancel_order_kb(order_id: int | str):
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='Отменить заказ', callback_data=f'cancel_order_{str(order_id)}'))

    return kb.as_markup()


def hide_order_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='Скрыть', callback_data=f'hide_button'))


def back_to_complaint_kb():
    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(text='← Назад', callback_data='complaints_button'))

    return kb.as_markup()


def back_to_complaint_order_id():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_complaint_order_id'))

    return kb.as_markup()


def back_to_complaint_description():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_complaint_description'))

    return kb.as_markup()


def to_main_menu(from_orders: bool = False):
    key = "True" if from_orders else "False"
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='Вернуться в меню',
                                callback_data=f'send_main_menu_{key}'))

    return kb.as_markup()


def order_back_to_servers(item: str, project: str, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_servers_{item}_{project}_{action_type}'))

    return kb.as_markup()


def back_to_filling():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_filling'))

    return kb.as_markup()


def complaint_management():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='', callback_data=''))

    pass
