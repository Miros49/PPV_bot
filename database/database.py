import datetime
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
                        ballance REAL DEFAULT 0.00,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        username TEXT,
                        action TEXT,
                        project TEXT,
                        server TEXT,
                        amount REAL,
                        status TEXT DEFAULT 'active',
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
                            timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id, username, phone_number, ballance, created_at FROM users WHERE user_id=?",
                   (user_id,))

    user_data = cursor.fetchone()
    conn.close()

    return user_data


def get_user_id_by_id(user_id_in_database: int) -> int | None:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE id = ?", (user_id_in_database,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None


def get_orders_by_user_id(user_id):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, action, project, server, amount, status, created_at
        FROM orders
        WHERE user_id = ?
    """, (user_id,))

    orders = cursor.fetchall()
    conn.close()

    return orders


def get_user_id_by_order(order_id: int | str) -> int:
    conn = sqlite3.connect(database_file)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id
        FROM orders
        WHERE id = ?
    """, (int(order_id),))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def add_user(user_id, username, phone_number):
    conn = sqlite3.connect(database_file)

    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, phone_number) VALUES (?, ?, ?)",
                   (user_id, username, phone_number))
    conn.commit()
    conn.close()


def edit_ballance(user_id: int, amount: float | int):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (result[0] + amount, user_id))

    conn.commit()
    conn.close()


def add_order(user_id, username, action, project, server, amount):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (user_id, username, action, project, server, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (user_id, username, action, project, server, amount))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_order(order_id: int | str) -> Tuple[int, int, str, str, str, str, float, str, str]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("""
                SELECT *
                FROM orders
                WHERE id = ?
            """, (int(order_id),))
    result = cursor.fetchone()
    conn.close()
    return result if result else None


def save_chat_message(chat_id, sender_id, receiver_id, message):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_logs (chat_id, sender_id, receiver_id, message) VALUES (?, ?, ?, ?)",
                   (chat_id, sender_id, receiver_id, message))
    conn.commit()
    conn.close()


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
        return match[0], match[1]  # Returning order_id and user_id of the matched order
    return None


def get_pending_sell_orders(user_id: int, project: str, server: str) \
        -> List[Tuple[int, int, str, str, str, str, float, str, str]]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, username, action, project, server, amount, status, created_at
        FROM orders
        WHERE user_id != ? AND action = 'sell' AND project = ? AND server = ? AND status = 'pending'
        ORDER BY amount ASC
    """, (user_id, project, server))
    orders = cursor.fetchall()
    conn.close()
    return orders


def create_report(order_id: int | str, complainer_id: int | str, offender_id: int | str, complaint: str):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (order_id, complainer_id, offender_id, complaint)
        VALUES (?, ?, ?, ?)
    """, (int(order_id), int(complainer_id), int(offender_id), complaint))
    conn.commit()
    conn.close()


def get_report(report_id: int | str) -> Tuple[int, int, int, int, str, str, str]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM reports WHERE id = ?''', (int(report_id),))
    report = cursor.fetchone()
    conn.close()
    return report


def get_open_reports() -> List[Tuple[int, int, int, int, str]]:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute('''SELECT id, order_id, complainer_id, offender_id, complaint FROM reports WHERE status = 'open' ''')
    open_reports = cursor.fetchall()

    conn.close()

    return open_reports


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
