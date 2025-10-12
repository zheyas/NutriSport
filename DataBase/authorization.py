# DataBase/authorization.py
import sqlite3
from typing import Optional, List, Tuple, Any
from datetime import datetime, timedelta
import secrets


class UserCredential:
    def __init__(
            self,
            user_id: str,
            login: str,
            password_hash: str,
            role: str = "user",  # ДОБАВЛЯЕМ поле role
            created_at: Optional[str] = None,
            updated_at: Optional[str] = None
    ):
        self.user_id = user_id
        self.login = login
        self.password_hash = password_hash
        self.role = role  # ДОБАВЛЯЕМ поле role
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return (
            f"UserCredential(user_id={self.user_id!r}, "
            f"login={self.login!r}, "
            f"role={self.role!r}, "
            f"created_at={self.created_at!r})"
        )

    def __str__(self):
        return f"{self.login} ({self.user_id}) - {self.role}"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserCredential":
        return cls(
            user_id=row["user_id"],
            login=row["login"],
            password_hash=row["password_hash"],
            role=row["role"] if "role" in row.keys() else "user",  # ДОБАВЛЯЕМ role
            created_at=row["created_at"] if "created_at" in row.keys() else None,
            updated_at=row["updated_at"] if "updated_at" in row.keys() else None
        )

    def to_tuple(self) -> tuple:
        return (
            self.user_id,
            self.login,
            self.password_hash,
            self.role,  # ДОБАВЛЯЕМ role
            self.created_at,
            self.updated_at
        )


class UserSession:
    def __init__(
            self,
            session_id: str,
            user_id: str,
            created_at: Optional[str] = None,
            expires_at: Optional[str] = None,
            last_activity: Optional[str] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_activity = last_activity

    def __repr__(self):
        return f"UserSession(session_id={self.session_id!r}, user_id={self.user_id!r})"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserSession":
        return cls(
            session_id=row["session_id"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            last_activity=row["last_activity"]
        )

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires


def init_user_credentials_table(conn: sqlite3.Connection) -> None:
    """
    Создает таблицу для хранения учетных данных пользователей
    """
    sql = """
    CREATE TABLE IF NOT EXISTS user_credentials (
        user_id TEXT PRIMARY KEY,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',  
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """
    cur = conn.cursor()
    cur.execute(sql)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_credentials_login ON user_credentials(login)")
    conn.commit()


def init_user_sessions_table(conn: sqlite3.Connection) -> None:
    """
    Создает таблицу для хранения пользовательских сессий
    """
    sql = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL,
        last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """
    cur = conn.cursor()
    cur.execute(sql)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)")
    conn.commit()


def create_user_credential(
        conn: sqlite3.Connection,
        user_id: str,
        login: str,
        password_hash: str,
        role: str = "user"  # ДОБАВЛЯЕМ параметр role
) -> None:
    """
    Создает учетные данные для пользователя
    """
    sql = """
    INSERT INTO user_credentials (user_id, login, password_hash, role)
    VALUES (?, ?, ?, ?)  
    """
    cur = conn.cursor()
    cur.execute(sql, (user_id, login, password_hash, role))  # ДОБАВЛЯЕМ role
    conn.commit()


def get_user_credential(conn: sqlite3.Connection, user_id: str) -> Optional[UserCredential]:
    """
    Получает учетные данные пользователя по ID
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_credentials WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return UserCredential.from_row(row) if row else None


def get_user_credential_by_login(conn: sqlite3.Connection, login: str) -> Optional[UserCredential]:
    """
    Получает учетные данные пользователя по логину
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_credentials WHERE login = ?", (login,))
    row = cur.fetchone()
    return UserCredential.from_row(row) if row else None


def update_user_credential(conn: sqlite3.Connection, credential: UserCredential) -> bool:
    """
    Обновляет учетные данные пользователя
    """
    sql = """
    UPDATE user_credentials SET
        login = ?,
        password_hash = ?,
        role = ?,  # ДОБАВЛЯЕМ обновление role
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = ?
    """
    cur = conn.cursor()
    params = (
        credential.login,
        credential.password_hash,
        credential.role,  # ДОБАВЛЯЕМ role
        credential.user_id
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


def update_user_login(conn: sqlite3.Connection, user_id: str, new_login: str) -> bool:
    """
    Обновляет только логин пользователя
    """
    sql = """
    UPDATE user_credentials SET
        login = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (new_login, user_id))
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


def delete_user_credential(conn: sqlite3.Connection, user_id: str) -> bool:
    """
    Удаляет учетные данные пользователя
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM user_credentials WHERE user_id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0


def authenticate_user(conn: sqlite3.Connection, login: str, password: str) -> Optional[UserCredential]:
    """
    Аутентифицирует пользователя по логину и паролю
    """
    # Импортируем здесь, чтобы избежать циклического импорта
    from DataBase.users import verify_password

    credential = get_user_credential_by_login(conn, login)
    if credential and verify_password(password, credential.password_hash):
        return credential
    return None


def list_user_credentials(conn: sqlite3.Connection) -> List[UserCredential]:
    """
    Получает все учетные данные пользователей
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_credentials ORDER BY user_id")
    rows = cur.fetchall()
    return [UserCredential.from_row(row) for row in rows]


def credentials_table_info(conn: sqlite3.Connection) -> List[str]:
    """
    Возвращает информацию о структуре таблицы учетных данных
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info (user_credentials)")
    cols = [r["name"] for r in cur.fetchall()]
    return cols


def get_user_with_credential(conn: sqlite3.Connection, user_id: str) -> Tuple[Any, Optional[UserCredential]]:
    """
    Получает полную информацию о пользователе (основные данные + учетные данные)
    """
    # Импортируем здесь, чтобы избежать циклического импорта
    from DataBase.users import get_user

    user = get_user(conn, user_id)
    credential = get_user_credential(conn, user_id)
    return user, credential


def get_all_users_with_credentials(conn: sqlite3.Connection) -> List[Tuple[Any, UserCredential]]:
    """
    Получает всех пользователей с их учетными данными
    """
    # Импортируем здесь, чтобы избежать циклического импорта
    from DataBase.users import list_users

    users_list = list_users(conn)
    result = []

    for user in users_list:
        credential = get_user_credential(conn, user.id)
        if credential:
            result.append((user, credential))

    return result


def search_users_by_login(conn: sqlite3.Connection, login_pattern: str) -> List[Tuple[Any, UserCredential]]:
    """
    Ищет пользователей по логину (частичное совпадение)
    """
    # Импортируем здесь, чтобы избежать циклического импорта
    from DataBase.users import get_user

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    SELECT uc.* 
    FROM user_credentials uc
    WHERE uc.login LIKE ?
    ORDER BY uc.login
    """

    cur.execute(sql, (f"%{login_pattern}%",))
    rows = cur.fetchall()

    result = []
    for row in rows:
        user = get_user(conn, row["user_id"])
        credential = UserCredential.from_row(row)
        if user:
            result.append((user, credential))

    return result


def create_complete_user(
        conn: sqlite3.Connection,
        user_data: dict,
        login: str,
        password: str
) -> bool:
    """
    Создает полного пользователя (основные данные + учетные данные)
    """
    try:
        # Импортируем здесь, чтобы избежать циклического импорта
        from DataBase.users import User, create_user, get_next_user_id, hash_password

        # Создаем основного пользователя
        user_id = get_next_user_id(conn)

        user = User(
            id=user_id,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            middle_name=user_data.get('middle_name'),
            birthdate=user_data.get('birthdate'),
            phone=user_data.get('phone', ''),
            email=user_data.get('email', ''),
            vip=bool(user_data.get('vip', False)),
            photo=user_data.get('photo'),
            login=login  # Сохраняем логин и в основной таблице для совместимости
        )
        create_user(conn, user)

        # Создаем учетные данные С РОЛЬЮ
        password_hash = hash_password(password)
        create_user_credential(conn, user_id, login, password_hash, "user")  # ЯВНО ПЕРЕДАЕМ РОЛЬ

        return True
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def user_exists_by_login(conn: sqlite3.Connection, login: str) -> bool:
    """
    Проверяет, существует ли пользователь с таким логином
    """
    credential = get_user_credential_by_login(conn, login)
    return credential is not None


# Функции для управления сессиями
def create_user_session(conn: sqlite3.Connection, user_id: str, duration_hours: int = 24) -> UserSession:
    """
    Создает новую сессию для пользователя
    """
    session_id = secrets.token_urlsafe(32)
    created_at = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()

    sql = """
    INSERT INTO user_sessions (session_id, user_id, created_at, expires_at, last_activity)
    VALUES (?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, (session_id, user_id, created_at, expires_at, created_at))
    conn.commit()

    return UserSession(session_id, user_id, created_at, expires_at, created_at)


def get_user_session(conn: sqlite3.Connection, session_id: str) -> Optional[UserSession]:
    """
    Получает сессию по ID
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_sessions WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    return UserSession.from_row(row) if row else None


def update_session_activity(conn: sqlite3.Connection, session_id: str) -> bool:
    """
    Обновляет время последней активности сессии
    """
    sql = "UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (session_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_user_session(conn: sqlite3.Connection, session_id: str) -> bool:
    """
    Удаляет сессию
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_expired_sessions(conn: sqlite3.Connection) -> int:
    """
    Удаляет все истекшие сессии и возвращает количество удаленных
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP")
    conn.commit()
    return cur.rowcount


def delete_all_user_sessions(conn: sqlite3.Connection, user_id: str) -> int:
    """
    Удаляет все сессии пользователя
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    return cur.rowcount


def get_user_sessions(conn: sqlite3.Connection, user_id: str) -> List[UserSession]:
    """
    Получает все активные сессии пользователя
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM user_sessions 
        WHERE user_id = ? AND expires_at > CURRENT_TIMESTAMP 
        ORDER BY last_activity DESC
    """, (user_id,))
    rows = cur.fetchall()
    return [UserSession.from_row(row) for row in rows]


# Функции для обратной совместимости
create_user_credentials = create_user_credential
get_user_credentials = get_user_credential
get_user_credentials_by_login = get_user_credential_by_login
update_user_credentials = update_user_credential
delete_user_credentials = delete_user_credential