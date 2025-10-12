import sqlite3
from typing import Optional, List
from datetime import datetime


class UserOrderAddress:
    def __init__(
        self,
        id: Optional[int],
        user_id: str,
        order_id: str,
        address_id: str,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.order_id = order_id
        self.address_id = address_id
        self.created_at = created_at

    def __repr__(self):
        return (f"UserOrderAddress(id={self.id!r}, user_id={self.user_id!r}, "
                f"order_id={self.order_id!r}, address_id={self.address_id!r}, "
                f"created_at={self.created_at!r})")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserOrderAddress":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            order_id=row["order_id"],
            address_id=row["address_id"],
            created_at=row["created_at"] if "created_at" in row.keys() else None
        )

    def to_tuple(self) -> tuple:
        return (
            self.user_id,
            self.order_id,
            self.address_id,
            self.created_at
        )


def init_user_order_address_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_order_address (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            address_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (address_id) REFERENCES addresses (id) ON DELETE CASCADE,
            UNIQUE(user_id, order_id, address_id)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_uo_user_id ON user_order_address(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_uo_order_id ON user_order_address(order_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_uo_address_id ON user_order_address(address_id)")
    conn.commit()


def create_user_order_address(conn: sqlite3.Connection, uoa: UserOrderAddress) -> int:
    """Создает связь и возвращает ID созданной записи"""
    sql = """
        INSERT INTO user_order_address (user_id, order_id, address_id, created_at)
        VALUES (?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, uoa.to_tuple())
    conn.commit()
    return cur.lastrowid


def get_user_order_address(conn: sqlite3.Connection, uoa_id: int) -> Optional[UserOrderAddress]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_order_address WHERE id = ?", (uoa_id,))
    row = cur.fetchone()
    return UserOrderAddress.from_row(row) if row else None


def get_relation_by_order(conn: sqlite3.Connection, order_id: str) -> Optional[UserOrderAddress]:
    """Находит связь по ID заказа"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_order_address WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    return UserOrderAddress.from_row(row) if row else None


def get_user_orders(conn: sqlite3.Connection, user_id: str) -> List[UserOrderAddress]:
    """Возвращает все связи для пользователя"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_order_address WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    return [UserOrderAddress.from_row(row) for row in rows]


def get_order_addresses(conn: sqlite3.Connection, order_id: str) -> List[UserOrderAddress]:
    """Возвращает все связи для заказа"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_order_address WHERE order_id = ?", (order_id,))
    rows = cur.fetchall()
    return [UserOrderAddress.from_row(row) for row in rows]


def list_user_order_addresses(conn: sqlite3.Connection) -> List[UserOrderAddress]:
    """Возвращает все связи пользователей и заказов"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_order_address ORDER BY id")
    rows = cur.fetchall()
    return [UserOrderAddress.from_row(row) for row in rows]


def delete_user_order_address(conn: sqlite3.Connection, uoa_id: int) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM user_order_address WHERE id = ?", (uoa_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_relation_by_order(conn: sqlite3.Connection, order_id: str) -> bool:
    """Удаляет связь по ID заказа"""
    cur = conn.cursor()
    cur.execute("DELETE FROM user_order_address WHERE order_id = ?", (order_id,))
    conn.commit()
    return cur.rowcount > 0

def update_user_order_address(conn: sqlite3.Connection, uoa: UserOrderAddress) -> bool:
    """Обновляет связь пользователя и заказа"""
    sql = """
        UPDATE user_order_address SET
            user_id = ?,
            order_id = ?,
            address_id = ?,
            created_at = ?
        WHERE id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (
        uoa.user_id,
        uoa.order_id,
        uoa.address_id,
        uoa.created_at,
        uoa.id
    ))
    conn.commit()
    return cur.rowcount > 0

def user_order_address_table_info(conn: sqlite3.Connection) -> List[str]:
    """Возвращает список названий колонок таблицы связей"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (user_order_address)")
    cols = [r["name"] for r in cur.fetchall()]
    return cols


def get_user_order_addresses_by_user(conn, user_id: str) -> List[UserOrderAddress]:
    """
    Получает все связи пользователь-заказ-адрес для конкретного пользователя
    """
    try:
        cur = conn.cursor()
        # ИСПРАВЛЕННЫЙ ЗАПРОС: добавлено WHERE условие с параметром
        cur.execute("SELECT * FROM user_order_address WHERE user_id = ?", (user_id,))

        results = []
        for row in cur.fetchall():
            results.append(UserOrderAddress(
                id=row['id'],
                user_id=row['user_id'],
                order_id=row['order_id'],
                address_id=row['address_id'],
                created_at=row['created_at']
            ))
        return results
    except Exception as e:
        print(f"Error in get_user_order_addresses_by_user: {e}")
        return []
