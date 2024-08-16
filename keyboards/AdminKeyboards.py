from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon import SERVERS
from utils import utils


def menu_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="📢 Репорты", callback_data='admin_reports'),
        InlineKeyboardButton(text='🗂 Информация', callback_data='admin_information'),
        InlineKeyboardButton(text='✏️ Изменить цену', callback_data='admin_edit_price'),
        InlineKeyboardButton(text='🚫 Забанить пользователя', callback_data='admin_ban_user')
    )
    kb.adjust(2, 1, 1)

    return kb.as_markup()


def information_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='👤 Пользователи', callback_data='admin_information_user'),
        InlineKeyboardButton(text='📋 Заказы', callback_data='admin_information_order'),
        InlineKeyboardButton(text='🔀 Сделки', callback_data='admin_information_matched-order'),
        InlineKeyboardButton(text='💢 Жалобы', callback_data='admin_information_report'),
        InlineKeyboardButton(text='💸 Транзакции', callback_data='admin_information_transactions'),
    ).adjust(2)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_admin_menu'))

    return kb.as_markup()


def back_to_information_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'admin_information'))

    return kb.as_markup()


def game_kb():
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text='GTA5', callback_data=f'admin_game_gta5'),
        InlineKeyboardButton(text='SAMP, CRMP, MTA', callback_data=f'admin_game_other')
    )
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_admin_menu'))

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

    kb.add(InlineKeyboardButton(text='Ответить', callback_data=f'answer_to_complaint_{str(complaint_id)}'))
    kb.add(InlineKeyboardButton(text='Вмешаться в чат', callback_data='interfere_in_chat')) if show_interfere_button \
        else None

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
