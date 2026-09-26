"""
Заполняет базу NutriSport начальными данными, если она пустая.

Использование:
    python seed_db.py            # заполнить, только если в базе нет пользователей и товаров
    python seed_db.py --force    # применить seed поверх существующих данных
                                 # (INSERT OR IGNORE — существующие строки не трогаются)

Путь к базе берётся из setting.DB_PATH (переменная окружения DB_PATH).
Данные лежат в db/seed.sql.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

from setting import DB_PATH

SEED_FILE = Path(__file__).resolve().parent / "db" / "seed.sql"
CHECK_TABLES = ("users", "products")


def table_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    except sqlite3.OperationalError:
        return 0  # таблицы ещё нет


def is_empty(conn: sqlite3.Connection) -> bool:
    return all(table_count(conn, t) == 0 for t in CHECK_TABLES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="применить seed даже если данные уже есть")
    args = parser.parse_args()

    if not SEED_FILE.exists():
        print(f"[seed] Файл {SEED_FILE} не найден — пропускаю.")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        if not is_empty(conn) and not args.force:
            stats = ", ".join(f"{t}={table_count(conn, t)}" for t in CHECK_TABLES)
            print(f"[seed] База {DB_PATH} уже содержит данные ({stats}) — заполнение пропущено.")
            return 0

        print(f"[seed] Заполняю базу {DB_PATH} из {SEED_FILE.name}...")
        script = SEED_FILE.read_text(encoding="utf-8")
        try:
            conn.executescript("BEGIN;\n" + script + "\nCOMMIT;")
        except sqlite3.Error:
            conn.rollback()
            raise

        stats = ", ".join(
            f"{t}={table_count(conn, t)}"
            for t in ("users", "user_credentials", "products", "addresses", "orders", "cart")
        )
        print(f"[seed] Готово: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
