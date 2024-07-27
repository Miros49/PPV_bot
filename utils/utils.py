import math
import re

from datetime import datetime

from database import get_order
from lexicon import *


def determine_game(project: str):
    if project in PROJECTS['gta5']:
        return 'gta5'
    elif project in PROJECTS['other']:
        return 'other'
    else:
        return None


def parse_message_virt(message: str):
    action_type_pattern = re.compile(r'Операция: (.+)')
    project_pattern = re.compile(r'Проект: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    amount_pattern = re.compile(r'Количество виртов: ([\d,]+)')
    price_pattern = re.compile(r'Итоговая цена: (\d+)\s*руб\.')

    action_type_match = action_type_pattern.search(message)
    project_match = project_pattern.search(message)
    server_match = server_pattern.search(message)
    amount_match = amount_pattern.search(message)
    price_match = price_pattern.search(message)

    if action_type_match and project_match and server_match and amount_match:
        action_type = action_type_match.group(1).strip()
        project = project_match.group(1).strip()
        server = server_match.group(1).strip()
        amount = amount_match.group(1).strip().replace(',', '')
        price_ = price_match.group(1).strip()

        return {
            'action_type': action_type,
            'project': project,
            'server': server,
            'amount': int(amount),
            'price': int(price_)
        }
    else:
        return None


def parse_message_business(message):
    project_pattern = re.compile(r'Проект: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    business_name_pattern = re.compile(r'Название бизнеса: (.+)')
    final_price_pattern = re.compile(r'Итоговая цена: (\d+) руб\.')

    project_match = project_pattern.search(message)
    server_match = server_pattern.search(message)
    business_name_match = business_name_pattern.search(message)
    final_price_match = final_price_pattern.search(message)

    if project_match and server_match and business_name_match and final_price_match:
        project = project_match.group(1).strip()
        server = server_match.group(1).strip()
        business_name = business_name_match.group(1).strip()
        final_price = final_price_match.group(1).strip()

        return {
            'project': project,
            'server': server,
            'business_name': business_name,
            'final_price': final_price
        }
    else:
        return None


def parse_message_account(message):
    project_pattern = re.compile(r'Проект: (.+)')
    server_pattern = re.compile(r'Сервер: (.+)')
    description_pattern = re.compile(r'Описание аккаунта: (.+)')
    final_price_pattern = re.compile(r'Итоговая цена: (\d+) руб\.')

    project_match = project_pattern.search(message)
    server_match = server_pattern.search(message)
    description_match = description_pattern.search(message)
    final_price_match = final_price_pattern.search(message)

    if project_match and server_match and description_match and final_price_match:
        project = project_match.group(1).strip()
        server = server_match.group(1).strip()
        description = description_match.group(1).strip()
        final_price = final_price_match.group(1).strip()

        return {
            'project': project,
            'server': server,
            'description': description,
            'price': final_price
        }
    else:
        return None


def get_item_text_projects(item: str) -> str:
    if item == 'virt':
        return 'виртуальную валюту'
    elif item == 'business':
        return 'бизнес'
    return 'аккаунт'


def get_item_text_servers(item: str) -> str:
    if item == 'virt':
        return 'виртуальной валюты'
    elif item == 'business':
        return 'бизнеса'
    return 'аккаунта'


def extract_price(message):
    pattern = r'Цена:\s+(\d+\.\d+)\s+руб'

    match = re.search(pattern, message)

    if match:
        return int(float(match.group(1)))

    return None


# def get_price(order_id: str | int, user: str):
#     order = get_order(order_id)
#     amount = order[7]
#
#     if order[4] == 'virt':
#         try:
#             price_per_million = PRICE_PER_MILLION_VIRTS[order[5]][user[:-2]]
#         except KeyError:
#             price_per_million = 100
#         return math.ceil((amount // 1000000) * price_per_million + (amount % 1000000) * (price_per_million / 1000000))
#
#     return amount if user == 'seller' else amount * 1.3


def calculate_price(amount: str | int, price_per_million: int):
    return math.ceil(
        (int(amount) // 1000000) * price_per_million + (int(amount) % 1000000) * (price_per_million / 1000000))
