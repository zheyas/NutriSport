import sqlite3
from typing import Optional, List
import setting
# --- Инициализация таблицы ----------------------------------

def init_addresses_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            id              TEXT PRIMARY KEY,
            country         TEXT NOT NULL,
            city_type       TEXT NOT NULL,      -- тип населенного пункта (например, город, село и т.п.)
            city            TEXT NOT NULL,      -- название населенного пункта
            street_type     TEXT NOT NULL,      -- тип улицы (улица, проспект и т.п.)
            street          TEXT NOT NULL,      -- название улицы
            house_number    TEXT NOT NULL,      -- номер дома
            apartment       TEXT,               -- номер квартиры (опционально)
            user_id         TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_addresses_user_id ON addresses(user_id)")
    conn.commit()

# --- Модель -------------------------------------------------

class Address:
    def __init__(
        self,
        id: str,
        country: str,
        city_type: str,
        city: str,
        street_type: str,
        street: str,
        house_number: str,
        apartment: Optional[str],
        user_id: str,
    ):
        self.id = id
        self.country = country
        self.city_type = city_type
        self.city = city
        self.street_type = street_type
        self.street = street
        self.house_number = house_number
        self.apartment = apartment
        self.user_id = user_id

    def __repr__(self):
        return (f"Address(id={self.id!r}, country={self.country!r}, city_type={self.city_type!r}, city={self.city!r}, "
                f"street_type={self.street_type!r}, street={self.street!r}, house_number={self.house_number!r}, "
                f"apartment={self.apartment!r}, user_id={self.user_id!r})")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Address":
        return cls(
            id=row["id"],
            country=row["country"],
            city_type=row["city_type"],
            city=row["city"],
            street_type=row["street_type"],
            street=row["street"],
            house_number=row["house_number"],
            apartment=row["apartment"],
            user_id=row["user_id"],
        )

    def to_tuple(self) -> tuple:
        return (
            self.id, self.country, self.city_type, self.city,
            self.street_type, self.street, self.house_number,
            self.apartment, self.user_id
        )

# --- CRUD ---------------------------------------------------

def create_address(conn: sqlite3.Connection, address: Address) -> None:
    sql = """
        INSERT INTO addresses (id, country, city_type, city, street_type, street, house_number, apartment, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, address.to_tuple())
    conn.commit()

def get_address(conn: sqlite3.Connection, address_id: str) -> Optional[Address]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM addresses WHERE id = ?", (address_id,))
    row = cur.fetchone()
    return Address.from_row(row) if row else None

def update_address(conn: sqlite3.Connection, address: Address) -> bool:
    sql = """
        UPDATE addresses SET
            country = ?, city_type = ?, city = ?, street_type = ?, street = ?,
            house_number = ?, apartment = ?, user_id = ?
        WHERE id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (
        address.country, address.city_type, address.city, address.street_type,
        address.street, address.house_number, address.apartment, address.user_id, address.id
    ))
    conn.commit()
    return cur.rowcount > 0

def delete_address(conn: sqlite3.Connection, address_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM addresses WHERE id = ?", (address_id,))
    conn.commit()
    return cur.rowcount > 0

def list_addresses(conn: sqlite3.Connection) -> List[Address]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM addresses ORDER BY id")
    rows = cur.fetchall()
    return [Address.from_row(row) for row in rows]

def addresses_by_user(conn: sqlite3.Connection, user_id: str) -> List[Address]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM addresses WHERE user_id = ? ORDER BY id", (user_id,))
    rows = cur.fetchall()
    return [Address.from_row(row) for row in rows]

# --- Генерация ID в формате ADR{n} --------------------------

def get_next_address_id(conn: sqlite3.Connection, pad: int = 3) -> str:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(SUBSTR(id, 4) AS INTEGER)) as maxnum FROM addresses")
    row = cur.fetchone()
    maxnum = row["maxnum"] or 0
    n = maxnum + 1
    return f"ADR{n:0{pad}d}"

def address_table_info(conn: sqlite3.Connection) -> List[str]:
    """Возвращает список названий колонок таблицы адресов"""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (addresses)")
    cols = [r["name"] for r in cur.fetchall()]
    return cols

if __name__ == "__main__":
    print(list_addresses(setting.conn_str))