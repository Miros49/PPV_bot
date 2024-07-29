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


def parse_message_virt(message: str):
    type_pattern = re.compile(r'Тип: (.+)')
    category_pattern = re.compile(r'Категория: (.+)')
    platform_pattern = re.compile(r'Платформа: (.+)')
    project_pattern = re.compile(r'Проект: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    amount_pattern = re.compile(r'Кол-во валюты: ([\d,]+)')
    price_pattern = re.compile(r'Стоимость: ([\d,\s]+)\s*руб')

    type_match = type_pattern.search(message)
    category_match = category_pattern.search(message)
    platform_match = platform_pattern.search(message)
    project_match = project_pattern.search(message)
    server_match = server_pattern.search(message)
    amount_match = amount_pattern.search(message)
    price_match = price_pattern.search(message)

    if type_match and category_match and platform_match and project_match and server_match and amount_match and price_match:
        action_type = type_match.group(1).strip()
        category = category_match.group(1).strip()
        platform = platform_match.group(1).strip()
        project = project_match.group(1).strip()
        server = server_match.group(1).strip()
        amount = amount_match.group(1).strip().replace(',', '')
        price_ = price_match.group(1).strip().replace(' ', '').replace(',', '')

        return {
            'type': action_type,
            'category': category,
            'platform': platform,
            'project': project,
            'server': server,
            'amount': int(amount),
            'price': int(price_)
        }
    else:
        return None


def parse_message_business(message: str):
    type_pattern = re.compile(r'Тип: (.+)')
    category_pattern = re.compile(r'Категория: (.+)')
    platform_pattern = re.compile(r'Платформа: (.+)')
    project_pattern = re.compile(r'Проект: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    business_name_pattern = re.compile(r'Наименование: (.+)')
    final_price_pattern = re.compile(r'Стоимость: (\d+)\s*руб')

    type_match = type_pattern.search(message)
    category_match = category_pattern.search(message)
    platform_match = platform_pattern.search(message)
    project_match = project_pattern.search(message)
    server_match = server_pattern.search(message)
    business_name_match = business_name_pattern.search(message)
    final_price_match = final_price_pattern.search(message)

    if type_match and category_match and platform_match and project_match and server_match and business_name_match and final_price_match:
        action_type = type_match.group(1).strip()
        category = category_match.group(1).strip()
        platform = platform_match.group(1).strip()
        project = project_match.group(1).strip()
        server = server_match.group(1).strip()
        business_name = business_name_match.group(1).strip()
        final_price = final_price_match.group(1).strip()

        return {
            'type': action_type,
            'category': category,
            'platform': platform,
            'project': project,
            'server': server,
            'business_name': business_name,
            'final_price': final_price
        }
    else:
        return None


import re


def parse_message_account(message: str):
    type_pattern = re.compile(r'Тип: (.+)')
    category_pattern = re.compile(r'Категория: (.+)')
    platform_pattern = re.compile(r'Платформа: (.+)')
    project_pattern = re.compile(r'Проект: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    description_pattern = re.compile(r'Описание: (.+)')
    final_price_pattern = re.compile(r'Стоимость: (\d+)\s*руб')

    type_match = type_pattern.search(message)
    category_match = category_pattern.search(message)
    platform_match = platform_pattern.search(message)
    project_match = project_pattern.search(message)
    server_match = server_pattern.search(message)
    description_match = description_pattern.search(message)
    final_price_match = final_price_pattern.search(message)

    if type_match and category_match and platform_match and project_match and server_match and description_match and final_price_match:
        action_type = type_match.group(1).strip()
        category = category_match.group(1).strip()
        platform = platform_match.group(1).strip()
        project = project_match.group(1).strip()
        server = server_match.group(1).strip()
        description = description_match.group(1).strip()
        final_price = final_price_match.group(1).strip()

        return {
            'type': action_type,
            'category': category,
            'platform': platform,
            'project': project,
            'server': server,
            'description': description,
            'price': final_price
        }
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
