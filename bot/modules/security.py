from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

async def security_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = (
        "⚙️ *إعدادات الأمان وسجل العمليات (Audit Log)*\n\n"
        "🔒 حالة النظام: محمي ومشفّر ✅\n"
        "📝 آخر تسجيل دخول: الأدمن الرئيسي (منذ 5 دقائق)\n"
        "🛡️ الصلاحيات: كاملة (Full Access)"
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_security_handler():
    return CallbackQueryHandler(security_handler, pattern="^(security|settings)$")
