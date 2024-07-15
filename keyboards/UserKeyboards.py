from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

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


def buy_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Вирты', callback_data='buy_virt'),
        InlineKeyboardButton(text='Бизнес', callback_data='buy_business'),
        InlineKeyboardButton(text='Аккаунт', callback_data='buy_account')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

    return kb.as_markup()


def sell_kb():
    kb = InlineKeyboardBuilder()  # 3

    kb.add(
        InlineKeyboardButton(text='Вирты', callback_data='sell_virt'),
        InlineKeyboardButton(text='Бизнес', callback_data='sell_business'),
        InlineKeyboardButton(text='Аккаунт', callback_data='sell_account')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

    return kb.as_markup()


def create_order_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Вирты', callback_data='buy_virt'),
        InlineKeyboardButton(text='Бизнес', callback_data='buy_business'),
        InlineKeyboardButton(text='Аккаунт', callback_data='buy_account'),
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

    return kb.as_markup()


def back_to_start_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

    return kb.as_markup()


def game_kb(action_type: str):
    kb = InlineKeyboardBuilder()  # 2

    kb.row(
        InlineKeyboardButton(text='GTA5', callback_data='game_gta5'),
        InlineKeyboardButton(text='SAMP, CRMP, MTA', callback_data='game_other')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_{action_type}'))

    return kb.as_markup()


def projects_kb(action_type: str):
    kb = InlineKeyboardBuilder()  # 3

    kb.add(
        InlineKeyboardButton(text="GTA5RP", callback_data='project_GTA5RP'),
        InlineKeyboardButton(text="Majestic", callback_data='project_Majestic'),
        InlineKeyboardButton(text="Grand RP GTA5", callback_data='aghafgsafasd'),
        InlineKeyboardButton(text="Radmir GTA5", callback_data='project_Radmir GTA5'),
        InlineKeyboardButton(text="Arizona RP GTA5", callback_data='fasfasfasfasfa'),
        InlineKeyboardButton(text="RMRP GTA5", callback_data='fasfasfasfasfasfaf'),
        InlineKeyboardButton(text='← Назад', callback_data=f'back_to_games_{action_type}')
    )
    kb.adjust(3, 3, 1)

    return kb.as_markup()


def orders_project_kb(action_type: str):  # TODO: пофиксить
    kb = InlineKeyboardBuilder()  # 3

    kb.add(
        InlineKeyboardButton(text="GTA5RP", callback_data='project_GTA5RP_orders'),
        InlineKeyboardButton(text="Majestic", callback_data='project_Majestic_orders'),
        InlineKeyboardButton(text="Radmir GTA5", callback_data='project_Radmir GTA5_orders')
    )

    return kb.as_markup()


def orders_servers_kb(servers_for_project):
    kb = InlineKeyboardBuilder()  # 2

    kb.add(*[InlineKeyboardButton(text=server, callback_data=f'server_{server}') for server in servers_for_project])
    kb.adjust(2)

    return kb.as_markup()


def servers_kb(servers_for_project):
    kb = InlineKeyboardBuilder()

    kb.add(*[InlineKeyboardButton(text=server, callback_data=f'server_{server}') for server in servers_for_project])
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_projects'))
    kb.adjust(2)

    return kb.as_markup()


def amount_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="1.000.000", callback_data='amount_1000000'),
        InlineKeyboardButton(text="1.500.000", callback_data='amount_1500000'),
        InlineKeyboardButton(text="2.000.000", callback_data='amount_2000000'),
        InlineKeyboardButton(text="3.000.000", callback_data='amount_3000000'),
        InlineKeyboardButton(text="5.000.000", callback_data='amount_5000000'),
        InlineKeyboardButton(text="10.000.000", callback_data='amount_10000000'),
        InlineKeyboardButton(text="Другое количество", callback_data='amount_custom')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_servers'))
    kb.adjust(2)

    return kb.as_markup()


def confirmation_of_creation_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Подтвердить", callback_data='confirmation_of_creation_confirm'),
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

    kb.add(InlineKeyboardButton(text='Связаться с поддержкой', callback_data='contact_support'))

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

    kb.row(InlineKeyboardButton(text="Написать тикет", callback_data="write_ticket"),
           InlineKeyboardButton(text="Мои тикеты", callback_data="my_tickets"))

    return kb.as_markup()


def send_report_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Отправить тикет", callback_data="send_ticket"),
        InlineKeyboardButton(text="Отменить тикет", callback_data="cancel_ticket")
    )

    return kb.as_markup()
