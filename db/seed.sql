-- Начальные данные NutriSport (сгенерировано из SportPit.db).
-- Применяется скриптом seed_db.py, только если база пустая.

CREATE TABLE IF NOT EXISTS users (
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
        );
CREATE TABLE IF NOT EXISTS user_credentials (
            user_id TEXT PRIMARY KEY,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL CHECK (price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            weight REAL NOT NULL DEFAULT 0 CHECK (weight >= 0),
            image TEXT,
            category TEXT
        );
CREATE TABLE IF NOT EXISTS addresses (
            id TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            city_type TEXT NOT NULL,
            city TEXT NOT NULL,
            street_type TEXT NOT NULL,
            street TEXT NOT NULL,
            house_number TEXT NOT NULL,
            apartment TEXT
        );
CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            order_date TEXT NOT NULL,
            total_price REAL NOT NULL CHECK(total_price >= 0),
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
        );
CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
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
        );
CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(user_id, product_id)
        );
CREATE INDEX IF NOT EXISTS idx_credentials_login ON user_credentials(login);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_uo_user_id ON user_order_address(user_id);
CREATE INDEX IF NOT EXISTS idx_uo_order_id ON user_order_address(order_id);
CREATE INDEX IF NOT EXISTS idx_uo_address_id ON user_order_address(address_id);

-- users: 21 rows
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us1', 'Admin', 'Adminov', '', '1990-01-01', '+70000000000', 'zhenyayasakov@yandex.ru', 1, NULL, 'admin');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us2', 'Ольга', 'Иванов', NULL, '1971-01-09', '+79729667534', 'user_1@example.com', 0, NULL, 'user_1');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us3', 'Наталья', 'Попов', NULL, '1986-03-13', '+79826736605', 'user_2@example.com', 1, NULL, 'user_2');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us4', 'Наталья', 'Петров', NULL, '2005-08-21', '+79143108752', 'user_3@example.com', 0, NULL, 'user_3');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us5', 'Анна', 'Кузнецов', NULL, '1985-06-24', '+79201082125', 'user_4@example.com', 1, NULL, 'user_4');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us6', 'Анна', 'Петров', NULL, '1971-12-23', '+79028625970', 'user_5@example.com', 1, NULL, 'user_5');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us7', 'Дмитрий', 'Петров', NULL, '1989-04-07', '+79205691713', 'user_6@example.com', 1, NULL, 'user_6');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us8', 'Алексей', 'Сидоров', NULL, '1978-03-22', '+79202276161', 'user_7@example.com', 0, NULL, 'user_7');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us9', 'Петр', 'Иванова', '', '1978-11-18', '+79954703107', 'user_8@example.com', 1, NULL, 'user_8');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us10', 'Анна', 'Иванов', '', '2000-02-27', '+79337182421', 'user_90@example.com', 0, NULL, 'user_9');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us11', 'Альга', 'Васильева', '', '1979-01-25', '+79485043815', 'user_10@example.com', 0, NULL, 'user_10');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us12', 'Иван', 'Иванов', NULL, '1974-08-28', '+79231043372', 'user_11@example.com', 0, NULL, 'user_11');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us13', 'Алексей', 'Кузнецов', NULL, '1978-12-19', '+79457952863', 'user_12@example.com', 0, NULL, 'user_12');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us14', 'Елена', 'Смирнова', NULL, '1999-06-13', '+79024232363', 'user_13@example.com', 0, NULL, 'user_13');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us15', 'Мария', 'Попов', NULL, '1971-12-25', '+79667563965', 'user_14@example.com', 1, NULL, 'user_14');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us16', 'Ольга', 'Петров', NULL, '1997-04-02', '+79634016372', 'user_15@example.com', 0, NULL, 'user_15');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us17', 'Мария', 'Васильева', NULL, '1985-01-28', '+79616787272', 'user_16@example.com', 0, NULL, 'user_16');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us18', 'Алексей', 'Васильева', NULL, '1976-02-19', '+79509100959', 'user_17@example.com', 1, NULL, 'user_17');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us19', 'Дмитрий', 'Кузнецов', NULL, '1998-06-25', '+79952137744', 'user_18@example.com', 0, NULL, 'user_18');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us20', 'Сергей', 'Кузнецов', NULL, '1988-07-16', '+79610814808', 'user_19@example.com', 1, NULL, 'user_19');
INSERT OR IGNORE INTO "users" ("id", "first_name", "last_name", "middle_name", "birthdate", "phone", "email", "vip", "photo", "login") VALUES ('us21', 'Алексей', 'Васильева', NULL, '1970-05-12', '+79109795808', 'user_20@example.com', 0, NULL, 'user_20');

-- user_credentials: 21 rows
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us1', 'admin', '$2b$12$V8K.2PMx4AYMG/8DioxW.eKQ/fkaIGak6kFh..48vuAMAvCrWQoqC', 'admin', '2026-04-17 09:05:10', '2026-04-17 09:05:10');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us2', 'user_1', '$2b$12$EP2ew2HJxIyTrz709YWJDebVmYz0Q34VwEdkNT5ls1J/yLpwSAwo.', 'user', '2026-04-17 09:05:11', '2026-04-17 09:05:11');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us3', 'user_2', '$2b$12$s8T8jUNShZ5DtjyhocFt1OhFRaAe.OCR1n2ccBC8trDlaxj8fARRW', 'user', '2026-04-17 09:05:11', '2026-04-17 09:05:11');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us4', 'user_3', '$2b$12$AnYuMtgTFFSm/M0yYYQKy.gmV8wIy6K0gcRVbgf2hxfBq/6.dshcm', 'user', '2026-04-17 09:05:11', '2026-04-17 09:05:11');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us5', 'user_4', '$2b$12$.axigILHAseQZRXi8d3vlulNPHLUShcQA9khi.sJM0l6uf2Z00MRi', 'user', '2026-04-17 09:05:11', '2026-04-17 09:05:11');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us6', 'user_5', '$2b$12$WQZPmfXrJhn0Vn6Z63MG2OWwFKMJ2J5Qr.hRXrAkoMoZvID/rcAw6', 'user', '2026-04-17 09:05:12', '2026-04-17 09:05:12');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us7', 'user_6', '$2b$12$ztzjDSC8ob4SNwhDqlf/pu3XVvXk.HFLh7I44RlUbM7kJlUET1gym', 'user', '2026-04-17 09:05:12', '2026-04-17 09:05:12');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us8', 'user_7', '$2b$12$LN6wL/.zhtqmRcp7GR62IOmk3DXYek11woiENu1nqiVl7yQdCS30u', 'user', '2026-04-17 09:05:12', '2026-04-17 09:05:12');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us9', 'user_8', '$2b$12$NYg7yqwRKG4W7bRZ4dWAzuP3ZRZxFkKLAXSWxmkix4Q5j3aHs1xPW', 'user', '2026-04-17 09:05:12', '2026-04-17 09:05:12');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us10', 'user_9', '$2b$12$CeXESTDSrI9vNxQxAlfsTu3.ALZocIpivBLYCYYmOp2amcL7kt6Ry', 'user', '2026-04-17 09:05:13', '2026-04-17 09:05:13');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us11', 'user_10', '$2b$12$24MMJmzAgBcRbuuTPa4aYu11VMLzZdQgLDd229t8dvu6ETQyt5EGC', 'user', '2026-04-17 09:05:13', '2026-04-17 09:05:13');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us12', 'user_11', '$2b$12$4JBlT28dy0Q0iSJA.6GAYuS1yovcdQ5hBrAd5tcSCBMPz7RhjCP1G', 'user', '2026-04-17 09:05:13', '2026-04-17 09:05:13');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us13', 'user_12', '$2b$12$DzozgpbAszTaOJGPktm3uOd.onZNjwkaBpqc/cGjnnmTWpBAFv4dW', 'user', '2026-04-17 09:05:13', '2026-04-17 09:05:13');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us14', 'user_13', '$2b$12$8HX7Rz5So2LbJlWIQi3/teTkw4bkzEtHZg9whk69pWK.oSbHyZj9y', 'user', '2026-04-17 09:05:14', '2026-04-17 09:05:14');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us15', 'user_14', '$2b$12$PfuJglr/ZJvGntHWJ.LUtOgvTCDDJN5phlWyyHrTgNMchKP.H36te', 'user', '2026-04-17 09:05:14', '2026-04-17 09:05:14');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us16', 'user_15', '$2b$12$ynyNDgvzQSuKVMp53HOfjuLjDhxPniTzzt/zFdzNNreyEdR4sCmWi', 'user', '2026-04-17 09:05:14', '2026-04-17 09:05:14');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us17', 'user_16', '$2b$12$dww8qJuOmEXlhYufg.hLHOii22Whll8/uWChSPMEq8ng9CAVkz5pO', 'user', '2026-04-17 09:05:14', '2026-04-17 09:05:14');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us18', 'user_17', '$2b$12$Zqf2IO/L1xIy8FV6t7TRteKozJehjqPjBqJgSRuDV2KOKIR8AZ.7e', 'user', '2026-04-17 09:05:15', '2026-04-17 09:05:15');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us19', 'user_18', '$2b$12$6N.DMIgFrcSGH3Z6g/t5eeaXQnJzK.QCWz/Y.QJ2S5V6TMmwhjEzm', 'user', '2026-04-17 09:05:15', '2026-04-17 09:05:15');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us20', 'user_19', '$2b$12$sAS5slDeP03MVJgyhlCKYe12CHA790gQ8ngoM8.zuErn20vJLhPra', 'user', '2026-04-17 09:05:15', '2026-04-17 09:05:15');
INSERT OR IGNORE INTO "user_credentials" ("user_id", "login", "password_hash", "role", "created_at", "updated_at") VALUES ('us21', 'user_20', '$2b$12$HgSzdezcboPXnYSOy417dujR7jGyL0cX2zduubvCMltD5W0g4ioOy', 'user', '2026-04-17 09:05:15', '2026-04-17 09:05:15');

-- products: 30 rows
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR1', 'Soy Isolate 1', 'Отличный протеины для спорта. Вес: 1352.0 г.', 13223.84, 165, 1352.0, NULL, 'ПРОТЕИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR2', 'Weight Gainer Pro 2', 'Отличный гейнеры для спорта. Вес: 1184.0 г.', 9314.88, 125, 1184.0, '/static/img/product_2.jpg', 'ГЕЙНЕРЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR3', 'BCAA 2:1:1 3', 'Отличный аминокислоты для спорта. Вес: 908.0 г.', 816.86, 13, 908.0, NULL, 'АМИНОКИСЛОТЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR4', 'Vitamin D3 4', 'Отличный витамины для спорта. Вес: 2693.0 г.', 2896.87, 121, 2693.0, '/static/img/product_4.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR5', 'Gym Bag 5', 'Отличный одежда для спорта. Вес: 2575.0 г.', 2119.15, 196, 2575.0, '/static/img/product_5.jpg', 'ОДЕЖДА');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR6', 'Whey Gold Standard 6', 'Отличный протеины для спорта. Вес: 1615.0 г.', 5478.16, 1, 1615.0, '/static/img/product_6.jpg', 'ПРОТЕИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR7', 'Weight Gainer Pro 7', 'Отличный гейнеры для спорта. Вес: 485.0 г.', 8772.89, 193, 485.0, '/static/img/product_7.jpg', 'ГЕЙНЕРЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR8', 'Super Mass 8', 'Отличный гейнеры для спорта. Вес: 1863.0 г.', 6251.98, 115, 1863.0, '/static/img/product_8.jpg', 'ГЕЙНЕРЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR9', 'Protein Bar 9', 'Отличный снеки для спорта. Вес: 1149.0 г.', 6340.55, 196, 1149.0, '/static/img/product_9.jpg', 'СНЕКИ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR10', 'Vegan Blend 10', 'Отличный протеины для спорта. Вес: 1849.0 г.', 12640.79, 63, 1849.0, '/static/img/product_10.jpg', 'ПРОТЕИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR11', 'Omega-3 11', 'Отличный витамины для спорта. Вес: 2143.0 г.', 1107.44, 59, 2143.0, '/static/img/product_11.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR12', 'Vitamin D3 12', 'Отличный витамины для спорта. Вес: 312.0 г.', 11365.23, 62, 312.0, NULL, 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR13', 'Omega-3 13', 'Отличный витамины для спорта. Вес: 1318.0 г.', 14195.3, 46, 1318.0, '/static/img/product_13.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR14', 'T-Shirt 14', 'Отличный одежда для спорта. Вес: 1142.0 г.', 5806.0, 100, 1142.0, '/static/img/product_14.jpg', 'ОДЕЖДА');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR15', 'Vitamin D3 15', 'Отличный витамины для спорта. Вес: 1906.0 г.', 14990.23, 120, 1906.0, '/static/img/product_15.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR16', 'Mass Gainer 3000 16', 'Отличный гейнеры для спорта. Вес: 2239.0 г.', 12528.41, 66, 2239.0, '/static/img/product_16.jpg', 'ГЕЙНЕРЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR17', 'Zinc+Magnesium 17', 'Отличный витамины для спорта. Вес: 810.0 г.', 3673.02, 54, 810.0, '/static/img/product_17.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR18', 'Protein Chips 18', 'Отличный снеки для спорта. Вес: 1610.0 г.', 7469.99, 144, 1610.0, '/static/img/product_18.jpg', 'СНЕКИ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR19', 'Weight Gainer Pro 19', 'Отличный гейнеры для спорта. Вес: 2538.0 г.', 7634.92, 135, 2538.0, NULL, 'ГЕЙНЕРЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR20', 'Hydrolyzed Whey 20', 'Отличный протеины для спорта. Вес: 1774.0 г.', 13850.1, 81, 1774.0, '/static/img/product_20.jpg', 'ПРОТЕИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR21', 'Weight Gainer Pro 21', 'Отличный гейнеры для спорта. Вес: 1796.0 г.', 13422.16, 162, 1796.0, NULL, 'ГЕЙНЕРЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR22', 'Vegan Blend 22', 'Отличный протеины для спорта. Вес: 733.0 г.', 656.28, 116, 733.0, '/static/img/product_22.jpg', 'ПРОТЕИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR23', 'Cap 23', 'Отличный одежда для спорта. Вес: 2873.0 г.', 9019.4, 1, 2873.0, NULL, 'ОДЕЖДА');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR24', 'Hoodie 24', 'Отличный одежда для спорта. Вес: 504.0 г.', 9826.62, 78, 504.0, '/static/img/product_24.jpg', 'ОДЕЖДА');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR25', 'Omega-3 25', 'Отличный витамины для спорта. Вес: 2494.0 г.', 11410.52, 54, 2494.0, '/static/img/product_25.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR26', 'EAA Complex 26', 'Отличный аминокислоты для спорта. Вес: 456.0 г.', 6755.17, 135, 456.0, NULL, 'АМИНОКИСЛОТЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR27', 'Cap 27', 'Отличный одежда для спорта. Вес: 1634.0 г.', 13937.39, 75, 1634.0, '/static/img/product_27.jpg', 'ОДЕЖДА');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR28', 'Zinc+Magnesium 28', 'Отличный витамины для спорта. Вес: 2741.0 г.', 9176.05, 103, 2741.0, '/static/img/product_28.jpg', 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR29', 'Omega-3 29', 'Отличный витамины для спорта. Вес: 983.0 г.', 12893.53, 96, 983.0, NULL, 'ВИТАМИНЫ');
INSERT OR IGNORE INTO "products" ("id", "name", "description", "price", "stock", "weight", "image", "category") VALUES ('PR30', 'Glutamine 30', 'Отличный аминокислоты для спорта. Вес: 1743.0 г.', 9434.38, 98, 1743.0, '/static/img/product_30.jpg', 'АМИНОКИСЛОТЫ');

-- addresses: 31 rows
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR001', 'Россия', 'г', 'СПб', 'ул', 'Гагарина', '27', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR002', 'Россия', 'г', 'Казань', 'ул', 'Пушкина', '72', '55');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR003', 'Россия', 'г', 'Новосибирск', 'ул', 'Молодежная', '71', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR004', 'Россия', 'г', 'Нижний Новгород', 'ул', 'Пушкина', '26', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR005', 'Казахстан', 'г', 'СПб', 'ул', 'Гагарина', '30', '107');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR006', 'Казахстан', 'г', 'Казань', 'ул', 'Пушкина', '104', '29');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR007', 'Казахстан', 'г', 'СПб', 'ул', 'Советская', '51', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR008', 'Казахстан', 'г', 'Екатеринбург', 'ул', 'Гагарина', '99', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR009', 'Беларусь', 'г', 'Екатеринбург', 'ул', 'Молодежная', '9', '118');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR010', 'Россия', 'г', 'Новосибирск', 'ул', 'Гагарина', '111', '183');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR011', 'Россия', 'г', 'Новосибирск', 'ул', 'Мира', '26', '12');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR012', 'Казахстан', 'г', 'Нижний Новгород', 'ул', 'Молодежная', '81', '62');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR013', 'Казахстан', 'г', 'СПб', 'ул', 'Пушкина', '34', '24');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR014', 'Беларусь', 'г', 'Екатеринбург', 'ул', 'Пушкина', '101', '140');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR015', 'Беларусь', 'г', 'СПб', 'ул', 'Советская', '113', '167');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR016', 'Беларусь', 'г', 'Казань', 'ул', 'Гагарина', '100', '78');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR017', 'Казахстан', 'г', 'Новосибирск', 'ул', 'Ленина', '71', '85');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR018', 'Казахстан', 'г', 'СПб', 'ул', 'Мира', '111', '26');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR019', 'Казахстан', 'г', 'Нижний Новгород', 'ул', 'Советская', '9', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR020', 'Беларусь', 'г', 'Москва', 'ул', 'Молодежная', '20', '103');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR021', 'Казахстан', 'г', 'Новосибирск', 'ул', 'Ленина', '24', '190');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR022', 'Казахстан', 'г', 'Екатеринбург', 'ул', 'Молодежная', '108', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR023', 'Беларусь', 'г', 'Новосибирск', 'ул', 'Мира', '49', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR024', 'Казахстан', 'г', 'Новосибирск', 'ул', 'Мира', '84', '55');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR025', 'Казахстан', 'г', 'Казань', 'ул', 'Гагарина', '72', '62');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR026', 'Россия', 'г', 'Москва', 'ул', 'Пушкина', '88', '170');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR027', 'Россия', 'г', 'Новосибирск', 'ул', 'Молодежная', '104', NULL);
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR028', 'Россия', 'г', 'Москва', 'ул', 'Мира', '17', '160');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR029', 'Беларусь', 'г', 'Нижний Новгород', 'ул', 'Мира', '106', '132');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR030', 'Казахстан', 'г', 'Москва', 'ул', 'Молодежная', '79', '94');
INSERT OR IGNORE INTO "addresses" ("id", "country", "city_type", "city", "street_type", "street", "house_number", "apartment") VALUES ('ADR031', 'Беларусь', 'г', 'Казань', 'ул', 'Гагарина', '14', '74');

-- orders: 56 rows
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD001', 'PR14', 5, '2025-03-28T00:00:00', 29030.0, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD002', 'PR2', 3, '2026-01-01T00:00:00', 27944.64, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD003', 'PR6', 2, '2024-12-20T00:00:00', 10956.32, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD004', 'PR27', 4, '2025-10-24T00:00:00', 55749.56, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD005', 'PR3', 5, '2025-06-03T00:00:00', 4084.3, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD006', 'PR18', 1, '2025-09-09T00:00:00', 7469.99, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD007', 'PR25', 4, '2026-03-08T00:00:00', 45642.08, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD008', 'PR1', 1, '2024-02-11T00:00:00', 13223.84, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD009', 'PR7', 2, '2025-06-22T00:00:00', 17545.78, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD010', 'PR7', 1, '2025-01-19T00:00:00', 8772.89, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD011', 'PR20', 1, '2024-08-09T00:00:00', 13850.1, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD012', 'PR3', 5, '2024-03-01T00:00:00', 4084.3, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD013', 'PR20', 3, '2025-06-06T00:00:00', 41550.3, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD014', 'PR10', 3, '2025-07-23T00:00:00', 37922.37, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD015', 'PR11', 4, '2024-10-01T00:00:00', 4429.76, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD016', 'PR6', 2, '2025-03-08T00:00:00', 10956.32, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD017', 'PR4', 1, '2024-01-03T00:00:00', 2896.87, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD018', 'PR17', 2, '2024-01-08T00:00:00', 7346.04, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD019', 'PR30', 2, '2024-07-25T00:00:00', 18868.76, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD020', 'PR19', 1, '2024-11-12T00:00:00', 7634.92, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD021', 'PR12', 4, '2024-06-18T00:00:00', 45460.92, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD022', 'PR27', 2, '2025-02-22T00:00:00', 27874.78, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD023', 'PR17', 5, '2026-01-02T00:00:00', 18365.1, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD024', 'PR15', 1, '2024-04-27T00:00:00', 14990.23, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD025', 'PR17', 4, '2025-03-17T00:00:00', 14692.08, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD026', 'PR19', 4, '2025-05-04T00:00:00', 30539.68, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD027', 'PR4', 1, '2024-06-03T00:00:00', 2896.87, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD028', 'PR1', 5, '2026-03-22T00:00:00', 66119.2, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD029', 'PR2', 5, '2025-04-20T00:00:00', 46574.399999999994, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD030', 'PR27', 2, '2024-03-31T00:00:00', 27874.78, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD031', 'PR16', 4, '2024-03-18T00:00:00', 50113.64, 'pending');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD032', 'PR13', 5, '2024-04-24T00:00:00', 70976.5, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD033', 'PR29', 2, '2026-03-11T00:00:00', 25787.06, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD034', 'PR3', 5, '2024-03-22T00:00:00', 4084.3, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD035', 'PR10', 2, '2024-10-14T00:00:00', 25281.58, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD036', 'PR19', 4, '2025-08-20T00:00:00', 30539.68, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD037', 'PR5', 1, '2024-01-21T00:00:00', 2119.15, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD038', 'PR17', 1, '2025-01-11T00:00:00', 3673.02, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD039', 'PR7', 4, '2026-03-27T00:00:00', 35091.56, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD040', 'PR16', 2, '2025-02-27T00:00:00', 25056.82, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD041', 'PR27', 4, '2024-04-11T00:00:00', 55749.56, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD042', 'PR16', 5, '2024-03-02T00:00:00', 62642.05, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD043', 'PR1', 5, '2025-12-10T00:00:00', 66119.2, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD044', 'PR22', 4, '2026-03-29T00:00:00', 2625.12, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD045', 'PR18', 2, '2025-03-27T00:00:00', 14939.98, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD046', 'PR6', 1, '2024-11-14T00:00:00', 5478.16, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD047', 'PR22', 4, '2025-12-10T00:00:00', 2625.12, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD048', 'PR21', 4, '2024-05-03T00:00:00', 53688.64, 'shipped');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD049', 'PR30', 4, '2024-10-16T00:00:00', 37737.52, 'delivered');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD050', 'PR15', 4, '2025-10-25T00:00:00', 59960.92, 'cancelled');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD051', 'PR19', 1, '2026-06-01T18:15:58.789349', 7634.92, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD052', 'PR3', 1, '2026-06-01T18:15:58.790560', 816.86, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD053', 'PR16', 1, '2026-06-01T18:15:58.791517', 12528.41, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD054', 'PR4', 2, '2026-06-01T18:15:58.792558', 5793.74, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD055', 'PR22', 1, '2026-06-01T18:15:58.793575', 656.28, 'processing');
INSERT OR IGNORE INTO "orders" ("id", "product_id", "quantity", "order_date", "total_price", "status") VALUES ('ORD056', 'PR24', 3, '2026-06-01T18:15:58.794662', 29479.86, 'processing');

-- user_order_address: 56 rows
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (1, 'us1', 'ORD001', 'ADR017', '2025-03-28T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (2, 'us10', 'ORD002', 'ADR013', '2026-01-01T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (3, 'us1', 'ORD003', 'ADR021', '2024-12-20T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (4, 'us6', 'ORD004', 'ADR014', '2025-10-24T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (5, 'us12', 'ORD005', 'ADR008', '2025-06-03T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (6, 'us7', 'ORD006', 'ADR024', '2025-09-09T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (7, 'us5', 'ORD007', 'ADR025', '2026-03-08T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (8, 'us14', 'ORD008', 'ADR011', '2024-02-11T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (9, 'us2', 'ORD009', 'ADR022', '2025-06-22T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (10, 'us17', 'ORD010', 'ADR015', '2025-01-19T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (11, 'us12', 'ORD011', 'ADR014', '2024-08-09T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (12, 'us21', 'ORD012', 'ADR024', '2024-03-01T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (13, 'us20', 'ORD013', 'ADR017', '2025-06-06T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (14, 'us11', 'ORD014', 'ADR006', '2025-07-23T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (15, 'us18', 'ORD015', 'ADR022', '2024-10-01T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (16, 'us3', 'ORD016', 'ADR018', '2025-03-08T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (17, 'us21', 'ORD017', 'ADR023', '2024-01-03T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (18, 'us12', 'ORD018', 'ADR014', '2024-01-08T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (19, 'us11', 'ORD019', 'ADR016', '2024-07-25T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (20, 'us2', 'ORD020', 'ADR027', '2024-11-12T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (21, 'us8', 'ORD021', 'ADR022', '2024-06-18T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (22, 'us16', 'ORD022', 'ADR011', '2025-02-22T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (23, 'us4', 'ORD023', 'ADR015', '2026-01-02T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (24, 'us8', 'ORD024', 'ADR019', '2024-04-27T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (25, 'us13', 'ORD025', 'ADR011', '2025-03-17T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (26, 'us13', 'ORD026', 'ADR026', '2025-05-04T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (27, 'us13', 'ORD027', 'ADR026', '2024-06-03T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (28, 'us21', 'ORD028', 'ADR022', '2026-03-22T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (29, 'us6', 'ORD029', 'ADR007', '2025-04-20T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (30, 'us11', 'ORD030', 'ADR023', '2024-03-31T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (31, 'us16', 'ORD031', 'ADR001', '2024-03-18T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (32, 'us20', 'ORD032', 'ADR027', '2024-04-24T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (33, 'us3', 'ORD033', 'ADR026', '2026-03-11T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (34, 'us16', 'ORD034', 'ADR004', '2024-03-22T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (35, 'us21', 'ORD035', 'ADR003', '2024-10-14T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (36, 'us9', 'ORD036', 'ADR023', '2025-08-20T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (37, 'us8', 'ORD037', 'ADR031', '2024-01-21T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (38, 'us12', 'ORD038', 'ADR019', '2025-01-11T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (39, 'us10', 'ORD039', 'ADR007', '2026-03-27T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (40, 'us9', 'ORD040', 'ADR023', '2025-02-27T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (41, 'us10', 'ORD041', 'ADR024', '2024-04-11T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (42, 'us17', 'ORD042', 'ADR029', '2024-03-02T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (43, 'us10', 'ORD043', 'ADR002', '2025-12-10T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (44, 'us5', 'ORD044', 'ADR029', '2026-03-29T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (45, 'us19', 'ORD045', 'ADR020', '2025-03-27T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (46, 'us21', 'ORD046', 'ADR024', '2024-11-14T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (47, 'us18', 'ORD047', 'ADR025', '2025-12-10T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (48, 'us3', 'ORD048', 'ADR009', '2024-05-03T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (49, 'us5', 'ORD049', 'ADR026', '2024-10-16T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (50, 'us8', 'ORD050', 'ADR012', '2025-10-25T00:00:00');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (51, 'us1', 'ORD051', 'ADR017', '2026-06-01T18:15:58.790160');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (52, 'us1', 'ORD052', 'ADR017', '2026-06-01T18:15:58.791116');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (53, 'us1', 'ORD053', 'ADR017', '2026-06-01T18:15:58.792117');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (54, 'us1', 'ORD054', 'ADR017', '2026-06-01T18:15:58.793130');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (55, 'us1', 'ORD055', 'ADR017', '2026-06-01T18:15:58.794247');
INSERT OR IGNORE INTO "user_order_address" ("id", "user_id", "order_id", "address_id", "created_at") VALUES (56, 'us1', 'ORD056', 'ADR017', '2026-06-01T18:15:58.795257');

-- cart: 28 rows
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (1, 'us16', 'PR4', 2, '2026-04-17T14:05:15.762016');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (2, 'us3', 'PR15', 3, '2026-04-17T14:05:15.762072');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (3, 'us17', 'PR9', 3, '2026-04-17T14:05:15.762079');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (4, 'us17', 'PR11', 2, '2026-04-17T14:05:15.762083');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (5, 'us6', 'PR9', 3, '2026-04-17T14:05:15.762087');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (6, 'us9', 'PR7', 3, '2026-04-17T14:05:15.762091');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (7, 'us11', 'PR4', 3, '2026-04-17T14:05:15.762095');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (8, 'us19', 'PR19', 3, '2026-04-17T14:05:15.762099');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (9, 'us21', 'PR10', 3, '2026-04-17T14:05:15.762103');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (10, 'us9', 'PR28', 2, '2026-04-17T14:05:15.762107');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (11, 'us4', 'PR9', 2, '2026-04-17T14:05:15.762110');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (13, 'us15', 'PR25', 1, '2026-04-17T14:05:15.762118');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (14, 'us2', 'PR1', 3, '2026-04-17T14:05:15.762122');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (15, 'us17', 'PR2', 3, '2026-04-17T14:05:15.762126');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (16, 'us20', 'PR30', 1, '2026-04-17T14:05:15.762130');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (17, 'us19', 'PR29', 3, '2026-04-17T14:05:15.762133');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (18, 'us18', 'PR15', 3, '2026-04-17T14:05:15.762137');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (19, 'us14', 'PR26', 2, '2026-04-17T14:05:15.762141');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (21, 'us7', 'PR10', 1, '2026-04-17T14:05:15.762148');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (22, 'us20', 'PR8', 3, '2026-04-17T14:05:15.762152');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (23, 'us18', 'PR3', 2, '2026-04-17T14:05:15.762156');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (24, 'us6', 'PR7', 1, '2026-04-17T14:05:15.762160');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (25, 'us16', 'PR9', 2, '2026-04-17T14:05:15.762165');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (26, 'us14', 'PR27', 2, '2026-04-17T14:05:15.762169');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (28, 'us7', 'PR13', 2, '2026-04-17T14:05:15.762177');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (29, 'us5', 'PR21', 3, '2026-04-17T14:05:15.762180');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (34, 'us1', 'PR3', 1, '2026-06-01T18:40:43.418992');
INSERT OR IGNORE INTO "cart" ("id", "user_id", "product_id", "quantity", "created_at") VALUES (35, 'us1', 'PR23', 1, '2026-06-01T18:40:43.861900');
