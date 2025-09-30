import os
import sqlite3
from pathlib import Path

# Определяем корень проекта
BASE_DIR = os.path.dirname(__file__)

conn_str = sqlite3.connect(os.path.join(BASE_DIR, 'SportPit.db'))

DB_PATH = os.path.join(BASE_DIR, 'SportPit.db')


per_page = 10  # количество пользователей на страницу

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 3 * 1024 * 1024  # 3 МБ
UPLOAD_DIR = Path(BASE_DIR) / "static" / "img"