FROM python:3.11-slim

WORKDIR /app

# تثبيت تبعيات النظام لـ Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    git \
    && rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات وتثبيتها
COPY bot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ المشروع كامل
COPY . .

# مجلد العمل داخل مجلد البوت
WORKDIR /app/bot

# إنشاء مجلد البيانات (يتم الكتابة عليه في وقت التشغيل للجلسات/المسودات/النسخ الاحتياطية)
# تأكد من وجود المجلد حتى لو لم يكن مُلَحَّقاً في git
RUN mkdir -p /app/bot/data /app/bot/data/backups

# المنفذ الذي يستمع عليه البوت في وضع webhook
# Render وغيرها تحدد PORT تلقائياً عبر متغير البيئة
EXPOSE 10000

# تشغيل البوت مباشرة (python-telegram-bot يعيد التشغيل تلقائياً عند الأخطاء)
CMD ["python3", "bot.py"]
