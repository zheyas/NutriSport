import sqlite3


from typing import Optional, List, Union
from datetime import datetime
from setting import conn_str
import bcrypt


def hash_password(password: str) -> str:
    """
    Принимает plain-текст пароля, возвращает bcrypt-хеш в виде строки.
    """
    # gensalt() генерирует случайную соль (по умолчанию log_rounds=12)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    # возвращаем строку, пригодную для хранения
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет plain-пароль против ранее сгенерированного хеша.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"),
                          hashed_password.encode("utf-8"))

#h = hash_password('123test321')
#print(h)
#print(verify_password("123test123", h))
#print(verify_password('123test321', h))

class User:
    def __init__(
        self,
        id: str,
        first_name: str,
        last_name: str,
        middle_name: Optional[str],
        birthdate: Union[str, datetime],        # 'YYYY-MM-DD'
        phone: str,
        email: str,
        role: str,
        vip: bool,
        login: str,
        password_hash: str
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.birthdate = birthdate
        self.phone = phone
        self.email = email
        self.role = role
        self.vip = vip
        self.login = login
        self.password_hash = password_hash

    def __repr__(self):
        return (
            f"User(id={self.id!r}, "
            f"first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, "
            f"middle_name={self.middle_name!r}, "
            f"birthdate={self.birthdate!r}, "
            f"phone={self.phone!r}, "
            f"email={self.email!r}, "
            f"role={self.role!r}, "
            f"vip={self.vip!r},"
            f" login={self.login})"

        )

    def __str__(self):
        return (
            f"[{self.id}] {self.first_name} {self.last_name} "
            f"({self.role}, VIP={'yes' if self.vip else 'no'})"
        )

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            middle_name=row["middle_name"],
            birthdate=row["birthdate"],
            phone=row["phone"],
            email=row["email"],
            role=row["role"],
            vip=bool(row["vip"]),
            login=row["login"],
            password_hash=row["password_hash"],
        )

    def to_tuple(self) -> tuple:
        """
        Возвращает кортеж в том же порядке, что в INSERT/UPDATE.
        """
        return (
            self.id,
            self.first_name,
            self.last_name,
            self.middle_name,
            self.birthdate,
            self.phone,
            self.email,
            self.role,
            int(self.vip),
            self.login,
            self.password_hash,
        )

# CRUD-функции

def create_user(conn: sqlite3.Connection, user: User) -> None:
    sql = """
    INSERT INTO users (
        id, first_name, last_name, middle_name,
        birthdate, phone, email, role, vip,
        login, password_hash
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        role          = ?,
        vip           = ?,
        login         = ?,
        password_hash = ?
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
        user.role,
        int(user.vip),
        user.login,
        user.password_hash,
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

def get_user_by_login(conn: sqlite3.Connection, login: str) -> List[User]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE login LIKE ?", (f"%{login}%",))
    rows = cur.fetchall()
    return [User.from_row(row) for row in rows]

def users_table_info(conn: sqlite3.Connection) -> str:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (users)")
    cols = [r["name"] for r in cur.fetchall() if "password" not in r["name"]]

    return(cols)

def get_next_user_id(conn: sqlite3.Connection) -> str:
    """
    Берёт из таблицы users максимальный числовой суффикс в id вида 'us<число>'
    и возвращает новый id с числом+1.
    Если записей нет, вернёт 'us1'.
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # substr(id,3) — отрезаем 'us', приводим к целому и берём максимум
    cur.execute(
        "SELECT MAX(CAST(substr(id,3) AS INTEGER)) AS maxnum "
        "FROM users"
    )
    row = cur.fetchone()
    maxnum = row["maxnum"] or 0
    return f"us{maxnum + 1}"

def add_new_user_example(conn: sqlite3.Connection):
    # Получаем уникальный id
    new_id = get_next_user_id(conn)

    # Формируем остальную информацию
    u = User(
        id=new_id,
        first_name="Николай",
        last_name="Коновалов",
        middle_name=None,
        birthdate="1988-07-12",
        phone="+79991234567",
        email="nikolay111@example.com",
        role="user",
        vip=False,
        login="nikolay",
        password_hash=hash_password("secret123")
    )

    # Вставляем
    create_user(conn, u)
    print(f"Создан пользователь {u.login} с id={u.id}")

