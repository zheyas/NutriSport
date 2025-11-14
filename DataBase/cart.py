# DataBase/cart.py
import sqlite3
from datetime import datetime
from typing import List, Optional


class CartItem:
    def __init__(self, id: int = None, user_id: str = None, product_id: str = None,
                 quantity: int = 1, created_at: str = None):
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.created_at = created_at or datetime.now().isoformat()


def init_cart_table(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(user_id, product_id)
        )
    """)
    conn.commit()


def get_cart_items(conn: sqlite3.Connection, user_id: str) -> List[CartItem]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cart WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()

    items = []
    for row in rows:
        items.append(CartItem(
            id=row[0],
            user_id=row[1],
            product_id=row[2],
            quantity=row[3],
            created_at=row[4]
        ))
    return items


def add_to_cart(conn: sqlite3.Connection, user_id: str, product_id: str, quantity: int = 1) -> bool:
    try:
        cursor = conn.cursor()

        # Проверяем, есть ли уже товар в корзине
        cursor.execute("SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?",
                       (user_id, product_id))
        existing = cursor.fetchone()

        if existing:
            # Обновляем количество
            new_quantity = existing[1] + quantity
            cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, existing[0]))
        else:
            # Добавляем новый товар
            cursor.execute(
                "INSERT INTO cart (user_id, product_id, quantity, created_at) VALUES (?, ?, ?, ?)",
                (user_id, product_id, quantity, datetime.now().isoformat())
            )

        conn.commit()
        return True
    except sqlite3.Error:
        return False


def update_cart_item(conn: sqlite3.Connection, cart_item_id: int, quantity: int) -> bool:
    try:
        cursor = conn.cursor()
        if quantity <= 0:
            # Если количество <= 0, удаляем товар из корзины
            cursor.execute("DELETE FROM cart WHERE id = ?", (cart_item_id,))
        else:
            cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_item_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False


def update_cart_item_full(conn: sqlite3.Connection, cart_item_id: int, user_id: str, product_id: str,
                          quantity: int) -> bool:
    """Обновить все поля элемента корзины с проверкой уникальности"""
    try:
        cursor = conn.cursor()

        # Проверяем, существует ли элемент корзины
        cursor.execute("SELECT id FROM cart WHERE id = ?", (cart_item_id,))
        if not cursor.fetchone():
            return False

        # Проверяем, нет ли у этого пользователя уже такого товара в корзине (кроме текущего элемента)
        cursor.execute("""
            SELECT id FROM cart 
            WHERE user_id = ? AND product_id = ? AND id != ?
        """, (user_id, product_id, cart_item_id))

        if cursor.fetchone():
            # У пользователя уже есть этот товар в корзине
            return False

        # Обновляем элемент корзины
        cursor.execute("""
            UPDATE cart 
            SET user_id = ?, product_id = ?, quantity = ?, updated_at = ?
            WHERE id = ?
        """, (user_id, product_id, quantity, datetime.now().isoformat(), cart_item_id))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating cart item: {e}")
        return False

def remove_from_cart(conn: sqlite3.Connection, cart_item_id: int) -> bool:
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE id = ?", (cart_item_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False


def clear_cart(conn: sqlite3.Connection, user_id: str) -> bool:
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False


def get_cart_total(conn: sqlite3.Connection, user_id: str) -> float:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(c.quantity * p.price) 
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    return result[0] or 0.0


def get_cart_items_count(conn: sqlite3.Connection, user_id: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantity) FROM cart WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] or 0


def list_all_cart_items(conn):
    """Получить все записи корзины с информацией о пользователях и товарах"""
    cursor = conn.cursor()

    query = """
    SELECT 
        c.id,
        c.user_id,
        u.first_name as user_first_name,
        u.last_name as user_last_name,
        c.product_id,
        p.name as product_name,
        c.quantity,
        p.price as product_price,
        (c.quantity * p.price) as total_price,
        c.created_at,
        c.updated_at
    FROM cart c
    LEFT JOIN users u ON c.user_id = u.id
    LEFT JOIN products p ON c.product_id = p.id
    ORDER BY c.created_at DESC
    """

    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    results = []

    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    return results


def cart_table_info(conn):
    """Получить заголовки таблицы корзины"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(cart)")
    cart_columns = [col[1] for col in cursor.fetchall()]

    # Добавляем дополнительные поля из JOIN
    additional_columns = [
        'user_first_name',
        'user_last_name',
        'product_name',
        'product_price',
        'total_price'
    ]

    return cart_columns + additional_columns


def get_cart_item(conn: sqlite3.Connection, cart_id: int) -> Optional[CartItem]:
    """Получить элемент корзины по ID"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.*,
            u.first_name as user_first_name,
            u.last_name as user_last_name, 
            p.name as product_name,
            p.price as product_price,
            (p.price * c.quantity) as total_price
        FROM cart c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN products p ON c.product_id = p.id
        WHERE c.id = ?
    """, (cart_id,))

    row = cursor.fetchone()

    if row:
        cart_item = CartItem(
            id=row[0],
            user_id=row[1],
            product_id=row[2],
            quantity=row[3],
            created_at=row[4]
        )
        # Добавляем дополнительную информацию как атрибуты
        cart_item.user_first_name = row[5]
        cart_item.user_last_name = row[6]
        cart_item.product_name = row[7]
        cart_item.product_price = row[8]
        cart_item.total_price = row[9]
        return cart_item
    return None


def get_cart_item_by_user_product(conn: sqlite3.Connection, user_id: str, product_id: str) -> Optional[CartItem]:
    """Получить элемент корзины по user_id и product_id"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))

    row = cursor.fetchone()

    if row:
        return CartItem(
            id=row[0],
            user_id=row[1],
            product_id=row[2],
            quantity=row[3],
            created_at=row[4]
        )
    return None


def get_user_cart_items_count(conn: sqlite3.Connection, user_id: str) -> int:
    """Получить количество товаров в корзине пользователя"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0
