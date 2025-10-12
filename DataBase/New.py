import sqlite3
import random
from datetime import datetime, timedelta
import setting


def fill_user_order_address_table(conn: sqlite3.Connection) -> None:
    """
    Заполняет таблицу user_order_address случайными связями
    на основе существующих пользователей, заказов и адресов
    """
    # Устанавливаем row_factory для возврата словарей
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")

        # Получаем существующие данные
        users = get_all_users(conn)
        orders = get_all_orders(conn)
        addresses = get_all_addresses(conn)

        print(f"Найдено: {len(users)} пользователей, {len(orders)} заказов, {len(addresses)} адресов")

        if not users or not orders or not addresses:
            print("Недостаточно данных для создания связей")
            return

        # Очищаем таблицу перед заполнением
        cur.execute("DELETE FROM user_order_address")
        print("Таблица user_order_address очищена")

        created_relations = 0

        # Создаем связи для каждого заказа
        for order in orders:
            order_id = order['id']

            # Случайно выбираем пользователя
            user = random.choice(users)
            user_id = user['id']

            # Находим адреса этого пользователя
            user_addresses = [addr for addr in addresses if addr['user_id'] == user_id]

            if user_addresses:
                # Выбираем случайный адрес пользователя
                address = random.choice(user_addresses)
                address_id = address['id']

                # Создаем связь
                created_at = generate_random_date()

                cur.execute("""
                    INSERT INTO user_order_address (user_id, order_id, address_id, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, order_id, address_id, created_at))

                created_relations += 1

                # Выводим прогресс каждые 10 записей
                if created_relations % 10 == 0:
                    print(f"Создано связей: {created_relations}")

        conn.commit()
        print(f"✅ Успешно создано {created_relations} связей в таблице user_order_address")

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при заполнении таблицы: {e}")
        raise


def get_all_users(conn: sqlite3.Connection) -> list:
    """Получает всех пользователей из БД"""
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    return [dict(row) for row in cur.fetchall()]


def get_all_orders(conn: sqlite3.Connection) -> list:
    """Получает все заказы из БД"""
    cur = conn.cursor()
    cur.execute("SELECT id, order_date FROM orders")
    return [dict(row) for row in cur.fetchall()]


def get_all_addresses(conn: sqlite3.Connection) -> list:
    """Получает все адреса из БД"""
    cur = conn.cursor()
    cur.execute("SELECT id, user_id FROM addresses")
    return [dict(row) for row in cur.fetchall()]


def generate_random_date(start_date: str = "2023-01-01", end_date: str = "2024-12-31") -> str:
    """
    Генерирует случайную дату в указанном диапазоне
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    random_days = random.randint(0, (end - start).days)
    random_date = start + timedelta(days=random_days)

    return random_date.strftime("%Y-%m-%d %H:%M:%S")


def check_table_data(conn: sqlite3.Connection) -> dict:
    """
    Проверяет данные в таблицах
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    stats = {}

    # Проверяем users
    cur.execute("SELECT COUNT(*) as count FROM users")
    stats['users_count'] = cur.fetchone()['count']

    # Проверяем orders
    cur.execute("SELECT COUNT(*) as count FROM orders")
    stats['orders_count'] = cur.fetchone()['count']

    # Проверяем addresses
    cur.execute("SELECT COUNT(*) as count FROM addresses")
    stats['addresses_count'] = cur.fetchone()['count']

    # Проверяем user_order_address
    cur.execute("SELECT COUNT(*) as count FROM user_order_address")
    stats['relations_count'] = cur.fetchone()['count']

    # Проверяем распределение адресов по пользователям
    cur.execute("""
        SELECT user_id, COUNT(*) as address_count 
        FROM addresses 
        GROUP BY user_id
    """)
    user_address_stats = cur.fetchall()
    stats['users_with_addresses'] = len(user_address_stats)
    stats['avg_addresses_per_user'] = sum(row['address_count'] for row in user_address_stats) / len(
        user_address_stats) if user_address_stats else 0

    return stats


def print_statistics(stats: dict) -> None:
    """Выводит статистику данных"""
    print("\n=== СТАТИСТИКА БАЗЫ ДАННЫХ ===")
    print(f"Пользователей: {stats['users_count']}")
    print(f"Заказов: {stats['orders_count']}")
    print(f"Адресов: {stats['addresses_count']}")
    print(f"Связей user_order_address: {stats['relations_count']}")
    print(f"Пользователей с адресами: {stats['users_with_addresses']}")
    print(f"Среднее количество адресов на пользователя: {stats['avg_addresses_per_user']:.1f}")


def main():
    """Основная функция"""
    conn = setting.conn_str

    try:
        # Проверяем текущее состояние
        print("Проверяем текущее состояние базы данных...")
        stats_before = check_table_data(conn)
        print_statistics(stats_before)

        # Запрашиваем подтверждение
        if stats_before['relations_count'] > 0:
            response = input(
                f"\nВ таблице user_order_address уже есть {stats_before['relations_count']} записей. Перезаписать? (y/N): ")
            if response.lower() != 'y':
                print("Операция отменена")
                return

        # Заполняем таблицу
        print("\nЗаполняем таблицу user_order_address...")
        fill_user_order_address_table(conn)

        # Проверяем результат
        print("\nПроверяем результат...")
        stats_after = check_table_data(conn)
        print_statistics(stats_after)

        # Выводим несколько примеров созданных связей
        cur = conn.cursor()
        cur.execute("""
            SELECT uoa.id, uoa.user_id, u.first_name, u.last_name, 
                   uoa.order_id, uoa.address_id, uoa.created_at
            FROM user_order_address uoa
            JOIN users u ON uoa.user_id = u.id
            ORDER BY uoa.id
            LIMIT 5
        """)

        examples = cur.fetchall()
        print(f"\n=== ПЕРВЫЕ {len(examples)} ПРИМЕРОВ СВЯЗЕЙ ===")
        for example in examples:
            print(
                f"ID: {example['id']}, Пользователь: {example['first_name']} {example['last_name']} ({example['user_id']}), "
                f"Заказ: {example['order_id']}, Адрес: {example['address_id']}, Создано: {example['created_at']}")

        print(f"\n✅ Таблица user_order_address успешно заполнена!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    # Для быстрого заполнения используйте:
    # quick_fill_user_order_address(setting.conn_str)

    # Для полного заполнения со статистикой:
    main()