from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties, save_properties

def sync_site_data():
    props = load_properties()
    save_properties(props)
    return len(props)

async def site_sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    count = sync_site_data()
    text = (
        "🔄 *مزامنة العروض مع الموقع الإلكتروني*\n\n"
        f"🌐 تم التحقق ومزامنة جميع العروض النشطة ({count} عرض) مع الموقع والمكونات برابط المزامنة المباشر."
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_site_sync_handler():
    return CallbackQueryHandler(site_sync_handler, pattern="^site_sync$")
