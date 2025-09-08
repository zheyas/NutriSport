import os
import sqlite3

# Определяем корень проекта
BASE_DIR = os.path.dirname(__file__)

conn_str = sqlite3.connect(os.path.join(BASE_DIR, 'SportPit.db'))

per_page = 10  # количество пользователей на страницу

