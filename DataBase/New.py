# generate_test_carts_fixed.py
import sqlite3
import random
from datetime import datetime, timedelta
from setting import DB_PATH


def check_users_structure():
    """Проверяет структуру таблицы users"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        print("🔍 Проверка структуры таблицы users...")

        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()

        print("📋 Структура таблицы users:")
        for col in columns:
            print(f"   {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")

        # Получаем пример пользователя
        cursor.execute("SELECT * FROM users LIMIT 1")
        sample_user = cursor.fetchone()

        if sample_user:
            print("\n📝 Пример пользователя:")
            for key in sample_user.keys():
                print(f"   {key}: {sample_user[key]}")

        return True

    except Exception as e:
        print(f"❌ Ошибка при проверке структуры: {e}")
        return False
    finally:
        conn.close()


def generate_test_carts():
    """Автоматически генерирует тестовые корзины"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        print("\n🛒 Генерация тестовых корзины...")

        # Получаем всех пользователей (просто их ID)
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()

        # Получаем все товары
        cursor.execute("SELECT id, name, stock, price FROM products WHERE stock > 0")
        products = cursor.fetchall()

        if not users:
            print("❌ Нет пользователей в базе данных")
            return False
        if not products:
            print("❌ Нет товаров в базе данных")
            return False

        print(f"👤 Найдено пользователей: {len(users)}")
        print(f"📦 Найдено товаров: {len(products)}")

        # Показываем первых 5 пользователей для отладки
        print("\n👥 Первые 5 пользователей:")
        for i, user in enumerate(users[:5]):
            print(f"   {i + 1}. {user['id']}")

        # Показываем первые 5 товаров для отладки
        print("\n📦 Первые 5 товаров:")
        for i, product in enumerate(products[:5]):
            print(
                f"   {i + 1}. {product['name']} (ID: {product['id']}, Цена: {product['price']} ₽, В наличии: {product['stock']} шт)")

        # Очищаем существующие корзины
        cursor.execute("DELETE FROM cart")
        print("\n🧹 Очищены существующие корзины")

        # Генерируем случайные корзины
        cart_count = min(20, len(users) * 2)  # Максимум 20 корзин
        created_carts = 0

        print(f"\n🎲 Генерируем {cart_count} корзин...")

        for i in range(cart_count):
            user = random.choice(users)
            product = random.choice(products)

            # Случайное количество (от 1 до 5, но не больше чем есть в наличии)
            max_quantity = min(5, product['stock'])
            quantity = random.randint(1, max_quantity)

            try:
                cursor.execute('''
                    INSERT INTO cart (user_id, product_id, quantity)
                    VALUES (?, ?, ?)
                ''', (user['id'], product['id'], quantity))

                created_carts += 1
                print(f"✅ Корзина {created_carts}: {user['id']} -> {product['name']} x{quantity}")

            except sqlite3.IntegrityError as e:
                # Если такая комбинация уже есть, пробуем другую
                continue
            except Exception as e:
                print(f"❌ Ошибка при создании корзины: {e}")
                continue

        conn.commit()
        print(f"\n🎉 Успешно создано корзин: {created_carts}")

        # Показываем статистику
        cursor.execute('''
            SELECT 
                COUNT(*) as total_carts,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(quantity) as total_items,
                SUM(p.price * c.quantity) as total_value
            FROM cart c
            JOIN products p ON c.product_id = p.id
        ''')

        stats = cursor.fetchone()
        print(f"\n📊 Статистика:")
        print(f"   Всего корзин: {stats['total_carts']}")
        print(f"   Уникальных пользователей: {stats['unique_users']}")
        print(f"   Всего товаров в корзинах: {stats['total_items']} шт")
        print(f"   Общая стоимость: {stats['total_value']:.2f} ₽")

        # Показываем детали по пользователям
        cursor.execute('''
            SELECT 
                c.user_id,
                COUNT(c.id) as cart_count,
                SUM(c.quantity) as total_items,
                SUM(p.price * c.quantity) as total_value
            FROM cart c
            JOIN products p ON c.product_id = p.id
            GROUP BY c.user_id
            ORDER BY total_value DESC
        ''')

        print(f"\n🏆 Топ пользователей по корзинам:")
        user_stats = cursor.fetchall()
        for row in user_stats:
            print(
                f"   {row['user_id']}: {row['cart_count']} корзин, {row['total_items']} товаров, {row['total_value']:.2f} ₽")

        # Показываем популярные товары
        cursor.execute('''
            SELECT 
                p.name,
                SUM(c.quantity) as total_quantity,
                COUNT(DISTINCT c.user_id) as unique_users
            FROM cart c
            JOIN products p ON c.product_id = p.id
            GROUP BY p.id
            ORDER BY total_quantity DESC
        ''')

        print(f"\n🔥 Популярные товары:")
        product_stats = cursor.fetchall()
        for row in product_stats:
            print(f"   {row['name']}: {row['total_quantity']} шт в {row['unique_users']} корзинах")

        return True

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        conn.close()


def quick_fix():
    """Быстрое исправление через SQL"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("⚡ Быстрое исправление через SQL...")

        # Удаляем старую таблицу если есть
        cursor.execute("DROP TABLE IF EXISTS cart")

        # Создаем новую таблицу
        cursor.execute('''
            CREATE TABLE cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                UNIQUE(user_id, product_id)
            )
        ''')

        conn.commit()
        print("✅ Таблица cart создана заново")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 Запуск генератора тестовых корзин...")

    # Проверяем структуру users
    check_users_structure()

    print("\n" + "=" * 50)

    # Сначала быстрый фикс
    if quick_fix():
        print("\n" + "=" * 50)
        # Затем генерация данных
        generate_test_carts()
    else:
        print("❌ Не удалось исправить структуру таблицы")