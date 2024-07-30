import math
import re

from datetime import datetime

from database import get_order, get_price_db
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
    final_price_pattern = re.compile(r'Стоимость: ([\d,]+)\s*руб')

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
        final_price = final_price_match.group(1).strip().replace(',', '')

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


def calculate_virt_price(amount: str | int, price_per_million: int) -> int:
    return math.ceil(
        (int(amount) // 1000000) * price_per_million + (int(amount) % 1000000) * (price_per_million / 1000000))


def get_item_text(item: str) -> str:
    return 'Вирты' if item == 'virt' else 'Бизнес' if item == 'business' else 'Аккаунт'


def get_game_text(game: str) -> str:
    return 'GTA 5' if game == 'gta5' else 'SAMP, MOBILE, CRMP'


def get_price(order_id: int | str, action_type: str) -> int:
    order = get_order(int(order_id))
    item, amount, price_ = order[4], order[7], order[9]

    if item != 'virt':
        return price_ if action_type == 'sell' else round(price_ * 1.3)

    if action_type == 'sell':
        return calculate_virt_price(amount, get_price_db(order[5], order[6], action_type))
    return int(order[8])


def get_order_seved_text(data: dict) -> str:
    action_text, item, project, server, price_, additional = data.values()
    emoji = '📘' if action_text == 'Продажа' else '📗'

    item_text = item_lexicon.get(item)

    return orders_lexicon['saved'] + orders_lexicon['show_order'].format(
        emoji, action_text, item, project, server, item_text, additional, '{:,}'.format(price_), ''
    )
