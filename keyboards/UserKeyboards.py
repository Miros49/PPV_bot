from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from lexicon import *


class UserKeyboards:
    def start_kb(self):
        kb = InlineKeyboardMarkup(row_width=1)

        kb.add(
            InlineKeyboardButton(text='Купить', callback_data='start_buy_button'), # /ORDERS /ORDERSBIZ /ORDERSACC
            InlineKeyboardButton(text='Продать', callback_data='start_sell_button'),
            InlineKeyboardButton(text='Создать заявку на покупку ', callback_data='start_create_order_button'),
            InlineKeyboardButton(text='Автопостер Discord', callback_data='start_autoposter_discord_button')
        )

        return kb

    def buy_kb(self):
        kb = InlineKeyboardMarkup(row_width=3)

        kb.add(
            InlineKeyboardButton(text='Вирты', callback_data='buy_virt'),
            InlineKeyboardButton(text='Бизнес', callback_data='buy_business'),
            InlineKeyboardButton(text='Аккаунт', callback_data='buy_account')
        )
        kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

        return kb

    def sell_kb(self):
        kb = InlineKeyboardMarkup(row_width=3)

        kb.add(
            InlineKeyboardButton(text='Вирты', callback_data='sell_virt'),
            InlineKeyboardButton(text='Бизнес', callback_data='sell_business'),
            InlineKeyboardButton(text='Аккаунт', callback_data='sell_account'),
            InlineKeyboardButton(text='← Назад', callback_data='back_to_start')
        )

        return kb

    def create_order_kb(self):
        kb = InlineKeyboardMarkup(row_width=3)

        kb.add(
            InlineKeyboardButton(text='Вирты', callback_data='buy_virt'),
            InlineKeyboardButton(text='Бизнес', callback_data='buy_business'),
            InlineKeyboardButton(text='Аккаунт', callback_data='buy_account'),
        )
        kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))

        return kb

    def back_to_start_kb(self):
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_start'))
        return kb

    def game_kb(self, action_type: str):
        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(
            InlineKeyboardButton(text='GTA5', callback_data='game_gta5'),
            InlineKeyboardButton(text='SAMP, CRMP, MTA', callback_data='game_other'),
            InlineKeyboardButton(text='← Назад', callback_data=f'back_to_{action_type}')
        )

        return kb

    def projects_kb(self, action_type: str):
        kb = InlineKeyboardMarkup(row_width=3)

        kb.add(
            InlineKeyboardButton(text="GTA5RP", callback_data='project_GTA5RP'),
            InlineKeyboardButton(text="Majestic", callback_data='project_Majestic'),
            InlineKeyboardButton(text="Grand RP GTA5", callback_data='aghafgsafasd'),
            InlineKeyboardButton(text="Radmir GTA5", callback_data='project_Radmir GTA5'),
            InlineKeyboardButton(text="Arizona RP GTA5", callback_data='fasfasfasfasfa'),
            InlineKeyboardButton(text="RMRP GTA5", callback_data='fasfasfasfasfasfaf'),

            InlineKeyboardButton(text='← Назад', callback_data=f'back_to_games_{action_type}')
        )

        return kb

    def orders_project_kb(self, action_type: str):
        kb = InlineKeyboardMarkup(row_width=3)

        kb.add(
            InlineKeyboardButton(text="GTA5RP", callback_data='project_GTA5RP_orders'),
            InlineKeyboardButton(text="Majestic", callback_data='project_Majestic_orders'),
            InlineKeyboardButton(text="Radmir GTA5", callback_data='project_Radmir GTA5_orders')
        )

        return kb

    def orders_servers_kb(self, servers_for_project):
        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(*[InlineKeyboardButton(text=server, callback_data=f'server_{server}') for server in servers_for_project])

        return kb

    def servers_kb(self, servers_for_project):
        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(*[InlineKeyboardButton(text=server, callback_data=f'server_{server}') for server in servers_for_project])
        kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_projects'))

        return kb

    def amount_kb(self):
        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(*[
            InlineKeyboardButton(text="1.000.000", callback_data='amount_1000000'),
            InlineKeyboardButton(text="1.500.000", callback_data='amount_1500000'),
            InlineKeyboardButton(text="2.000.000", callback_data='amount_2000000'),
            InlineKeyboardButton(text="3.000.000", callback_data='amount_3000000'),
            InlineKeyboardButton(text="5.000.000", callback_data='amount_5000000'),
            InlineKeyboardButton(text="10.000.000", callback_data='amount_10000000'),
            InlineKeyboardButton(text="Другое количество", callback_data='amount_custom')
        ])
        kb.row(InlineKeyboardButton(text='← Назад', callback_data='back_to_servers'))

        return kb
