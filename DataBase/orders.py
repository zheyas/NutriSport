#DataBase/orders.py
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import setting


# --- Инициализация таблицы ----------------------------------

def init_orders_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            order_date TEXT NOT NULL,
            total_price REAL NOT NULL CHECK(total_price >= 0),
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)")
    conn.commit()


# --- Модель -------------------------------------------------

class Order:
    def __init__(
            self,
            id: str,
            product_id: str,
            quantity: int,
            order_date: str,
            total_price: float,
            status: str = 'pending'
    ):
        self.id = id
        self.product_id = product_id
        self.quantity = quantity
        self.order_date = order_date
        self.total_price = total_price
        self.status = status

    def __repr__(self):
        return (f"Order(id={self.id!r}, product_id={self.product_id!r}, quantity={self.quantity!r}, "
                f"order_date={self.order_date!r}, total_price={self.total_price!r}, status={self.status!r})")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Order":
        # Используем прямое обращение к полям через индексацию вместо .get()
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            order_date=row["order_date"],
            total_price=row["total_price"],
            status=row["status"] if "status" in row.keys() else "pending"  # Проверяем наличие поля
        )

    def to_tuple(self) -> tuple:
        return (
            self.id, self.product_id, self.quantity,
            self.order_date, self.total_price, self.status
        )


# --- CRUD операции ------------------------------------------

def create_order(conn: sqlite3.Connection, order: Order) -> None:
    sql = """
        INSERT INTO orders (id, product_id, quantity, order_date, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, order.to_tuple())
    conn.commit()


def get_order(conn: sqlite3.Connection, order_id: str) -> Optional[Order]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    return Order.from_row(row) if row else None


def update_order(conn: sqlite3.Connection, order: Order) -> bool:
    sql = """
        UPDATE orders SET
            product_id = ?, quantity = ?, order_date = ?,
            total_price = ?, status = ?
        WHERE id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (
        order.product_id, order.quantity, order.order_date,
        order.total_price, order.status, order.id
    ))
    conn.commit()
    return cur.rowcount > 0


def delete_order(conn: sqlite3.Connection, order_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    return cur.rowcount > 0


def list_orders(conn: sqlite3.Connection) -> List[Order]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY order_date DESC")
    rows = cur.fetchall()
    return [Order.from_row(row) for row in rows]


def orders_with_details(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Возвращает заказы с дополнительной информацией о товаре через таблицу связей"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*, p.name as product_name, p.price as product_price,
               uoa.user_id, uoa.address_id,
               u.first_name, u.last_name,
               a.country, a.city, a.street, a.house_number, a.apartment
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN user_order_address uoa ON o.id = uoa.order_id
        LEFT JOIN users u ON uoa.user_id = u.id
        LEFT JOIN addresses a ON uoa.address_id = a.id
        ORDER BY o.order_date DESC
    """)
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def orders_by_user(conn: sqlite3.Connection, user_id: str) -> List[Dict[str, Any]]:
    """Возвращает заказы конкретного пользователя"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*, p.name as product_name, p.price as product_price,
               uoa.address_id, a.country, a.city, a.street, a.house_number, a.apartment
        FROM orders o
        JOIN user_order_address uoa ON o.id = uoa.order_id
        JOIN products p ON o.product_id = p.id
        LEFT JOIN addresses a ON uoa.address_id = a.id
        WHERE uoa.user_id = ?
        ORDER BY o.order_date DESC
    """, (user_id,))
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def orders_by_product(conn: sqlite3.Connection, product_id: str) -> List[Order]:
    """Возвращает заказы по конкретному товару"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE product_id = ? ORDER BY order_date DESC", (product_id,))
    rows = cur.fetchall()
    return [Order.from_row(row) for row in rows]


# --- Генерация ID в формате ORD{n} --------------------------

def get_next_order_id(conn: sqlite3.Connection, pad: int = 3) -> str:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(SUBSTR(id, 4) AS INTEGER)) as maxnum FROM orders")
    row = cur.fetchone()
    maxnum = row["maxnum"] or 0
    n = maxnum + 1
    return f"ORD{n:0{pad}d}"


# --- Информация о таблице -----------------------------------

def orders_table_info(conn: sqlite3.Connection) -> List[str]:
    """Возвращает список названий колонок таблицы заказов"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (orders)")
    cols = [r["name"] for r in cur.fetchall()]
    return cols


# --- Расчет общей стоимости ---------------------------------

def calculate_total_price(conn: sqlite3.Connection, product_id: str, quantity: int) -> float:
    """Рассчитывает общую стоимость заказа на основе цены товара"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT price FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Товар с ID {product_id} не найден")
    product_price = row["price"]
    return product_price * quantity


# --- Статистика и аналитика ---------------------------------

def get_orders_statistics(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Возвращает статистику по заказам"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Общее количество заказов
    cur.execute("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = cur.fetchone()["total_orders"]

    # Заказы по статусам
    cur.execute("""
        SELECT status, COUNT(*) as count 
        FROM orders 
        GROUP BY status
    """)
    status_stats = {row["status"]: row["count"] for row in cur.fetchall()}

    # Общая выручка
    cur.execute("SELECT SUM(total_price) as total_revenue FROM orders")
    total_revenue = cur.fetchone()["total_revenue"] or 0

    # Средний чек
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    return {
        "total_orders": total_orders,
        "status_stats": status_stats,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value
    }


def get_recent_orders(conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, Any]]:
    """Возвращает последние заказы"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*, p.name as product_name, 
               u.first_name, u.last_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN user_order_address uoa ON o.id = uoa.order_id
        JOIN users u ON uoa.user_id = u.id
        ORDER BY o.order_date DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    return [dict(row) for row in rows]


# В файл DataBase/orders.py добавьте/обновите функции:

def get_largest_order(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """Получить самый большой заказ по общей стоимости"""
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                o.id as order_id,
                o.product_id,
                o.quantity,
                o.total_price,
                o.order_date,
                o.status,
                p.name as product_name,
                p.price as unit_price,
                u.id as user_id,
                u.first_name,
                u.last_name,
                u.email,
                a.country,
                a.city,
                a.street,
                a.house_number,
                a.apartment
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN user_order_address uoa ON o.id = uoa.order_id
            LEFT JOIN users u ON uoa.user_id = u.id
            LEFT JOIN addresses a ON uoa.address_id = a.id
            ORDER BY o.total_price DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        return dict(result) if result else None
    except Exception as e:
        print(f"Error in get_largest_order: {e}")
        return None


def get_category_lovers(conn: sqlite3.Connection, category: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Получить топ пользователей по покупкам в определенной категории"""
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.id as user_id,
                u.first_name,
                u.last_name,
                u.email,
                COUNT(DISTINCT o.id) as orders_count,
                SUM(o.quantity) as total_quantity,
                SUM(o.total_price) as total_spent,
                GROUP_CONCAT(DISTINCT p.name) as favorite_products
            FROM users u
            JOIN user_order_address uoa ON u.id = uoa.user_id
            JOIN orders o ON uoa.order_id = o.id
            JOIN products p ON o.product_id = p.id
            WHERE p.category = ?
            GROUP BY u.id, u.first_name, u.last_name, u.email
            ORDER BY total_spent DESC
            LIMIT ?
        """, (category, limit))

        results = []
        for row in cur.fetchall():
            results.append({
                'user_id': row['user_id'],
                'name': f"{row['first_name']} {row['last_name']}",
                'email': row['email'],
                'orders_count': row['orders_count'],
                'total_quantity': row['total_quantity'],
                'total_spent': row['total_spent'],
                'favorite_products': row['favorite_products'].split(',')[:3] if row['favorite_products'] else []
            })
        return results
    except Exception as e:
        print(f"Error in get_category_lovers: {e}")
        return []


def get_user_favorite_product(conn: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    """Получить любимый товар пользователя"""
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.category,
                p.price,
                p.image,
                COUNT(o.id) as purchase_count,
                SUM(o.total_price) as total_spent,
                MAX(o.order_date) as last_purchase
            FROM products p
            JOIN orders o ON p.id = o.product_id
            JOIN user_order_address uoa ON o.id = uoa.order_id
            WHERE uoa.user_id = ?
            GROUP BY p.id, p.name, p.category, p.price, p.image
            ORDER BY purchase_count DESC, total_spent DESC
            LIMIT 1
        """, (user_id,))

        result = cur.fetchone()
        if result:
            # Рассчитываем рейтинг на основе количества покупок
            purchase_count = result['purchase_count']
            if purchase_count >= 10:
                rating = 5
            elif purchase_count >= 5:
                rating = 4
            elif purchase_count >= 3:
                rating = 3
            elif purchase_count >= 2:
                rating = 2
            else:
                rating = 1

            return {
                'id': result['id'],
                'name': result['name'],
                'category': result['category'],
                'price': result['price'],
                'image_url': result['image'] or '/static/images/placeholder-product.jpg',
                'purchase_count': purchase_count,
                'total_spent': result['total_spent'],
                'last_purchase': result['last_purchase'],
                'rating': rating
            }
        return None
    except Exception as e:
        print(f"Error in get_user_favorite_product: {e}")
        return None


# Добавьте также функцию для проверки существования пользователя
def user_exists(conn: sqlite3.Connection, user_id: str) -> bool:
    """Проверить существование пользователя"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        return cur.fetchone() is not None
    except Exception as e:
        print(f"Error in user_exists: {e}")
        return False

if __name__ == "__main__":
    print(orders_table_info(setting.conn_str))