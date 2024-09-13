import math
import re
import sqlite3

from datetime import datetime
from typing import Any

from aiogram.types import InlineKeyboardMarkup

from database import get_order, get_price_db, get_deal, update_deal_status, update_order_status
from keyboards import UserKeyboards as User_kb
from lexicon import *


def determine_game(project: str):
    if project in PROJECTS['gta5']:
        return 'gta5'
    elif project in PROJECTS['other']:
        return 'other'
    else:
        return None


def parse_message_order(message: str):
    type_pattern = re.compile(r'Тип: (.+)')
    category_pattern = re.compile(r'Категория: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    amount_pattern = re.compile(r'Кол-во валюты: ([\d,]+)')
    business_name_pattern = re.compile(r'Наименование: (.+)')
    description_pattern = re.compile(r'Описание: (.+)')
    final_price_pattern = re.compile(r'Стоимость: ([\d\s,\.]+)\s*₽')

    type_match = type_pattern.search(message)
    category_match = category_pattern.search(message)
    server_match = server_pattern.search(message)
    amount_match = amount_pattern.search(message)
    business_name_match = business_name_pattern.search(message)
    description_match = description_pattern.search(message)
    final_price_match = final_price_pattern.search(message)

    if type_match and category_match and server_match and final_price_match:
        action_type = type_match.group(1).strip()
        category = category_match.group(1).strip()
        server_full = server_match.group(1).strip().split(',')
        project = server_full[0].strip()
        server = server_full[1].strip()
        final_price = final_price_match.group(1).strip().replace(',', '').replace(' ', '').replace('.', '')

        result = {
            'type': action_type,
            'category': category,
            'project': project,
            'server': server,
            'price': int(final_price)
        }

        if category == 'Вирты' and amount_match:
            amount = amount_match.group(1).strip().replace(',', '')
            result['amount'] = int(amount)
        elif category == 'Бизнес' and business_name_match:
            business_name = business_name_match.group(1).strip()
            result['business_name'] = business_name
        elif category == 'Аккаунт' and description_match:
            description = description_match.group(1).strip()
            result['description'] = description
        else:
            return None

        return result
    else:
        return None


def parse_complaint(complaint_text: str):
    deal_id_pattern = re.compile(r'├ ID сделки: (\d+)')
    description_pattern = re.compile(r'└ Описание: (.+)')

    deal_id_match = deal_id_pattern.search(complaint_text)
    description_match = description_pattern.search(complaint_text)

    if deal_id_match and description_match:
        deal_id = deal_id_match.group(1).strip()
        description = description_match.group(1).strip()

        result = {
            'deal_id': deal_id,
            'description': description
        }

        return result
    else:
        return None


def calculate_virt_price(amount: str | int, price_per_million: int) -> int:
    return math.ceil(
        (int(amount) // 1000000) * price_per_million + (int(amount) % 1000000) * (price_per_million / 1000000))


def get_item_text(item: str) -> str:
    return 'Вирты' if item == 'virt' else 'Бизнес' if item == 'business' else 'Аккаунт'


def get_game_text(game: str) -> str:
    return 'GTA 5' if game == 'gta5' else 'SAMP, CRMP'


def get_price(order_id: int | str, action_type: str) -> int:
    order = get_order(int(order_id))
    item, amount, price_ = order[4], order[7], order[9]

    if item != 'virt':
        return price_ if action_type == 'sell' else round(price_ * 1.3)

    if action_type == 'sell':
        return calculate_virt_price(amount, get_price_db(order[5], order[6], action_type))
    return int(order[8])


def get_income_amount(order_id: int | str) -> int | float:
    return get_price(order_id, 'buy') - get_price(order_id, 'sell')


def get_order_seved_text(data: dict) -> str:
    action_text, item, project, server, price_, additional = data.values()
    emoji = '📘' if action_text == 'Продажа' else '📗'

    item_text = item_lexicon.get(item)
    additional = '{:,}'.format(additional) if item == 'Вирты' else additional

    return orders_lexicon['saved'] + orders_lexicon['show_order'].format(
        emoji, action_text, item, project, server, item_text, additional, '{:,}'.format(price_).replace(',', ' '), ''
    )


def get_deal_kb(deal_id: str, tg_id: str | int, show_complaint: bool = True,
                show_cancel: bool = True) -> InlineKeyboardMarkup:
    deal = get_deal(deal_id)

    print(show_complaint)

    if tg_id == deal[1]:
        return User_kb.confirmation_of_deal_buyer_kb(deal[3], deal_id, show_report=show_complaint,
                                                     show_cancel=show_cancel)
    return User_kb.confirmation_of_deal_seller_kb(deal[1], deal_id, show_report=show_complaint)


def parse_time_to_hours(time_str: str) -> int:
    total_hours = 0

    time_parts = re.findall(r'(\d+)([dh])', time_str)

    for value, unit in time_parts:
        value = int(value)
        if unit == 'd':
            total_hours += value * 24
        elif unit == 'h':
            total_hours += value

    return total_hours


def deal_completion(deal_id: Any, seller_order_id: Any, buyer_order_id: Any, deal_status: str, order_status: str):
    try:
        update_deal_status(deal_id, deal_status)
        update_order_status(seller_order_id, order_status)
        if buyer_order_id != 0:
            update_order_status(buyer_order_id, order_status)
    except sqlite3.Error as e:
        print(f"Error updating order status to 'confirmed': {e}")


def extract_text_from_message(message_text: str):
    extracted_text = message_text.split('Подтвердите рассылку:')[1]
    return extracted_text.strip()
