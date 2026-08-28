from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

async def notifications_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = (
        "🔔 *نظام الإشعارات والتنبيهات الفورية*\n\n"
        "🔴 [عاجل] طلب زائر جديد لعقار استراحة الهياثم.\n"
        "🟡 [مهم] استفسار لم يتم الرد عليه منذ ساعتين.\n"
        "🟢 [عادي] تم تحديث أسعار البوصلة العقارية بنجاح."
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_notifications_handler():
    return CallbackQueryHandler(notifications_handler, pattern="^notifications$")
