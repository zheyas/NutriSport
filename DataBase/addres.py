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
            apartment       TEXT                -- номер квартиры (опционально)
        )
    """)
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
            apartment: Optional[str] = None
    ):
        self.id = id
        self.country = country
        self.city_type = city_type
        self.city = city
        self.street_type = street_type
        self.street = street
        self.house_number = house_number
        self.apartment = apartment

    def __repr__(self):
        return (f"Address(id={self.id!r}, country={self.country!r}, city_type={self.city_type!r}, city={self.city!r}, "
                f"street_type={self.street_type!r}, street={self.street!r}, house_number={self.house_number!r}, "
                f"apartment={self.apartment!r})")

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
            apartment=row["apartment"]
        )

    def to_tuple(self) -> tuple:
        return (
            self.id, self.country, self.city_type, self.city,
            self.street_type, self.street, self.house_number,
            self.apartment
        )


# --- CRUD ---------------------------------------------------

def create_address(conn: sqlite3.Connection, address: Address) -> None:
    sql = """
        INSERT INTO addresses (id, country, city_type, city, street_type, street, house_number, apartment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            house_number = ?, apartment = ?
        WHERE id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (
        address.country, address.city_type, address.city, address.street_type,
        address.street, address.house_number, address.apartment, address.id
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


def get_all_addresses(conn: sqlite3.Connection) -> List[Address]:
    """Получить все адреса (альтернативное название для совместимости)"""
    return list_addresses(conn)


def list_addresses_by_user(conn: sqlite3.Connection, user_id: str) -> List[Address]:
    """
    Получить все адреса пользователя через связи user_order_address
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT a.id, a.country, a.city_type, a.city, a.street_type, a.street, a.house_number, a.apartment
        FROM addresses a
        JOIN user_order_address uoa ON a.id = uoa.address_id
        WHERE uoa.user_id = ?
        ORDER BY a.id
    """, (user_id,))

    addresses = []
    for row in cursor.fetchall():
        addresses.append(Address(
            id=row[0],
            country=row[1],
            city_type=row[2],
            city=row[3],
            street_type=row[4],
            street=row[5],
            house_number=row[6],
            apartment=row[7],))
    return addresses

if __name__ == "__main__":
    # Выполняем миграцию базы данных
    print("Запуск миграции таблицы addresses...")

    with sqlite3.connect(setting.DB_PATH) as conn:
        try:
            cur = conn.cursor()

            # Создаем временную таблицу без user_id
            print("Создание временной таблицы...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS addresses_new (
                    id              TEXT PRIMARY KEY,
                    country         TEXT NOT NULL,
                    city_type       TEXT NOT NULL,
                    city            TEXT NOT NULL,
                    street_type     TEXT NOT NULL,
                    street          TEXT NOT NULL,
                    house_number    TEXT NOT NULL,
                    apartment       TEXT
                )
            """)

            # Проверяем, существует ли старая таблица с user_id
            cur.execute("PRAGMA table_info(addresses)")
            old_columns = [row[1] for row in cur.fetchall()]

            if 'user_id' in old_columns:
                print("Обнаружена старая структура таблицы. Выполняем миграцию данных...")

                # Копируем данные из старой таблицы (исключая user_id)
                cur.execute("""
                    INSERT INTO addresses_new (id, country, city_type, city, street_type, street, house_number, apartment)
                    SELECT id, country, city_type, city, street_type, street, house_number, apartment 
                    FROM addresses
                """)

                # Удаляем старую таблицу
                cur.execute("DROP TABLE addresses")

                # Переименовываем новую таблицу
                cur.execute("ALTER TABLE addresses_new RENAME TO addresses")

                print("Миграция данных завершена успешно!")
            else:
                print("Таблица уже имеет новую структуру. Миграция не требуется.")
                # Удаляем временную таблицу, если она создалась
                cur.execute("DROP TABLE IF EXISTS addresses_new")

            # Удаляем старый индекс, если он существует
            try:
                cur.execute("DROP INDEX IF EXISTS idx_addresses_user_id")
            except:
                pass

            conn.commit()
            print("Миграция таблицы addresses завершена успешно!")

            # Показываем текущие адреса
            print("\nТекущие адреса в базе:")
            addresses = list_addresses(conn)
            for addr in addresses:
                print(f"  {addr}")

        except Exception as e:
            print(f"Ошибка при миграции: {e}")
            conn.rollback()