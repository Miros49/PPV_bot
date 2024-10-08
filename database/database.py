import datetime
import sqlite3
from collections import defaultdict

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from typing import List, Tuple, Optional, Union

from core import config, storage
from states import UserStates

database_file = 'database/database.db'


def init_db():
    create_tables()


def create_tables():
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            phone_number TEXT,
            balance REAL DEFAULT 0.00,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            item TEXT,
            project TEXT,
            server TEXT,
            amount INTEGER,
            description TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER,
            sender_id INTEGER,
            receiver_id INTEGER,
            type TEXT,
            message TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            buyer_order_id INTEGER,
            seller_id INTEGER,
            seller_order_id INTEGER,
            ststus TEXT DEFAULT 'open',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
    ''')
    # completion_timestamp TEXT DEFAULT NONE

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bot_user_id INTEGER,
                            user_id INTEGER,
                            order_id INTEGER DEFAULT 0,
                            deal_id INTEGER DEFAULT 0,
                            amount REAL,
                            action TEXT,
                            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            complainer_id INTEGER,
            offender_id INTEGER,
            complaint TEXT,
            status TEXT DEFAULT 'open',
            answer TEXT DEFAULT NONE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT,
            server TEXT,
            buy INTEGER DEFAULT 100,
            sell INTEGER DEFAULT 100
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            banned_until TEXT,
            bans_number INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT,
            source_id INTEGER,
            action TEXT,
            amount REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS remembered_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE
        )
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS service (technical_work INTEGER DEFAULT 0)''')

    conn.commit()
    conn.close()


def get_current_time_formatted() -> str:
    tz = datetime.timezone(datetime.timedelta(hours=3))  # GMT+3
    now = datetime.datetime.now(tz)
    return now.strftime('%d.%m.%Y %H:%M')


def add_user(user_id, username, phone_number):
    current_time = get_current_time_formatted()

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, phone_number, created_at) VALUES (?, ?, ?, ?)",
                   (user_id, username, phone_number, current_time))
    conn.commit()
    conn.close()


def create_report(order_id: int | str, complainer_id: int | str, offender_id: int | str, complaint: str):
    current_time = get_current_time_formatted()

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

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


def get_all_user_ids() -> List[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    return user_ids


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


def get_user_by_id(user_id_in_database: int | str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id_in_database),))
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


def count_users() -> int:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    user_count = cursor.fetchone()[0]
    conn.close()

    return user_count


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
        FROM deals
        WHERE buyer_id = ? OR seller_id = ?
    """, (user_id, user_id))
    total_deals = cursor.fetchone()[0]

    # Count the number of confirmed deals
    cursor.execute("""
        SELECT COUNT(*)
        FROM deals
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


# ------------------ УПРАВЛЕНИЕ ЗАКАЗАМИ ------------------ #


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
        cursor.execute("""
            UPDATE orders
            SET status = 'deleted'
            WHERE id = ?
        """, (int(order_id),))
        conn.commit()
        return True

    except sqlite3.Error as e:
        print(f"Ошибка при изменении статуса заказа: {e}", datetime.datetime.now().time(), sep='\n')
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

        other_user_state = FSMContext(
            storage, StorageKey(bot_id=int(config.tg_bot.token.split(':')[0]), chat_id=user_id, user_id=user_id))
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


def count_active_orders() -> int:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'pending'
    """)

    active_orders_count = cursor.fetchone()[0]
    conn.close()

    return active_orders_count


def get_deal_id_by_order_id(order_id: int | str) -> Optional[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id
        FROM deals
        WHERE (buyer_order_id = ? OR seller_order_id = ?) AND ststus = 'confirmed'
    ''', (int(order_id), int(order_id)))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


# ------------------ УПРАВЛЕНИЕ ЖАЛОБАМИ ------------------ #


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


def get_complaint(complaint_id: int | str) -> Tuple[int, int, int, int, str, str, str, str]:
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


def set_complaint_status(complaint_id: int | str, status: str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reports
        SET status = ?
        WHERE id = ?
    """, (status, int(complaint_id)))

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


def create_deal(buyer_id: int, buyer_order_id: int, seller_id: int, seller_order_id: int) -> Optional[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''INSERT INTO deals (
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

    cursor.execute('''SELECT * FROM deals WHERE id = ?''', (int(deal_id),))

    order = cursor.fetchone()
    conn.close()

    return order


def get_user_deals(user_id: int) -> List[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM deals
        WHERE buyer_id = ? OR seller_id = ?
    """, (user_id, user_id))

    deal_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return deal_ids


def update_deal_status(deal_id: int | str, new_status: str) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE deals 
            SET ststus = ? 
            WHERE id = ?''',
                       (new_status, int(deal_id))
                       )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении статуса: {e}", datetime.datetime.now().time(), sep='\n')
        return False


def check_deal(deal_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id 
        FROM deals
        WHERE id = ? AND (buyer_id = ? OR seller_id = ?)
    """, (deal_id, user_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def count_active_deals() -> int:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM deals
        WHERE ststus = 'open'
    """)

    active_deals_count = cursor.fetchone()[0]
    conn.close()

    return active_deals_count


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


# ------------------ УПРАВЛЕНИЕ ТРАНЗАКЦИЯМИ ------------------ #


def add_transaction(user_id: int, amount: float, action: str, order_id: int = 0, deal_id: int = 0):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    current_time = get_current_time_formatted()

    cursor.execute("""
        INSERT INTO transactions (bot_user_id, user_id, order_id, deal_id, amount, action, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (get_bot_user_id(user_id), user_id, order_id, deal_id, amount, action, current_time))

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


def get_transactions(user_id: int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, user_id, amount, action, deal_id, timestamp 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        """, (user_id,))

        transactions = cursor.fetchall()
        transactions_by_day = defaultdict(list)

        for trans in transactions:
            date = trans[-1].split(' ')[0]
            transactions_by_day[date].append(trans)

        return sorted(transactions_by_day.items(), reverse=True)

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return []

    finally:
        conn.close()


def get_cashout_transactions(user_id: int) -> List[Tuple]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ? AND action = 'cashout'
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


def user_is_not_banned(user_id: int | str) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT banned_until FROM bans WHERE user_id = ?", (int(user_id),))

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


def unban_user(user_id: int) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    # есть ли такой тип в бд
    cursor.execute("SELECT id FROM bans WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        tz = datetime.timezone(datetime.timedelta(hours=3))
        current_time = datetime.datetime.now(tz).strftime('%d.%m.%Y %H:%M')

        # разбан
        cursor.execute("UPDATE bans SET banned_until = ? WHERE user_id = ?", (current_time, user_id))
        conn.commit()

        unbanned = True

    else:
        unbanned = False

    conn.close()
    return unbanned


# ------------------ УПРАВЛЕНИЕ ЛОГАМИ СДЕЛОК ------------------ #


def save_chat_message(deal_id, sender_id, receiver_id, message_type, message):
    current_time = get_current_time_formatted()

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chat_logs (deal_id, sender_id, receiver_id, type, message, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (deal_id, sender_id, receiver_id, message_type, message, current_time)
    )

    conn.commit()
    conn.close()


def get_chat_messages(deal_id: int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM chat_logs
        WHERE deal_id = ?
        ORDER BY timestamp ASC
    """, (deal_id,))

    messages = cursor.fetchall()
    conn.close()

    return messages


# ------------------ УПРАВЛЕНИЕ ДОХОДОМ ------------------ #


def add_income(source_type, source_id, action, amount):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO income (source_type, source_id, action, amount)
                      VALUES (?, ?, ?, ?)''', (source_type, source_id, action, amount))

    conn.commit()


def calculate_profit():
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT 
                        (SELECT COALESCE(SUM(amount), 0) FROM income WHERE action = 'income') - 
                        (SELECT COALESCE(SUM(amount), 0) FROM income WHERE action = 'loss') 
                      AS profit''')

    result = cursor.fetchone()

    return round(result[0]) if result else 0


# ------------------ УПРАВЛЕНИЕ техническим перерывом ------------------ #


def is_technical_work():
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT technical_work FROM service LIMIT 1''')

    result = cursor.fetchone()

    return True if result and result[0] == 1 else False


def set_technical_work(is_enabled):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''UPDATE service SET technical_work = ?''', (1 if is_enabled else 0,))

    conn.commit()


def init_user_memory_db():
    """Инициализация базы данных для хранения user_id."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    # Создание таблицы для хранения user_id, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS remembered_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE
        )
    ''')

    conn.commit()
    conn.close()


def remember_user_id(user_id: int):
    """Запоминает user_id, для оповещения об окончании тех работ"""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT OR IGNORE INTO remembered_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении user_id: {e}")
    finally:
        conn.close()


def get_remembered_user_ids() -> List[int]:
    """Возвращает список всех запомненных user_id и очищает список."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM remembered_users")
        user_ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Ошибка при получении: {e}")
        user_ids = []
    finally:
        conn.close()

    return user_ids


def delete_user_memory_table():
    """Удаляет таблицу user_memory из базы данных."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        # Удаляем таблицу user_memory
        cursor.execute("DROP TABLE IF EXISTS user_memory")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при удалении таблицы: {e}")
    finally:
        conn.close()


# ------------------ УПРАВЛЕНИЕ приветственной базой данных ------------------ #


def init_wellcome_db():
    """Инициализация базы данных для хранения user_id."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS welcome_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE
        )
    ''')

    conn.commit()
    conn.close()


def remember_welcomed_user_id(user_id: int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT OR IGNORE INTO welcome_db (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении user_id в welcome_db: {e}")
    finally:
        conn.close()


def is_user_welcomed(user_id: int) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM welcome_db WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"Ошибка при проверке наличия user_id в welcome_db: {e}")
        return False
    finally:
        conn.close()


def get_welcomed_user_ids() -> List[int]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM welcome_db")
        user_ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Ошибка при получении из welcome_db: {e}")
        user_ids = []
    finally:
        conn.close()

    return user_ids


def delete_welcome_db():
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        # Удаляем таблицу user_memory
        cursor.execute("DROP TABLE IF EXISTS welcome_db")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при удалении таблицы: {e}")
    finally:
        conn.close()
