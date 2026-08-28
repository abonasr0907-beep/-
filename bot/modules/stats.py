from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.config import VISITORS_FILE
from bot.database import load_properties, load_json
from utils.helpers import format_number, format_currency

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    visitors = load_json(VISITORS_FILE, default=[])

    total_props = len(properties)
    active_props = len([p for p in properties if p.get("status") == "active"])
    archived_props = len([p for p in properties if p.get("status") == "archived"])
    draft_props = len([p for p in properties if p.get("status") == "draft"])

    total_visitors = len(visitors)
    contacted_visitors = len([v for v in visitors if v.get("status") == "contacted"])

    # Location demand calculation
    loc_counts = {}
    for p in properties:
        loc = p.get("location", "أخرى")
        loc_counts[loc] = loc_counts.get(loc, 0) + 1

    top_locs = sorted(loc_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_locs_str = ", ".join([f"{loc} ({count})" for loc, count in top_locs]) if top_locs else "لا يوجد"

    # Average price calculation
    prices = [p.get("price", 0) for p in properties if p.get("price")]
    avg_price = sum(prices) / len(prices) if prices else 0

    text = (
        "📊 *إحصائيات النظام - آفاق الإنجاز*\n\n"
        f"🏡 *إجمالي العروض:* {total_props}\n"
        f"  • نشط: {active_props} 🟢\n"
        f"  • مسودة: {draft_props} 🟡\n"
        f"  • مؤرشف: {archived_props} 📦\n\n"
        f"📨 *طلبات الزوار:* {total_visitors} (تم التواصل: {contacted_visitors})\n"
        f"📍 *أكثر المناطق عرضاً:* {top_locs_str}\n"
        f"💰 *متوسط أسعار العقارات:* {format_currency(avg_price)}\n"
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_stats_handler():
    return CallbackQueryHandler(stats_handler, pattern="^stats$")
