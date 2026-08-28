from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

async def follow_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = (
        "📞 *المتابعة التلقائية للعملاء والزوار*\n\n"
        "⏰ *تذكيرات المتابعة اليومية:*\n"
        "1. 📞 تابع مع العميل: (أبو فهد - 0540000000) - مضى 3 أيام على الاستفسار.\n"
        "2. ⚠️ عميل محتمل لم يتحول: (استراحة العفجة) - مضى أسبوع."
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_follow_up_handler():
    return CallbackQueryHandler(follow_up_handler, pattern="^follow_up$")
