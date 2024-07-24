from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def menu_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="📢 Репорты", callback_data='admin_reports'),
        InlineKeyboardButton(text='🗂 Информация', callback_data='admin_information')
    )
    kb.adjust(2)

    return kb.as_markup()


def information_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text='👤 Пользователь', callback_data='admin_information_user'),
        InlineKeyboardButton(text='📋 Заказ', callback_data='admin_information_order'),
        InlineKeyboardButton(text='🔀 Скрещённый заказ', callback_data='admin_information_matched-order'),
        InlineKeyboardButton(text='💢 Жалоба', callback_data='admin_information_report'),
        InlineKeyboardButton(text='💸 Транзакция', callback_data='admin_information_transactions'),
    ).adjust(2)
    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'back_to_menu'))

    return kb.as_markup()


def back_to_information_kb():
    kb = InlineKeyboardBuilder()

    kb.row(InlineKeyboardButton(text='← Назад', callback_data=f'admin_information'))

    return kb.as_markup()
