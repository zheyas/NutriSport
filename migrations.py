import sqlite3
from setting import DB_PATH


def ensure_photo_column(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]  # r[1] = name
    if "photo" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN photo TEXT")
        conn.commit()

def set_user_photo(user_id: str, photo_url: str) -> bool:
    """
    Обновляет поле photo у пользователя с данным id.
    Возвращает True, если запись обновлена (пользователь найден), иначе False.
    """
    if not user_id or not photo_url:
        raise ValueError("user_id и photo_url обязательны")

    with sqlite3.connect(DB_PATH) as conn:
        ensure_photo_column(conn)
        cur = conn.cursor()
        cur.execute("UPDATE users SET photo = ? WHERE id = ?", (photo_url.strip(), user_id))
        conn.commit()
        return cur.rowcount > 0

# Пример: установить аватар для us0
if __name__ == "__main__":
    ok = set_user_photo(
        "us0",
        "https://i.pinimg.com/736x/77/20/f0/7720f0ffa6a6003ebc94152c4e365bec.jpg"
    )
    print("Аватар обновлён" if ok else "Пользователь не найден")