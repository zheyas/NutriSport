# create_db_fresh.py
import sqlite3
import random
from datetime import datetime, timedelta
import bcrypt
import setting


# ---------- Функции для хеширования паролей (аналогично users.py) ----------
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# ---------- Создание всех таблиц ----------
def create_all_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # 1. Таблица users
    cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            birthdate TEXT,
            phone TEXT,
            email TEXT,
            vip INTEGER DEFAULT 0,
            photo TEXT,
            login TEXT
        )
    """)

    # 2. Таблица user_credentials (учетные данные)
    cursor.execute("""
        CREATE TABLE user_credentials (
            user_id TEXT PRIMARY KEY,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX idx_credentials_login ON user_credentials(login)")

    # 3. Таблица products
    cursor.execute("""
        CREATE TABLE products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL CHECK (price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            weight REAL NOT NULL DEFAULT 0 CHECK (weight >= 0),
            image TEXT,
            category TEXT
        )
    """)
    cursor.execute("CREATE INDEX idx_products_name ON products(name)")
    cursor.execute("CREATE INDEX idx_products_category ON products(category)")

    # 4. Таблица addresses
    cursor.execute("""
        CREATE TABLE addresses (
            id TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            city_type TEXT NOT NULL,
            city TEXT NOT NULL,
            street_type TEXT NOT NULL,
            street TEXT NOT NULL,
            house_number TEXT NOT NULL,
            apartment TEXT
        )
    """)

    # 5. Таблица orders
    cursor.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            order_date TEXT NOT NULL,
            total_price REAL NOT NULL CHECK(total_price >= 0),
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
        )
    """)
    cursor.execute("CREATE INDEX idx_orders_product_id ON orders(product_id)")
    cursor.execute("CREATE INDEX idx_orders_date ON orders(order_date)")

    # 6. Таблица user_sessions
    cursor.execute("""
        CREATE TABLE user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX idx_sessions_user_id ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX idx_sessions_expires ON user_sessions(expires_at)")

    # 7. Таблица user_order_address (связь пользователь-заказ-адрес)
    cursor.execute("""
        CREATE TABLE user_order_address (
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
    cursor.execute("CREATE INDEX idx_uo_user_id ON user_order_address(user_id)")
    cursor.execute("CREATE INDEX idx_uo_order_id ON user_order_address(order_id)")
    cursor.execute("CREATE INDEX idx_uo_address_id ON user_order_address(address_id)")

    # 8. Таблица cart
    cursor.execute("""
        CREATE TABLE cart (
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
    print("✅ Все таблицы созданы.")


# ---------- Вспомогательные функции для генерации ID ----------
def get_next_user_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(substr(id,3) AS INTEGER)) FROM users")
    maxnum = cur.fetchone()[0] or 0
    return f"us{maxnum + 1}"


def get_next_product_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(substr(id,3) AS INTEGER)) FROM products")
    maxnum = cur.fetchone()[0] or 0
    return f"PR{maxnum + 1}"


def get_next_address_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(substr(id,4) AS INTEGER)) FROM addresses")
    maxnum = cur.fetchone()[0] or 0
    return f"ADR{maxnum + 1:03d}"


def get_next_order_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(substr(id,4) AS INTEGER)) FROM orders")
    maxnum = cur.fetchone()[0] or 0
    return f"ORD{maxnum + 1:03d}"


# ---------- Заполнение тестовыми данными ----------
def populate_test_data(conn):
    cursor = conn.cursor()

    # ----- 1. Администратор -----
    admin_id = get_next_user_id(conn)
    cursor.execute("""
        INSERT INTO users (id, first_name, last_name, email, phone, birthdate, vip, login)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (admin_id, 'Admin', 'Adminov', 'admin@example.com', '+70000000000', '1990-01-01', 1, 'admin'))
    admin_hash = hash_password('admin')
    cursor.execute("""
        INSERT INTO user_credentials (user_id, login, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, (admin_id, 'admin', admin_hash, 'admin'))
    print("✅ Администратор создан: admin / admin")

    # ----- 2. Обычные пользователи (20) -----
    first_names = ['Иван', 'Петр', 'Сергей', 'Анна', 'Мария', 'Елена', 'Дмитрий', 'Ольга', 'Алексей', 'Наталья']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнова', 'Кузнецов', 'Попов', 'Васильева']
    user_ids = [admin_id]

    for i in range(20):
        login = f"user_{i + 1}"
        first = random.choice(first_names)
        last = random.choice(last_names)
        user_id = get_next_user_id(conn)
        cursor.execute("""
            INSERT INTO users (id, first_name, last_name, email, phone, birthdate, vip, login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, first, last, f"{login}@example.com", f"+7{random.randint(9000000000, 9999999999)}",
              f"{random.randint(1970, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
              random.choice([0, 1]), login))
        pwd_hash = hash_password(f"pass_{i + 1}")
        cursor.execute("""
            INSERT INTO user_credentials (user_id, login, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (user_id, login, pwd_hash, 'user'))
        user_ids.append(user_id)
        print(f"✅ Пользователь {login} (пароль: pass_{i + 1})")

    # ----- 3. Товары (30) -----
    categories = ["ПРОТЕИНЫ", "ГЕЙНЕРЫ", "АМИНОКИСЛОТЫ", "ВИТАМИНЫ", "СНЕКИ", "ОДЕЖДА"]
    product_names = {
        "ПРОТЕИНЫ": ["Whey Gold Standard", "Casein Pro", "Soy Isolate", "Vegan Blend", "Hydrolyzed Whey"],
        "ГЕЙНЕРЫ": ["Mass Gainer 3000", "Carbo Load", "Super Mass", "Weight Gainer Pro"],
        "АМИНОКИСЛОТЫ": ["BCAA 2:1:1", "Glutamine", "Arginine", "EAA Complex", "Beta-Alanine"],
        "ВИТАМИНЫ": ["Multivitamin Sport", "Vitamin D3", "Omega-3", "Zinc+Magnesium"],
        "СНЕКИ": ["Protein Bar", "Protein Cookie", "Protein Chips", "Energy Gel"],
        "ОДЕЖДА": ["T-Shirt", "Hoodie", "Cap", "Gym Bag"]
    }
    product_ids = []
    for i in range(30):
        cat = random.choice(categories)
        name = random.choice(product_names[cat]) + f" {i + 1}"
        price = round(random.uniform(500, 15000), 2)
        stock = random.randint(0, 200)
        weight = round(random.uniform(250, 3000), 0)
        desc = f"Отличный {cat.lower()} для спорта. Вес: {weight} г."
        image = f"/static/img/product_{i + 1}.jpg" if random.random() > 0.3 else None
        prod_id = get_next_product_id(conn)
        cursor.execute("""
            INSERT INTO products (id, name, description, price, stock, weight, image, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (prod_id, name, desc, price, stock, weight, image, cat))
        product_ids.append(prod_id)
    print(f"✅ Создано {len(product_ids)} товаров")

    # ----- 4. Адреса (по 1-2 на пользователя) -----
    countries = ['Россия', 'Беларусь', 'Казахстан']
    cities = ['Москва', 'СПб', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород']
    streets = ['Ленина', 'Пушкина', 'Советская', 'Молодежная', 'Гагарина', 'Мира']
    address_ids = []
    for uid in user_ids:
        for _ in range(random.randint(1, 2)):
            addr_id = get_next_address_id(conn)
            cursor.execute("""
                INSERT INTO addresses (id, country, city_type, city, street_type, street, house_number, apartment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (addr_id, random.choice(countries), 'г', random.choice(cities), 'ул', random.choice(streets),
                  str(random.randint(1, 120)), str(random.randint(1, 200)) if random.random() > 0.3 else None))
            address_ids.append(addr_id)
    print(f"✅ Создано {len(address_ids)} адресов")

    # ----- 5. Заказы и связи (50) -----
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()
    orders_created = 0
    for _ in range(50):
        user = random.choice(user_ids)
        product = random.choice(product_ids)
        quantity = random.randint(1, 5)
        # Получаем цену товара
        cursor.execute("SELECT price FROM products WHERE id = ?", (product,))
        price = cursor.fetchone()[0]
        total = price * quantity
        order_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        order_id = get_next_order_id(conn)
        cursor.execute("""
            INSERT INTO orders (id, product_id, quantity, order_date, total_price, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, product, quantity, order_date.isoformat(), total, random.choice(statuses)))
        # Связь с адресом (если есть адреса)
        if address_ids:
            address = random.choice(address_ids)
            cursor.execute("""
                INSERT INTO user_order_address (user_id, order_id, address_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (user, order_id, address, order_date.isoformat()))
            orders_created += 1
    print(f"✅ Создано {orders_created} заказов с привязкой к адресам")

    # ----- 6. Корзина (30 элементов) -----
    cart_items = 0
    for _ in range(30):
        user = random.choice(user_ids)
        product = random.choice(product_ids)
        # Проверяем уникальность пары
        cursor.execute("SELECT 1 FROM cart WHERE user_id=? AND product_id=?", (user, product))
        if not cursor.fetchone():
            quantity = random.randint(1, 3)
            cursor.execute("""
                INSERT INTO cart (user_id, product_id, quantity, created_at)
                VALUES (?, ?, ?, ?)
            """, (user, product, quantity, datetime.now().isoformat()))
            cart_items += 1
    print(f"✅ Добавлено {cart_items} элементов в корзину")

    conn.commit()


# ---------- Главная функция ----------
def main():
    # Удаляем старый файл, если есть (на всякий случай)
    import os
    if os.path.exists(setting.DB_PATH):
        os.remove(setting.DB_PATH)
        print(f"Удалён старый файл {setting.DB_PATH}")

    conn = sqlite3.connect(setting.DB_PATH)
    create_all_tables(conn)
    populate_test_data(conn)
    conn.close()
    print("\n🎉 База данных успешно создана и заполнена!")
    print("🔑 Администратор: admin / admin")
    print("🚀 Теперь можно запускать сервер: uvicorn main:app --reload")


if __name__ == "__main__":
    main()