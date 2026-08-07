#!/bin/bash
# سكربت تشغيل البوت مع إعادة تشغيل تلقائية عند التوقف
# Bot runner with auto-restart on crash
# استخدم: chmod +x start_bot.sh && ./start_bot.sh

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BOT_DIR"

echo "🚀 بدء تشغيل بوت آفاق الإنجاز العقاري..."
echo "📁 المجلد: $BOT_DIR"
echo "🔄 إعادة تشغيل تلقائية مفعّلة"
echo "📄 السجل: bot.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ▶ تشغيل البوت..."
    python3 bot.py >> bot.log 2>&1
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠ البوت توقف (كود: $EXIT_CODE)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 إعادة تشغيل خلال 5 ثوان..."
    sleep 5
done
