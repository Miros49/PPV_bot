import datetime
import math
import sqlite3

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from typing import List, Tuple, Optional, Union

from core import storage
from states import UserStates

database_file = 'database/database.db'


def init_db():
    create_tables()


def create_tables():
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        username TEXT,
                        phone_number TEXT,
                        balance REAL DEFAULT 0.00,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        username TEXT,
                        action TEXT,
                        item TEXT,
                        project TEXT,
                        server TEXT,
                        amount INTEGER,
                        description TEXT,
                        price INTEGER,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id TEXT,
                        sender_id INTEGER,
                        receiver_id INTEGER,
                        message TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS matched_orders (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                buyer_id INTEGER,
                                buyer_order_id INTEGER,
                                seller_id INTEGER,
                                seller_order_id INTEGER,
                                ststus TEXT DEFAULT 'open',
                                timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bot_user_id INTEGER UNIQUE,
                            user_id INTEGER UNIQUE,
                            order_id INTEGER DEFAULT 0,
                            deal_id INTEGER DEFAULT 0,
                            amount REAL,
                            action TEXT,
                            timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_id INTEGER,
                            complainer_id INTEGER,
                            offender_id INTEGER,
                            complaint TEXT,
                            status TEXT DEFAULT 'open',
                            answer TEXT DEFAULT NONE,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS prices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project TEXT,
                            server TEXT,
                            buy INTEGER DEFAULT 100,
                            sell INTEGER DEFAULT 100)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS bans (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER UNIQUE,
                            banned_until TEXT,
                            bans_number INTEGER)''')

    conn.commit()
    conn.close()


def get_current_time_formatted() -> str:
    tz = datetime.timezone(datetime.timedelta(hours=3))  # GMT+3
    now = datetime.datetime.now(tz)
    return now.strftime('%d.%m.%Y %H:%M')


def add_user(user_id, username, phone_number):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    current_time = get_current_time_formatted()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, phone_number, created_at) VALUES (?, ?, ?, ?)",
                   (user_id, username, phone_number, current_time))
    conn.commit()
    conn.close()


def add_order(user_id, username, action, item, project, server, amount, description, price):
    current_time = get_current_time_formatted()

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (user_id, username, action, item, project, server, amount, description, price, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, action, item, project, server, amount, description, price, current_time))

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return order_id


def save_chat_message(chat_id, sender_id, receiver_id, message):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    current_time = get_current_time_formatted()
    cursor.execute("INSERT INTO chat_logs (chat_id, sender_id, receiver_id, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (chat_id, sender_id, receiver_id, message, current_time))
    conn.commit()
    conn.close()


def create_report(order_id: int | str, complainer_id: int | str, offender_id: int | str, complaint: str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    current_time = get_current_time_formatted()
    cursor.execute("""
        INSERT INTO reports (order_id, complainer_id, offender_id, complaint, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (int(order_id), int(complainer_id), int(offender_id), complaint, current_time))
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id, username, phone_number, balance, created_at FROM users WHERE user_id=?",
                   (user_id,))

    user_data = cursor.fetchone()
    conn.close()

    return user_data


def get_bot_user_id(user_id):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE user_id=?", (user_id,))

    bot_user_id = cursor.fetchone()[0]
    conn.close()

    return bot_user_id


def get_user_id_by_id(user_id_in_database: int) -> int | None:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE id = ?", (user_id_in_database,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None


def get_user_by_id(user_id_in_database: int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id_in_database,))
    result = cursor.fetchone()
    conn.close()

    return result


def get_orders_by_user_id(user_id, status):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ? and status = ?
    """, (user_id, status))

    orders = cursor.fetchall()
    conn.close()

    return orders


def get_user_id_by_order(order_id: int | str) -> int:
    conn = sqlite3.connect(database_file)

    cursor = conn.cursor()
    cursor.execute("""SELECT user_id FROM orders WHERE id = ?""", (int(order_id),))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def get_balance(user_id: int | str):
    conn = sqlite3.connect(database_file)

    cursor = conn.cursor()
    cursor.execute("""SELECT balance FROM users WHERE user_id = ?""", (int(user_id),))

    result = cursor.fetchone()
    conn.close()

    return result[0]


def edit_balance(user_id: int, amount: float, action: str, order_id: Union[int, str] = 0, deal_id: Union[int, str] = 0,
                 buy_order_creation: bool = False):
    current_time = get_current_time_formatted()

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))

    result = cursor.fetchone()
    new_balance = result[0] + amount

    if new_balance < 0:
        print('\n\nОТРИЦАТЕЛЬНЫЙ БАЛАНС!\n')
        print(user_id, amount, action, order_id, deal_id, buy_order_creation, '\n\n')

    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))

    if not buy_order_creation:
        bot_user_id = get_bot_user_id(user_id)

        cursor.execute("""
            INSERT INTO transactions (bot_user_id, user_id, order_id, deal_id, amount, action, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (bot_user_id, user_id, int(order_id), int(deal_id), amount, action, current_time))

    conn.commit()
    conn.close()


def get_order(order_id: int | str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM orders WHERE id = ?', (int(order_id),))

    result = cursor.fetchone()
    conn.close()
    return result if result else None


def update_order_status(order_id, status):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (status, order_id))

    conn.commit()
    conn.close()


def delete_order(order_id: int | str) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM orders WHERE id = ?", (int(order_id),))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при удалении заказа: {e}", datetime.datetime.now().time(), sep='\n')
        return False
    finally:
        conn.close()


def get_item(order_id: int | str) -> str:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT item FROM orders WHERE id = ?''', (int(order_id),))

    item = cursor.fetchone()
    conn.close()
    return item


async def match_orders(user_id, action, project, server, amount):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    if project in ["HASSLE Online", "Radmir RP"]:
        projects_to_check = ["HASSLE Online", "Radmir RP"]
        query = """
            SELECT id, user_id
            FROM orders
            WHERE action = ? AND project IN (?, ?) AND server = ? AND amount = ? AND status = 'pending' AND user_id != ?
            AND user_id NOT IN ({})
            LIMIT 1
        """
        params_base = (('sell' if action == 'buy' else 'buy'), *projects_to_check, server, amount, user_id)
    else:
        query = """
            SELECT id, user_id
            FROM orders
            WHERE action = ? AND project = ? AND server = ? AND amount = ? AND status = 'pending' AND user_id != ?
            AND user_id NOT IN ({})
            LIMIT 1
        """
        params_base = (('sell' if action == 'buy' else 'buy'), project, server, amount, user_id)

    excluded_user_ids = set()

    while True:
        formatted_query = query.format(",".join("?" * len(excluded_user_ids)))
        params = params_base + tuple(excluded_user_ids)

        cursor.execute(formatted_query, params)
        match = cursor.fetchone()

        if not match:
            conn.close()
            return None

        order_id, other_user_id = match[0], match[1]

        other_user_state = FSMContext(storage, StorageKey(bot_id=7324739366, chat_id=user_id, user_id=user_id))
        if await other_user_state.get_state() not in [UserStates.in_chat, UserStates.in_chat_waiting_complaint]:
            conn.close()
            return order_id, other_user_id

        excluded_user_ids.add(other_user_id)


def get_pending_sell_orders(user_id: int, item: str, project: str, server: str) -> List[Tuple]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    if project in ["HASSLE Online", "Radmir RP"]:
        projects_to_check = ["HASSLE Online", "Radmir RP"]
        query = """
            SELECT * FROM orders
            WHERE user_id != ? AND action = 'sell' AND item = ? AND project IN (?, ?)
            AND server = ? AND status = 'pending'
            ORDER BY amount ASC
        """
        params = (user_id, item, *projects_to_check, server)
    else:
        query = """
            SELECT * FROM orders
            WHERE user_id != ? AND action = 'sell' AND item = ? AND project = ? AND server = ? AND status = 'pending'
            ORDER BY amount ASC
        """
        params = (user_id, item, project, server)

    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()

    return orders


def get_report(report_id: int | str) -> Tuple[int, int, int, int, str, str, str]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM reports WHERE id = ?''', (int(report_id),))
    report = cursor.fetchone()
    conn.close()
    return report


def get_open_complaints() -> List[Tuple[int, int, int, int, str, str]]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, order_id, complainer_id, offender_id, complaint, answer, created_at
        FROM reports
        WHERE status = 'open' 
    ''')

    open_reports = cursor.fetchall()
    conn.close()

    return open_reports


def get_complaint(complaint_id: int | str) -> Tuple[int, int, int, int, str, str]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM reports 
        WHERE id = ?
    """, (int(complaint_id),))

    complaint = cursor.fetchone()
    conn.close()

    return complaint


def set_complaint_answer(complaint_id: int | str, answer: str, status: str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reports
        SET answer = ?, status = ?
        WHERE id = ?
    """, (answer, status, int(complaint_id)))

    conn.commit()
    conn.close()


def get_complaints(user_id) -> List[Tuple]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM reports WHERE complainer_id = ? 
                      ORDER BY CASE 
                                  WHEN status = 'open' THEN 1
                                  WHEN status = 'closed' THEN 2
                                  ELSE 3
                               END''', (user_id,))

    report_info = cursor.fetchall()
    conn.close()

    return report_info


def user_has_complaint_on_order(user_id: int, order_id: int) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 
        FROM reports 
        WHERE complainer_id = ? AND order_id = ?
    """, (user_id, order_id))

    complaint_exists = cursor.fetchone() is not None
    conn.close()

    return complaint_exists


def delete_complaint(complaint_id: int | str) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM reports WHERE id = ?", (int(complaint_id),))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting complaint: {e}", datetime.datetime.now().time(), sep='\n')
        return False
    finally:
        conn.close()


# ------------------ УПРАВЛЕНИЕ СДЕЛКАМИ ------------------ #


def create_matched_order(buyer_id: int, buyer_order_id: int, seller_id: int, seller_order_id: int) -> Optional[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO matched_orders (
                buyer_id, buyer_order_id, seller_id, seller_order_id
            ) VALUES (?, ?, ?, ?)''',
            (buyer_id, buyer_order_id, seller_id, seller_order_id)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Ошибка при создании элемента: {e}", datetime.datetime.now().time(), sep='\n')
        return None


def get_deal(deal_id: int | str) -> Tuple[int, int, int, int, int, str, str]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM matched_orders WHERE id = ?''', (int(deal_id),))

    order = cursor.fetchone()
    conn.close()

    return order


def get_user_deals(user_id: int) -> List[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM matched_orders
        WHERE buyer_id = ? OR seller_id = ?
    """, (user_id, user_id))

    matched_order_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return matched_order_ids


def update_deal_status(deal_id: int | str, new_status: str) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE matched_orders 
            SET ststus = ? 
            WHERE id = ?''',
                       (new_status, int(deal_id))
                       )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении статуса: {e}", datetime.datetime.now().time(), sep='\n')
        return False


def check_matched_order(matched_order_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id 
        FROM matched_orders
        WHERE id = ? AND (buyer_id = ? OR seller_id = ?)
    """, (matched_order_id, user_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def add_prices(project: str, server: str, buy_price: str | int, sell_price: str | int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""SELECT id FROM prices WHERE project = ? AND server = ?""", (project, server))
    result = cursor.fetchone()

    if result:
        cursor.execute("""
            UPDATE prices
            SET buy = ?, sell = ?
            WHERE id = ?
        """, (int(buy_price), int(sell_price), result[0]))
    else:
        cursor.execute("""
            INSERT INTO prices (project, server, buy, sell)
            VALUES (?, ?, ?, ?)
        """, (project, server, int(buy_price), int(sell_price)))

    conn.commit()
    conn.close()


def get_old_prices(project: str, server: str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""SELECT buy, sell FROM prices WHERE project = ? AND server = ?""",
                   (project, server))

    result = cursor.fetchone()
    conn.close()

    return result


def get_price_db(project: str, server: str, action_type: str) -> int | float:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    if action_type == 'buy':
        cursor.execute('SELECT buy FROM prices WHERE project = ? AND server = ?', (project, server))
    else:
        cursor.execute('SELECT sell FROM prices WHERE project = ? AND server = ?', (project, server))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 100


def add_transaction(user_id: int, amount: float, action: str, order_id: int = 0, deal_id: int = 0):
    bot_user_id = get_bot_user_id(user_id)

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    current_time = get_current_time_formatted()

    cursor.execute("""
        INSERT INTO transactions (bot_user_id, user_id, order_id, deal_id, amount, action, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (bot_user_id, user_id, order_id, deal_id, amount, action, current_time))

    conn.commit()
    conn.close()


def get_transaction(transaction_id: int) -> Optional[Tuple]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    transaction = cursor.fetchone()
    conn.close()

    return transaction


def get_transactions(user_id: int) -> List[Tuple]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    transactions = cursor.fetchall()
    conn.close()

    return transactions


def delete_transaction(user_id: Union[int, str], order_id: Union[int, str] = 0, deal_id: Union[int, str] = 0) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        if order_id:
            cursor.execute("DELETE FROM transactions WHERE user_id = ? AND order_id = ?",
                           (int(user_id), int(order_id),))
        elif deal_id:
            cursor.execute("DELETE FROM transactions WHERE user_id = ? AND deal_id = ?", (int(user_id), int(deal_id),))
        else:
            raise ValueError("Either order_id or deal_id must be provided")

        conn.commit()

    except sqlite3.Error as e:
        tz = datetime.timezone(datetime.timedelta(hours=3))
        print(f"Error deleting transaction: {e}", datetime.datetime.now(tz).strftime('%d.%m %H:%M'), sep='\n')

    finally:
        conn.close()


# ------------------ УПРАВЛЕНИЕ БАНАМИ ------------------ #


def ban_user(user_id: int, ban_duration_hours: int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(tz)

    if ban_duration_hours == -1:
        banned_until = "forever"
    else:
        banned_until = (now + datetime.timedelta(hours=ban_duration_hours)).strftime('%d.%m.%Y %H:%M')

    # Проверяем, есть ли пользователь в базе данных
    cursor.execute("SELECT id, bans_number FROM bans WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        # Если пользователь уже существует, обновляем запись
        ban_id, bans_number = result
        bans_number += 1
        cursor.execute("""
            UPDATE bans
            SET banned_until = ?, bans_number = ?
            WHERE id = ?
        """, (banned_until, bans_number, ban_id))
    else:
        # Если пользователя нет, добавляем новую запись
        cursor.execute("""
            INSERT INTO bans (user_id, banned_until, bans_number)
            VALUES (?, ?, ?)
        """, (user_id, banned_until, 1))

    conn.commit()
    conn.close()


def get_ban_info(user_id: int) -> Optional[Tuple[int, int, str, int]]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bans WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    return result if result else False


def user_is_not_banned(user_id: int) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT banned_until FROM bans WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return True

    banned_until = result[0]
    if banned_until == "forever":
        return False

    tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(tz)
    banned_until_time = datetime.datetime.strptime(banned_until, '%d.%m.%Y %H:%M').replace(tzinfo=tz)

    return now > banned_until_time


def get_user_activity_summary(user_id: int) -> dict:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    # Calculate total deposited amount
    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE user_id = ? AND action = 'deposit'
    """, (user_id,))
    total_top_up = cursor.fetchone()[0] or 0

    # Count the number of orders created
    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE user_id = ?
    """, (user_id,))
    total_orders = cursor.fetchone()[0]

    # Count the number of deals conducted
    cursor.execute("""
        SELECT COUNT(*)
        FROM matched_orders
        WHERE buyer_id = ? OR seller_id = ?
    """, (user_id, user_id))
    total_deals = cursor.fetchone()[0]

    # Count the number of confirmed deals
    cursor.execute("""
        SELECT COUNT(*)
        FROM matched_orders
        WHERE (buyer_id = ? OR seller_id = ?) AND ststus = 'confirmed'
    """, (user_id, user_id))
    confirmed_deals = cursor.fetchone()[0]

    # Count the number of complaints made against the user
    cursor.execute("""
        SELECT COUNT(*)
        FROM reports
        WHERE offender_id = ?
    """, (user_id,))
    complaints_against_user = cursor.fetchone()[0]

    conn.close()

    return {
        "total_top_up": total_top_up,
        "total_orders": total_orders,
        "total_deals": total_deals,
        "confirmed_deals": confirmed_deals,
        "complaints_against_user": complaints_against_user
    }
