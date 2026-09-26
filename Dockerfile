FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DB_PATH=/data/SportPit.db \
    ADMIN_SUDO_VERIFICATION=0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker/entrypoint.sh && mkdir -p /data

VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
# Render передаёт порт в переменной PORT; локально по умолчанию 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
