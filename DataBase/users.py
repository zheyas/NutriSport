#DataBase/users.py
import sqlite3
from typing import Optional, List, Union
from datetime import datetime
from setting import conn_str
import bcrypt


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"),
                          hashed_password.encode("utf-8"))


class User:
    def __init__(
            self,
            id: str,
            first_name: str,
            last_name: str,
            middle_name: Optional[str],
            birthdate: Union[str, datetime],
            phone: str,
            email: str,
            vip: bool,
            photo: Optional[str] = None,
            login: Optional[str] = None  # Оставляем для обратной совместимости
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.birthdate = birthdate
        self.phone = phone
        self.email = email
        self.vip = vip
        self.photo = photo
        self.login = login  # Для обратной совместимости

    def __repr__(self):
        return (
            f"User(id={self.id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"middle_name={self.middle_name!r}, "
            f"birthdate={self.birthdate!r}, "
            f"phone={self.phone!r}, "
            f"email={self.email!r}, "
            f"vip={self.vip!r}, "
            f"photo={self.photo!r})"
        )

    def __str__(self):
        return (
            f"[{self.id}] {self.first_name} {self.last_name} "
            f"(VIP={'yes' if self.vip else 'no'})"
        )

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        photo = row["photo"] if "photo" in row.keys() else None
        login = row["login"] if "login" in row.keys() else None
        return cls(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            middle_name=row["middle_name"],
            birthdate=row["birthdate"],
            phone=row["phone"],
            email=row["email"],
            vip=bool(row["vip"]),
            photo=photo,
            login=login
        )

    def to_tuple(self) -> tuple:
        """
        Порядок — как в INSERT/UPDATE (без аутентификационных данных).
        """
        return (
            self.id,
            self.first_name,
            self.last_name,
            self.middle_name,
            self.birthdate,
            self.phone,
            self.email,
            int(self.vip),
            self.photo,
        )


# CRUD операции только для основной информации пользователя

def create_user(conn: sqlite3.Connection, user: User) -> None:
    sql = """
    INSERT INTO users (
        id, first_name, last_name, middle_name,
        birthdate, phone, email, vip, photo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, user.to_tuple())
    conn.commit()


def get_user(conn: sqlite3.Connection, user_id: str) -> Optional[User]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    return User.from_row(row) if row else None


def update_user(conn: sqlite3.Connection, user: User) -> bool:
    sql = """
    UPDATE users SET
        first_name    = ?,
        last_name     = ?,
        middle_name   = ?,
        birthdate     = ?,
        phone         = ?,
        email         = ?,
        vip           = ?,
        photo         = ?
    WHERE id = ?
    """
    cur = conn.cursor()
    params = (
        user.first_name,
        user.last_name,
        user.middle_name,
        user.birthdate,
        user.phone,
        user.email,
        int(user.vip),
        user.photo,
        user.id
    )
    cur.execute(sql, params)
    conn.commit()
    return cur.rowcount > 0


def delete_user(conn: sqlite3.Connection, user_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0


def list_users(conn: sqlite3.Connection) -> List[User]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id")
    rows = cur.fetchall()
    return [User.from_row(row) for row in rows]


def users_table_info(conn: sqlite3.Connection) -> List[str]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (users)")
    cols = [r["name"] for r in cur.fetchall()]
    return cols


def get_next_user_id(conn: sqlite3.Connection) -> str:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT MAX(CAST(substr(id,3) AS INTEGER)) AS maxnum "
        "FROM users"
    )
    row = cur.fetchone()
    maxnum = row["maxnum"] or 0
    return f"us{maxnum + 1}"


def migrate_to_new_schema(conn: sqlite3.Connection) -> None:
    """
    Мигрирует существующие данные в новую схему с раздельными таблицами
    """
    # Импортируем здесь, чтобы избежать циклического импорта
    from DataBase import authorization as au

    # Создаем таблицу учетных данных
    au.init_user_credentials_table(conn)

    # Переносим существующие учетные данные
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Получаем всех пользователей со старыми учетными данными
    cur.execute("SELECT id, login, password_hash FROM users WHERE login IS NOT NULL")
    users_with_creds = cur.fetchall()

    # Переносим учетные данные в новую таблицу
    for user in users_with_creds:
        au.create_user_credential(conn, user['id'], user['login'], user['password_hash'])

    # Создаем временную таблицу без полей аутентификации
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users_new (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        middle_name TEXT,
        birthdate TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        vip INTEGER NOT NULL DEFAULT 0,
        photo TEXT
    )
    """)

    # Копируем данные (исключаем аутентификационные поля)
    cur.execute("""
    INSERT INTO users_new (id, first_name, last_name, middle_name, birthdate, phone, email, vip, photo)
    SELECT id, first_name, last_name, middle_name, birthdate, phone, email, vip, photo FROM users
    """)

    # Заменяем старую таблицу на новую
    cur.execute("DROP TABLE users")
    cur.execute("ALTER TABLE users_new RENAME TO users")

    conn.commit()
    print("Миграция данных завершена успешно")


def check_schema_version(conn: sqlite3.Connection) -> bool:
    """
    Проверяет, проведена ли уже миграция схемы
    """
    try:
        # Проверяем существование таблицы user_credentials
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_credentials'")
        return cur.fetchone() is not None
    except:
        return False


def init_db_schema(conn: sqlite3.Connection) -> None:
    """
    Инициализирует схему БД (выполняет миграцию при необходимости)
    """
    if not check_schema_version(conn):
        print("Проводим миграцию схемы базы данных...")
        migrate_to_new_schema(conn)
    else:
        print("Схема базы данных актуальна")

def get_all_users(conn: sqlite3.Connection) -> List[User]:
    """Получить всех пользователей (альтернативное название для совместимости)"""
    return list_users(conn)