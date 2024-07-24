from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon import *


def start_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='Купить', callback_data='start_buy_button'),  # /ORDERS /ORDERSBIZ /ORDERSACC
        InlineKeyboardButton(text='Продать', callback_data='start_sell_button'),
        InlineKeyboardButton(text='Создать заявку на покупку ', callback_data='start_create_order_button'),
        InlineKeyboardButton(text='Автопостер Discord', callback_data='start_autoposter_discord_button')
    )

    kb.adjust(1)

    return kb.as_markup()


def create_ordeer_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='Создать заявку на покупку ', callback_data='start_create_order_button'),
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_show')
    ).adjust(1)

    return kb.as_markup()


def action_kb(action_type: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Вирты', callback_data=f'virt_{action_type}'),
        InlineKeyboardButton(text='Бизнес', callback_data=f'business_{action_type}'),
        InlineKeyboardButton(text='Аккаунт', callback_data=f'account_{action_type}')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

    return kb.as_markup()


def back_to_start_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

    return kb.as_markup()


def game_kb(item: str, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='GTA5', callback_data=f'game_gta5_{item}_{action_type}'),
        InlineKeyboardButton(text='SAMP, CRMP, MTA', callback_data=f'game_other_{item}_{action_type}')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_{action_type}'))

    return kb.as_markup()


def projects_kb(item: str, projects_list: list, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.add(*[InlineKeyboardButton(text=project, callback_data=f'project_{item}_{project}_{action_type}') for project in
             projects_list])
    kb.adjust(3)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_games_{item}_{action_type}'))

    return kb.as_markup()


def servers_kb(item: str, game, project: str, servers_for_project: list, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.add(*[
        InlineKeyboardButton(
            text=server,
            callback_data=f'server_{item}_{project}_{server}_{action_type}') for server in servers_for_project
    ])
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_projects_{item}_{game}_{action_type}'))

    return kb.as_markup()


def amount_kb(project: str, server: str, action_type: str):
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="1.000.000", callback_data=f'amount_1000000_{project}_{server}_{action_type}'),
        InlineKeyboardButton(text="1.500.000", callback_data=f'amount_1500000_{project}_{server}_{action_type}'),
        InlineKeyboardButton(text="2.000.000", callback_data=f'amount_2000000_{project}_{server}_{action_type}'),
        InlineKeyboardButton(text="3.000.000", callback_data=f'amount_3000000_{project}_{server}_{action_type}'),
        InlineKeyboardButton(text="5.000.000", callback_data=f'amount_5000000_{project}_{server}_{action_type}'),
        InlineKeyboardButton(text="10.000.000", callback_data=f'amount_10000000_{project}_{server}_{action_type}'),
        InlineKeyboardButton(text="Другое количество", callback_data=f'amount_custom_{project}_{server}_{action_type}')
    )
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_servers_{project}_{action_type}'))

    return kb.as_markup()


def confirmation_of_creation_kb(item: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text='Подтвердить',
            callback_data=f'confirmation_of_creation_{item}_confirm'),
        InlineKeyboardButton(text="Отменить", callback_data='confirmation_of_creation_cancel')
    )

    return kb.as_markup()


def confirmation_of_deal_buyer_kb(seller_id: str | int, matched_orders_id: str | int):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="📢 Сообщить о нарушении",
                             callback_data=f'report_{str(seller_id)}_{str(matched_orders_id)}'))
    kb.row(
        InlineKeyboardButton(text="✅ Подтвердить сделку", callback_data='confirmation_of_deal_confirm'),
        InlineKeyboardButton(text="❌ Отменить сделку", callback_data='confirmation_of_deal_cancel')
    )

    return kb.as_markup()


def confirmation_of_deal_seller_kb(buyer_id: str | int, matched_orders_id: str | int):
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="📢 Сообщить о нарушении",
                             callback_data=f'report_{str(buyer_id)}_{str(matched_orders_id)}'),
        InlineKeyboardButton(text="Отменить сделку", callback_data='confirmation_of_deal_cancel')
    )
    kb.adjust(1)

    return kb.as_markup()


def support_kb():
    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(text='Связаться с поддержкой', url='https://t.me/hatepizza'))

    return kb.as_markup()


def account_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up_balance"),
        InlineKeyboardButton(text="Мои ордера", callback_data="my_orders")
    )

    return kb.as_markup()


def report_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text="Написать жалобу", callback_data="write_ticket"),
           InlineKeyboardButton(text="Мои жалобы", callback_data="my_tickets"))

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
