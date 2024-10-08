from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database import get_bot_user_id, is_technical_work
from lexicon import SERVERS, buttons
from utils import utils


# def menu_kb():
#     kb = InlineKeyboardBuilder()
#
#     kb.add(
#         InlineKeyboardButton(text="📢 Репорты", callback_data='admin_reports'),
#         InlineKeyboardButton(text='🗂 Навигатор', callback_data='admin_information'),
#         InlineKeyboardButton(text='✏️ Изменить цену', callback_data='admin_edit_price')
#     ).adjust(2)
#
#     return kb.as_markup()


def menu_reply_kb():
    kb = ReplyKeyboardBuilder()

    kb.add(
        KeyboardButton(text=buttons['open_complaints']),
        KeyboardButton(text=buttons['edit_price']),
        KeyboardButton(text=buttons['users']),
        KeyboardButton(text=buttons['orders']),
        KeyboardButton(text=buttons['deals']),
        KeyboardButton(text=buttons['complaints_info']),
        KeyboardButton(text=buttons['transactions']),
        KeyboardButton(text=buttons['newsletter']),
        KeyboardButton(text=buttons['turn_on']) if is_technical_work() else KeyboardButton(text=buttons['turn_off'])
    ).adjust(2, 1, 2, 2, 1)

    return kb.as_markup(resize_keyboard=True)


# def information_kb():
#     kb = InlineKeyboardBuilder()
#
#     kb.add(
#         InlineKeyboardButton(text='👤 Пользователи', callback_data='admin_information_user'),
#         InlineKeyboardButton(text='📋 Заказы', callback_data='admin_information_order'),
#         InlineKeyboardButton(text='🔀 Сделки', callback_data='admin_information_deal'),
#         InlineKeyboardButton(text='💢 Жалобы', callback_data='admin_information_report'),
#     ).adjust(1, 2)
#     # kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_admin_menu'))
#
#     return kb.as_markup()


def cancel_search_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='Отменить поиск', callback_data=f'admin_cancel_search'))

    return kb.as_markup()


def game_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='GTA5', callback_data=f'admin_game_gta5'),
        InlineKeyboardButton(text='SAMP, CRMP, MTA', callback_data=f'admin_game_other')
    )
    # kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_admin_menu'))

    return kb.as_markup()


def projects_kb(game: str, projects_list: list):
    kb = InlineKeyboardBuilder()

    kb.add(*[InlineKeyboardButton(text=project, callback_data=f'admin_project_{game}_{project}') for project in
             projects_list])
    kb.adjust(3)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_games'))

    return kb.as_markup()


def servers_kb(project: str):
    kb = InlineKeyboardBuilder()

    kb.add(*[
        InlineKeyboardButton(
            text=server,
            callback_data=f'change_{project}_{server}') for server in SERVERS[project]
    ]).adjust(3)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'admin_game_{utils.determine_game(project)}'))

    return kb.as_markup()


def confirm_editing(project: str, server: str, buy: str, sell: str):
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='✅ Подтвердить?', callback_data=f'c-eY_{project}_{server}_{buy}_{sell}'),
        InlineKeyboardButton(text='❌ Отменить', callback_data='c-eN')
    )

    return kb.as_markup()


def answer_to_complaint_kb(complaint_id: int, show_interfere_button: bool = False):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Ответить', callback_data=f'answer_to_complaint_{str(complaint_id)}'),
        InlineKeyboardButton(text='Отклонить', callback_data=f'reject_complaint_{str(complaint_id)}')
    )
    kb.row(InlineKeyboardButton(text='Вмешаться в чат', callback_data='interfere_in_chat')) if show_interfere_button \
        else None

    return kb.as_markup()


def interfere_in_chat_like_kb(deal_id: int | str, show_interfere_button: bool):
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(
        text='Вмешаться в чат', callback_data=f'interfere_in_chat_confirm_{str(deal_id)}')
    ) if show_interfere_button else None
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_information_about_deal_{str(deal_id)}'))

    return kb.as_markup()


def cancel_kb():
    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(text='Отменить', callback_data='cancel_button'))

    return kb.as_markup()


def confirm_answer_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_answer'),
        InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_button')
    )

    return kb.as_markup()


def confirm_ban_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_ban'),
        InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_button')
    )

    return kb.as_markup()


def inspect_user_kb(user_id: int | str, is_not_banned: bool, previous_steps: list):
    # back_button_callback = f'back_to_information_about_{previous_steps[-1]}' if previous_steps \
    #     else 'admin_information_user'

    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='Операции', callback_data=f'show_user_operations_{str(user_id)}'),
        InlineKeyboardButton(text='Ордера', callback_data=f'show_user_orders_{str(user_id)}'),
        InlineKeyboardButton(text='Уменьшить баланс', callback_data=f'reduce_user_balance_{str(user_id)}'),
        InlineKeyboardButton(text='Пополнить баланс', callback_data=f'top_up_user_balance_{str(user_id)}')
    ).adjust(2)
    kb.row(InlineKeyboardButton(text='Разбанить', callback_data=f'admin_unban_user_{str(user_id)}')) if is_not_banned \
        else kb.row(
        InlineKeyboardButton(text='🚫 Забанить пользователя', callback_data=f'admin_ban_user_{str(user_id)}'))
    # kb.row(InlineKeyboardButton(text='← Назад', callback_data=back_button_callback))

    return previous_steps, kb.as_markup()


def inspect_order_kb(order_id: int | str, user_id: int | str, previous_steps: list):
    # back_button_callback = f'back_to_information_about_{previous_steps[-1]}' if previous_steps \
    #     else 'admin_information_order'

    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Пользователь', callback_data=f'send_information_about_user_{str(user_id)}')
    )
    # kb.row(InlineKeyboardButton(text='← Назад', callback_data=back_button_callback))

    return previous_steps, kb.as_markup()


def inspect_deal_kb(deal_id: Any, buyer_id: Any, seller_id: Any, buyer_order_id: Any, seller_order_id: Any,
                    is_active: bool, previous_steps: list):
    # back_button_callback = f'back_to_information_about_{previous_steps[-1]}' if previous_steps \
    #     else 'admin_information_deal'

    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Завершить сделку', callback_data=f'admin_cancel_deal_{str(deal_id)}'),
        InlineKeyboardButton(text='Подтвердить сделку', callback_data=f'admin_confirm_deal_{str(deal_id)}')
    ) if is_active else None
    kb.row(
        InlineKeyboardButton(text='Продавец',
                             callback_data=f'send_information_about_user_{str(get_bot_user_id(seller_id))}'),
        InlineKeyboardButton(text='Покупатель',
                             callback_data=f'send_information_about_user_{str(get_bot_user_id(buyer_id))}'),
    )
    kb.row(
        InlineKeyboardButton(text='Заказ продавца',
                             callback_data=f'send_information_about_order_{str(seller_order_id)}'),
        InlineKeyboardButton(text='Заказ покупателя',
                             callback_data=f'send_information_about_order_{str(buyer_order_id)}'))
    kb.row(InlineKeyboardButton(text='Посмотреть чат', callback_data=f'show_chat_{str(deal_id)}'))
    # kb.row(InlineKeyboardButton(text='← Назад', callback_data=back_button_callback))

    return previous_steps, kb.as_markup()


def inspect_complaint_kb(deal_id: int | str, complainer_id: int | str, offender_id: int | str,
                         previous_steps: list = None, complaint_id: int | str = None):
    # back_button_callback = f'back_to_information_about_{previous_steps[-1]}' if previous_steps \
    #     else 'admin_information_deal'

    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Сделка', callback_data=f'send_information_about_deal_{str(deal_id)}'),
        InlineKeyboardButton(text='Истец',
                             callback_data=f'send_information_about_user_{str(get_bot_user_id(complainer_id))}'),
        InlineKeyboardButton(text='Ответчик', callback_data=f'send_information_about_user_{str(offender_id)}'),
    )
    kb.row(
        InlineKeyboardButton(text='Ответить', callback_data=f'answer_to_complaint_{str(complaint_id)}'),
        InlineKeyboardButton(text='Отклонить', callback_data=f'reject_complaint_{str(complaint_id)}')
    ) if complaint_id else None

    # kb.row(InlineKeyboardButton(text='← Назад', callback_data=back_button_callback))

    return previous_steps, kb.as_markup()


def back_to_inspection_user(user_id: Any):
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_information_about_user_{str(user_id)}'))

    return kb.as_markup()


def confirmation_of_editing_user_balance(user_id: Any, action: str, amount: Any):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='✅ Да',
                             callback_data=f'confirm_balance_change_{str(user_id)}_{action}_{str(amount)}'),
        InlineKeyboardButton(text='❌ Нет, отменить', callback_data=f'back_to_information_about_user_{str(user_id)}'),
        InlineKeyboardButton(text='← Назад', callback_data='back_to_entering_balance_change_amount')
    ).adjust(2)

    return kb.as_markup()


def exit_chat():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='Покинуть чат', callback_data='exit_chat'))

    return kb.as_markup()


def confirm_newsletter():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='Подтвердить', callback_data='confirm_newsletter'),
        InlineKeyboardButton(text='Отменить', callback_data='cancel_button')
    )

    return kb.as_markup()
