import datetime
import math
import sqlite3

from typing import List, Tuple, Optional

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
                            amount REAL,
                            sender_id INTEGER,
                            receiver_id INTEGER,
                            order_id INTEGER,
                            timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_id INTEGER,
                            complainer_id INTEGER,
                            offender_id INTEGER,
                            complaint TEXT,
                            status TEXT DEFAULT 'open',
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS prices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            project TEXT,
                            server TEXT,
                            buy INTEGER DEFAULT 100,
                            sell INTEGER DEFAULT 100)''')

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
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    current_time = get_current_time_formatted()
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
    cursor.execute("SELECT id FROM users WHERE user_id=?", (user_id,))  # TODO: нафиг отсюда
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


def get_orders_by_user_id(user_id):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
    """, (user_id,))

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


def edit_balance(user_id: int, amount: float | int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (result[0] + amount, user_id))

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


def get_item(order_id: int | str) -> str:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT item FROM orders WHERE id = ?''', (int(order_id),))

    item = cursor.fetchone()
    conn.close()
    return item


def match_orders(user_id, action, project, server, amount):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    if action == 'buy':
        cursor.execute("""
            SELECT id, user_id
            FROM orders
            WHERE action = 'sell' AND project = ? AND server = ? AND amount = ? AND status = 'pending' AND user_id != ?
            LIMIT 1

        """, (project, server, amount, user_id))
    else:
        cursor.execute("""
            SELECT id, user_id
            FROM orders
            WHERE action = 'buy' AND project = ? AND server = ? AND amount = ? AND status = 'pending' AND user_id != ?
            LIMIT 1
        """, (project, server, amount, user_id))

    match = cursor.fetchone()
    conn.close()

    if match:
        return match[0], match[1]
    return None


def get_pending_sell_orders(user_id: int, item: str, project: str, server: str) -> List[Tuple]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM orders
        WHERE user_id != ? AND action = 'sell' AND item = ? AND project = ? AND server = ? AND status = 'pending'
        ORDER BY amount ASC""", (user_id, item, project, server))

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

    cursor.execute(
        '''SELECT id, order_id, complainer_id, offender_id, complaint, created_at FROM reports WHERE status = 'open' ''')

    open_reports = cursor.fetchall()
    conn.close()

    return open_reports


def get_complaints(user_id) -> List[Tuple[int, int, str]]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT id, order_id, created_at, complaint FROM reports WHERE complainer_id = ? ''', (user_id,))

    report_info = cursor.fetchall()
    conn.close()

    return report_info


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


def get_matched_order(order_id: int | str) -> Tuple[int, int, int, int, int, str, str]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM matched_orders WHERE id = ?''', (int(order_id),))
    order = cursor.fetchone()
    conn.close()
    return order


def get_user_matched_orders(user_id: int) -> List[int]:
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


def update_matched_order_status(order_id: int, new_status: str) -> bool:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE matched_orders 
            SET ststus = ? 
            WHERE id = ?''',
                       (new_status, order_id)
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

    cursor.execute("""SELECT id FROM prices WHERE """, (project, server))
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
