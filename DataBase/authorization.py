import sqlite3
from typing import Optional, List, Tuple
from datetime import datetime
from DataBase import users as us


class UserCredentials:
    def __init__(
            self,
            user_id: str,
            login: str,
            password_hash: str,
            role: str,
            created_at: Optional[datetime] = None,
            updated_at: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.login = login
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return (
            f"UserCredentials(user_id={self.user_id!r}, "
            f"login={self.login!r}, "
            f"role={self.role!r}, "
            f"created_at={self.created_at!r})"
        )

    def __str__(self):
        return f"{self.login} ({self.role})"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserCredentials":
        return cls(
            user_id=row["user_id"],
            login=row["login"],
            password_hash=row["password_hash"],
            role=row["role"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )

    def to_tuple(self) -> tuple:
        return (
            self.user_id,
            self.login,
            self.password_hash,
            self.role,
        )


def create_credentials_table(conn: sqlite3.Connection) -> None:
    """
    Создает таблицу для хранения учетных данных пользователей
    """
    sql = """
    CREATE TABLE IF NOT EXISTS user_credentials (
        user_id TEXT PRIMARY KEY,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()


def create_user_credentials(
        conn: sqlite3.Connection,
        user_id: str,
        login: str,
        password_hash: str,
        role: str
) -> None:
    """
    Создает учетные данные для пользователя
    """
    sql = """
    INSERT INTO user_credentials (user_id, login, password_hash, role)
    VALUES (?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, (user_id, login, password_hash, role))
    conn.commit()


def get_user_credentials(conn: sqlite3.Connection, user_id: str) -> Optional[UserCredentials]:
    """
    Получает учетные данные пользователя по ID
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_credentials WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return UserCredentials.from_row(row) if row else None


def get_user_credentials_by_login(conn: sqlite3.Connection, login: str) -> Optional[UserCredentials]:
    """
    Получает учетные данные пользователя по логину
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_credentials WHERE login = ?", (login,))
    row = cur.fetchone()
    return UserCredentials.from_row(row) if row else None


def update_user_credentials(conn: sqlite3.Connection, credentials: UserCredentials) -> bool:
    """
    Обновляет учетные данные пользователя
    """
    sql = """
    UPDATE user_credentials SET
        login = ?,
        password_hash = ?,
        role = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = ?
    """
    cur = conn.cursor()
    params = (
        credentials.login,
        credentials.password_hash,
        credentials.role,
        credentials.user_id
    )
    cur.execute(sql, params)
    conn.commit()
    return cur.rowcount > 0


def update_user_password(conn: sqlite3.Connection, user_id: str, new_password_hash: str) -> bool:
    """
    Обновляет только пароль пользователя
    """
    sql = """
    UPDATE user_credentials SET
        password_hash = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (new_password_hash, user_id))
    conn.commit()
    return cur.rowcount > 0


def update_user_role(conn: sqlite3.Connection, user_id: str, new_role: str) -> bool:
    """
    Обновляет только роль пользователя
    """
    sql = """
    UPDATE user_credentials SET
        role = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (new_role, user_id))
    conn.commit()
    return cur.rowcount > 0


def delete_user_credentials(conn: sqlite3.Connection, user_id: str) -> bool:
    """
    Удаляет учетные данные пользователя
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM user_credentials WHERE user_id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0


def authenticate_user(conn: sqlite3.Connection, login: str, password: str) -> Optional[UserCredentials]:
    """
    Аутентифицирует пользователя по логину и паролю
    """
    credentials = get_user_credentials_by_login(conn, login)
    if credentials and us.verify_password(password, credentials.password_hash):
        return credentials
    return None


def get_user_with_credentials(conn: sqlite3.Connection, user_id: str) -> Tuple[
    Optional['User'], Optional[UserCredentials]]:
    """
    Получает полную информацию о пользователе (основные данные + учетные данные)
    """
    from users import get_user  # Импортируем здесь, чтобы избежать циклического импорта

    user = get_user(conn, user_id)
    credentials = get_user_credentials(conn, user_id)
    return user, credentials


def get_all_users_with_credentials(conn: sqlite3.Connection) -> List[Tuple['User', UserCredentials]]:
    """
    Получает всех пользователей с их учетными данными
    """
    from users import list_users

    users = list_users(conn)
    result = []

    for user in users:
        credentials = get_user_credentials(conn, user.id)
        if credentials:
            result.append((user, credentials))

    return result


def search_users_by_login(conn: sqlite3.Connection, login_pattern: str) -> List[Tuple['User', UserCredentials]]:
    """
    Ищет пользователей по логину (частичное совпадение)
    """
    from users import get_user

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    SELECT uc.*, u.* 
    FROM user_credentials uc
    JOIN users u ON uc.user_id = u.id
    WHERE uc.login LIKE ?
    ORDER BY uc.login
    """

    cur.execute(sql, (f"%{login_pattern}%",))
    rows = cur.fetchall()

    result = []
    for row in rows:
        user = get_user(conn, row["user_id"])
        credentials = UserCredentials.from_row(row)
        if user:
            result.append((user, credentials))

    return result


def create_complete_user(
        conn: sqlite3.Connection,
        user_id: str,
        first_name: str,
        last_name: str,
        middle_name: Optional[str],
        birthdate: str,
        phone: str,
        email: str,
        vip: bool,
        login: str,
        password: str,
        role: str,
        photo: Optional[str] = None
) -> bool:
    """
    Создает полного пользователя (основные данные + учетные данные)
    """
    from users import User, create_user

    try:
        # Создаем основного пользователя
        user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            birthdate=birthdate,
            phone=phone,
            email=email,
            vip=vip,
            photo=photo
        )
        create_user(conn, user)

        # Создаем учетные данные
        password_hash = us.hash_password(password)
        create_user_credentials(conn, user_id, login, password_hash, role)

        return True
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return False


# Пример использования
if __name__ == "__main__":
    import sqlite3
    from users import init_db_schema

    # Тестовое подключение
    conn = sqlite3.connect("test.db")

    # Инициализация схемы
    init_db_schema(conn)

    # Пример создания пользователя
    create_complete_user(
        conn=conn,
        user_id="us100",
        first_name="Иван",
        last_name="Петров",
        middle_name="Сергеевич",
        birthdate="1990-01-01",
        phone="+79990000000",
        email="ivan@example.com",
        vip=True,
        login="ivan90",
        password="secret123",
        role="user",
        photo=None
    )

    # Пример аутентификации
    credentials = authenticate_user(conn, "ivan90", "secret123")
    if credentials:
        print(f"Аутентификация успешна: {credentials}")
    else:
        print("Аутентификация не удалась")

    conn.close()