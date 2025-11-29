CREATE TABLE app_migrations (
            id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
CREATE TABLE products (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            price       REAL NOT NULL CHECK (price >= 0),
            stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            image       TEXT,                      -- URL/путь к изображению
            category    TEXT                       -- Текстовая категория
        , weight REAL NOT NULL DEFAULT 0);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_category ON products(category);
CREATE TABLE user_credentials (
        user_id TEXT PRIMARY KEY,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
CREATE TABLE IF NOT EXISTS "users" (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        middle_name TEXT,
        birthdate TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        vip INTEGER NOT NULL DEFAULT 0,
        photo TEXT
    );
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
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_uo_user_id ON user_order_address(user_id);
CREATE INDEX idx_uo_order_id ON user_order_address(order_id);
CREATE INDEX idx_uo_address_id ON user_order_address(address_id);
CREATE TABLE IF NOT EXISTS "orders" (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                order_date TEXT NOT NULL,
                total_price REAL NOT NULL CHECK(total_price >= 0),
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
            );
CREATE INDEX idx_orders_new_product_id ON "orders"(product_id);
CREATE INDEX idx_orders_new_date ON "orders"(order_date);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_credentials_login ON user_credentials(login);
CREATE TABLE user_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL,
        last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
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
            );
CREATE TABLE IF NOT EXISTS "addresses" (
                    id              TEXT PRIMARY KEY,
                    country         TEXT NOT NULL,
                    city_type       TEXT NOT NULL,
                    city            TEXT NOT NULL,
                    street_type     TEXT NOT NULL,
                    street          TEXT NOT NULL,
                    house_number    TEXT NOT NULL,
                    apartment       TEXT
                );
