from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, CommandHandler
)
from bot.database import get_property, update_property

SELECTING_PROPERTY, ENTERING_VIDEO_URL = range(2)

async def start_tour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = "🎥 *الجولة الافتراضية للفيديو*\n\nيرجى اختيار العرض المطلوب لربطه برابط فيديو (يوتيوب، تيك توك، إنستغرام، سناب شات)."
    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    return ConversationHandler.END

def get_tour_handler():
    return CallbackQueryHandler(start_tour, pattern="^tour$")
