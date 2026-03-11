FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para Pillow y qrcode
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 libfreetype6-dev fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run pasa PORT como variable de entorno (default 8080)
ENV PORT=8080

CMD ["python", "telegram_bot.py"]
