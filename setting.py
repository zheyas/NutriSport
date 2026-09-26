import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Определяем корень проекта
BASE_DIR = os.path.dirname(__file__)

# Настройки базы данных
# Путь к SQLite-базе можно переопределить через DB_PATH
# (в Docker база лежит в томе /data внутри контейнера)
DB_PATH = os.getenv('DB_PATH') or os.path.join(BASE_DIR, 'SportPit.db')
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
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

# Mail settings
MAIL_LOGIN = os.getenv('MAIL_LOGIN', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_SMTP_HOST = os.getenv('MAIL_SMTP_HOST', 'smtp.mail.ru')
MAIL_SMTP_PORT = int(os.getenv('MAIL_SMTP_PORT', '465'))
MAIL_DEBUG_CODE = os.getenv('MAIL_DEBUG_CODE', '0').strip().lower() in {'1', 'true', 'yes', 'on'}

# Другие настройки (если есть)
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', '')
