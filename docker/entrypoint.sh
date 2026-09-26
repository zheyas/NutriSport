#!/bin/sh
set -e

# Заполняем SQLite-базу начальными данными, если она пустая
python seed_db.py

exec "$@"
