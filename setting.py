import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Определяем корень проекта
BASE_DIR = os.path.dirname(__file__)

# Настройки базы данных
DB_PATH = os.path.join(BASE_DIR, 'SportPit.db')
conn_str = sqlite3.connect(DB_PATH)
per_page = 10  # количество пользователей на страницу

# Настройки загрузки изображений
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 3 * 1024 * 1024  # 3 МБ
UPLOAD_DIR = Path(BASE_DIR) / "static" / "img"

# Stripe settings
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_CURRENCY = 'rub'

# Другие настройки (если есть)
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', '')