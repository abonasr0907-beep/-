from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties

async def reports_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    text = (
        "📈 *التقرير الأسبوعي للأداء والتسويق*\n\n"
        f"📊 عدد العروض الكلية: {len(properties)}\n"
        "🎯 نسبة التفاعل مع الموقع: +24%\n"
        "📞 أكثر العقارات طلباً هذا الأسبوع: الأراضي السكنية بالرحمانية والهياثم."
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_reports_handler():
    return CallbackQueryHandler(reports_handler, pattern="^reports$")
