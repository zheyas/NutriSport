import sqlite3
import setting

def init_products_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            price       REAL NOT NULL CHECK (price >= 0),
            stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            weight      REAL NOT NULL DEFAULT 0 CHECK (weight >= 0), 
            image       TEXT,
            category    TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
    conn.commit()

def upgrade_products_add_category(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(products)")
    cols = {r["name"] for r in cur.fetchall()}
    if "category" not in cols:
        cur.execute("ALTER TABLE products ADD COLUMN category TEXT")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        conn.commit()

def upgrade_products_add_weight(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(products)")
    cols = {r["name"] for r in cur.fetchall()}
    if "weight" not in cols:
        cur.execute("ALTER TABLE products ADD COLUMN weight REAL NOT NULL DEFAULT 0")
        conn.commit()

init_products_table()