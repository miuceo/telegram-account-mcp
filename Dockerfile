# Python yengil rasmiy versiyasi
FROM python:3.11-slim

# Ishchi papka
WORKDIR /app

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Bog'liqliklarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodlarini ko'chirish
COPY . .

# Standart portni ochish
EXPOSE 8000

# Serverni SSE rejimida ishga tushirish
CMD ["python", "server.py", "--transport", "sse"]
