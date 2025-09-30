import setting
import sqlite3
from typing import Optional, List

def init_products_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            price       REAL NOT NULL CHECK (price >= 0),
            stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
            weight      REAL NOT NULL DEFAULT 0 CHECK (weight >= 0),  -- граммы
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

# --- Модель -------------------------------------------------

class Product:
    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str],
        price: float,
        stock: int,
        image: Optional[str] = None,
        category: Optional[str] = None,
        weight: float = 0.0,              # граммы
    ):
        self.id = id
        self.name = name
        self.description = description
        self.price = float(price)
        self.stock = int(stock)
        self.image = image
        self.category = category
        self.weight = float(weight)

    def __repr__(self):
        return f"Product(id={self.id!r}, name={self.name!r}, price={self.price}, stock={self.stock}, weight={self.weight}, category={self.category!r})"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Product":
        keys = set(row.keys())
        cat = row["category"] if ("category" in keys) else None
        wt = row["weight"] if ("weight" in keys) else 0.0
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            stock=row["stock"],
            image=row["image"],
            category=cat,
            weight=wt,
        )

    def to_tuple(self) -> tuple:
        # порядок должен соответствовать INSERT
        return (self.id, self.name, self.description, self.price, self.stock, self.weight, self.image, self.category)

# --- CRUD ---------------------------------------------------

def create_product(conn: sqlite3.Connection, product: Product) -> None:
    sql = """
        INSERT INTO products (id, name, description, price, stock, weight, image, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, product.to_tuple())
    conn.commit()

def get_product(conn: sqlite3.Connection, product_id: str) -> Optional[Product]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    return Product.from_row(row) if row else None


def update_product(conn: sqlite3.Connection, product: Product) -> bool:
    sql = """
        UPDATE products SET
            name = ?, description = ?, price = ?, stock = ?, weight = ?, image = ?, category = ?
        WHERE id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (product.name, product.description, product.price, product.stock, product.weight, product.image, product.category, product.id))
    conn.commit()
    return cur.rowcount > 0

def delete_product(conn: sqlite3.Connection, product_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    return cur.rowcount > 0

def list_products(conn: sqlite3.Connection) -> List[Product]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id")
    rows = cur.fetchall()
    return [Product.from_row(row) for row in rows]

def search_products_by_name(conn: sqlite3.Connection, q: str) -> List[Product]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE name LIKE ? ORDER BY name", (f"%{q}%",))
    return [Product.from_row(r) for r in cur.fetchall()]

def search_products_by_category(conn: sqlite3.Connection, q: str) -> List[Product]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE category LIKE ? ORDER BY name", (f"%{q}%",))
    return [Product.from_row(r) for r in cur.fetchall()]

def products_table_info(conn: sqlite3.Connection) -> List[str]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (products)")
    cols = [r["name"] for r in cur.fetchall()]
    return cols

# --- Генерация ID в формате PR{n} ---------------------------

def get_next_product_id(conn: sqlite3.Connection, pad: int = 0) -> str:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(substr(id, 3) AS INTEGER)) AS maxnum FROM products")
    row = cur.fetchone()
    maxnum = row["maxnum"] or 0
    n = maxnum + 1
    if pad > 0:
        return f"PR{n:0{pad}d}"
    return f"PR{n}"

if __name__ == "__main__":
    print(list_products(setting.conn_str))