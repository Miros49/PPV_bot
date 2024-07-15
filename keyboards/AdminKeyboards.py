from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="📢 Репорты", callback_data='admin_reports'),
        InlineKeyboardButton(text='💸 Операции', callback_data='admin_transactions'),  # TODO: доделать кнопку
        InlineKeyboardButton(text='👨‍💻 Поддержка', callback_data='admin_support'),  # TODO: доделать кнопку
        InlineKeyboardButton(text='ℹ️ Информация', callback_data='admin_information')  # TODO: доделать кнопку
    )

    return kb
