from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def menu_kb():
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(text="📢 Репорты", callback_data='admin_reports'),
        InlineKeyboardButton(text='💸 Операции', callback_data='admin_transactions'),  # TODO: доделать кнопку
        InlineKeyboardButton(text='👨‍💻 Поддержка', callback_data='admin_support'),  # TODO: доделать кнопку
        InlineKeyboardButton(text='ℹ️ Информация', callback_data='admin_information')  # TODO: доделать кнопку
    )
    kb.adjust(2)

    return kb.as_markup()
