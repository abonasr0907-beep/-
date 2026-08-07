FROM python:3.11-slim

WORKDIR /app

# تثبيت تبعيات النظام لـ Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    git \
    && rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات وتثبيتها
COPY bot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# نسخ المشروع كامل
COPY . .

# مجلد العمل داخل مجلد البوت
WORKDIR /app/bot

# تشغيل البوت (مع إعادة تشغيل تلقائية داخل start_bot.sh)
CMD ["bash", "start_bot.sh"]
