FROM python:3.11-slim

WORKDIR /app

# تثبيت مكتبات النظام اللازمة لـ Pillow (معالجة الصور) و git
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    git \
    && rm -rf /var/lib/apt/lists/*

# نسخ requirements.txt من مجلد bot وتثبيت المتطلبات
COPY bot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع كاملاً
COPY . .

# مجلد العمل داخل مجلد البوت (لأن bot.py يستخدم مسارات نسبية)
WORKDIR /app/bot

# المنفذ الذي يستمع عليه البوت في وضع webhook
# Render يحدد PORT تلقائياً عبر متغير البيئة
ENV PORT=10000
EXPOSE 10000

# تشغيل البوت مباشرة
CMD ["python3", "bot.py"]
