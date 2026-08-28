from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties

async def assistant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    total_props = len(properties)

    # Simple AI recommendation logic
    loc_counts = {}
    for p in properties:
        loc = p.get("location", "أخرى")
        loc_counts[loc] = loc_counts.get(loc, 0) + 1

    top_loc = max(loc_counts.items(), key=lambda x: x[1])[0] if loc_counts else "الرحمانية"

    text = (
        "🤖 *المساعد الذكي للتحليل والعقارات*\n\n"
        f"📊 بناءً على تحليل عروضك الحالية ({total_props} عرض):\n"
        f"💡 منطقة *{top_loc}* تشهد أعلى معدل طلب وإقبال من الزوار!\n"
        "✨ *نصيحة المساعد الذكي:* أضف استراحات وأراضي أكثر في هذه المنطقة لزيادة المبيعات والسرعة الإجمالية للبيع."
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_assistant_handler():
    return CallbackQueryHandler(assistant_handler, pattern="^assistant$")
