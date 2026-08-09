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
# في Railway، يمكن ربط Volume بمسار /app/bot/data للتخزين الدائم
RUN mkdir -p /app/bot/data /app/bot/data/backups

# Railway يوفر PORT تلقائياً عبر متغير البيئة
# البوت يستخدم PORT في وضع webhook، أو polling إذا لم يوجد WEBHOOK_URL
EXPOSE 10000
# منفذ خادم API لاستقبال طلبات الزوار من الموقع (اختياري)
EXPOSE 8080

# تشغيل البوت مباشرة
# python-telegram-bot يعيد التشغيل تلقائياً عند الأخطاء
# Railway يعيد التشغيل عند التعطل (restartPolicyType = ON_FAILURE)
CMD ["python3", "bot.py"]
