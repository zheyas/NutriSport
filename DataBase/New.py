import sqlite3
import setting
from typing import List, Dict, Any


def migrate_orders_table(conn: sqlite3.Connection) -> None:
    """
    Миграция таблицы orders:
    1. Создаем временную таблицу с новой структурой
    2. Переносим данные
    3. Удаляем старую таблицу
    4. Переименовываем временную таблицу
    """
    cur = conn.cursor()

    try:
        # Начинаем транзакцию
        cur.execute("BEGIN TRANSACTION")

        # 1. Проверяем текущую структуру таблицы
        cur.execute("PRAGMA table_info(orders)")
        current_columns = [row[1] for row in cur.fetchall()]
        print(f"Текущие колонки orders: {current_columns}")

        # 2. Создаем временную таблицу с новой структурой (без address_id)
        cur.execute("""
            CREATE TABLE orders_new (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                order_date TEXT NOT NULL,
                total_price REAL NOT NULL CHECK(total_price >= 0),
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
            )
        """)

        # 3. Создаем индексы для новой таблицы
        cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_new_product_id ON orders_new(product_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_new_date ON orders_new(order_date)")

        # 4. Переносим данные (исключаем address_id)
        if 'address_id' in current_columns:
            # Если есть address_id - копируем только нужные колонки
            cur.execute("""
                INSERT INTO orders_new (id, product_id, quantity, order_date, total_price, status)
                SELECT id, product_id, quantity, order_date, total_price, status 
                FROM orders
            """)
            print("Данные перенесены (исключен address_id)")
        else:
            # Если структура уже новая - копируем все
            cur.execute("""
                INSERT INTO orders_new 
                SELECT id, product_id, quantity, order_date, total_price, status 
                FROM orders
            """)
            print("Данные перенесены (структура уже новая)")

        # 5. Удаляем старую таблицу и переименовываем новую
        cur.execute("DROP TABLE orders")
        cur.execute("ALTER TABLE orders_new RENAME TO orders")

        # 6. Фиксируем изменения
        conn.commit()
        print("Миграция orders завершена успешно!")

    except Exception as e:
        # Откатываем в случае ошибки
        conn.rollback()
        print(f"Ошибка миграции: {e}")
        raise


def migrate_user_order_address_data(conn: sqlite3.Connection) -> None:
    """
    Создает связи user_order_address на основе существующих данных
    """
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")

        # Получаем все заказы с их адресами (из старой структуры)
        cur.execute("""
            SELECT o.id as order_id, a.user_id, a.id as address_id
            FROM orders o 
            JOIN addresses a ON o.address_id = a.id
        """)

        orders_with_addresses = cur.fetchall()
        print(f"Найдено {len(orders_with_addresses)} заказов для создания связей")

        # Создаем связи в новой таблице
        for order in orders_with_addresses:
            order_id, user_id, address_id = order
            cur.execute("""
                INSERT INTO user_order_address (user_id, order_id, address_id, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (user_id, order_id, address_id))

        conn.commit()
        print("Миграция данных связей завершена успешно!")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка миграции связей: {e}")
        raise


def check_migration_status(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Проверяет статус миграции"""
    cur = conn.cursor()

    # Проверяем структуру orders
    cur.execute("PRAGMA table_info(orders)")
    orders_columns = [row[1] for row in cur.fetchall()]

    # Проверяем существование таблицы связей
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_order_address'")
    has_relation_table = cur.fetchone() is not None

    # Считаем количество связей
    relation_count = 0
    if has_relation_table:
        cur.execute("SELECT COUNT(*) FROM user_order_address")
        relation_count = cur.fetchone()[0]

    # Считаем количество заказов
    cur.execute("SELECT COUNT(*) FROM orders")
    orders_count = cur.fetchone()[0]

    return {
        'orders_columns': orders_columns,
        'has_address_id': 'address_id' in orders_columns,
        'has_relation_table': has_relation_table,
        'relation_count': relation_count,
        'orders_count': orders_count
    }


if __name__ == "__main__":
    conn = setting.conn_str

    # Проверяем текущий статус
    status = check_migration_status(conn)
    print("Статус до миграции:")
    print(f"  Колонки orders: {status['orders_columns']}")
    print(f"  Есть address_id: {status['has_address_id']}")
    print(f"  Есть таблица связей: {status['has_relation_table']}")
    print(f"  Количество заказов: {status['orders_count']}")

    # Запускаем миграцию
    if status['has_address_id']:
        print("\nЗапуск миграции...")
        migrate_orders_table(conn)
        migrate_user_order_address_data(conn)

        # Проверяем результат
        new_status = check_migration_status(conn)
        print("\nСтатус после миграции:")
        print(f"  Колонки orders: {new_status['orders_columns']}")
        print(f"  Есть address_id: {new_status['has_address_id']}")
        print(f"  Есть таблица связей: {new_status['has_relation_table']}")
        print(f"  Количество связей: {new_status['relation_count']}")
        print(f"  Количество заказов: {new_status['orders_count']}")
    else:
        print("Миграция не требуется - структура уже актуальна")