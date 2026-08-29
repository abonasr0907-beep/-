"""
bot/modules/customers.py
قسم إحصائيات وتفاعلات العملاء والـ CRM
"""

from collections import Counter
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def customers_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import main
    events = getattr(main, 'CRM_EVENTS', [])

    if not events:
        msg = (
            "👥 *إحصائيات وقاعدة تفاعلات العملاء (CRM)*\n\n"
            "لا توجد تفاعلات أو أحداث مسجلة حتى الآن."
        )
        return await update.message.reply_text(msg, parse_mode="Markdown")

    counts = Counter(e.get("type", "unknown") for e in events)
    last_10 = events[-10:]

    text_summary = "👥 *إحصائيات وقاعدة تفاعلات العملاء (CRM)*\n\n"
    text_summary += f"📊 *إجمالي الأحداث المسجلة:* {len(events)}\n"
    text_summary += "📈 *توزيع التفاعلات:*\n"
    for event_type, count in counts.items():
        text_summary += f" • {event_type}: {count}\n"

    text_summary += "\n📋 *آخر 10 تفاعلات للعملاء:*\n"
    for idx, ev in enumerate(reversed(last_10), 1):
        ev_type = ev.get("type", "أمر")
        ev_time = ev.get("timestamp", "").split("T")[0]
        text_summary += f"{idx}. [{ev_type}] بتاريخ {ev_time}\n"

    text_summary += "\n💡 لاستخراج تقرير نصي كامل للتفاعلات، استخدم الأمر مع التصدير."

    await update.message.reply_text(text_summary, parse_mode="Markdown")

def get_customers_handler():
    return CommandHandler("customers", customers_command_handler)
