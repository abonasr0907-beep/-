from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties

async def pricing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    text = "🏷️ *نظام التسعير الذكي والمقارنة*\n\n"

    if properties:
        p = properties[0]
        text += (
            f"🏡 العرض الحالي: `{p.get('id')}` ({p.get('location')})\n"
            f"💰 السعر الحالي: {p.get('price')} ريال\n"
            "📈 مقترحات الذكاء الاصطناعي: السعر مناسب ومنافس لمتوسط أسعار المنطقة."
        )
    else:
        text += "لا توجد عروض حالية للمقارنة والتسعير الذكي."

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_pricing_handler():
    return CallbackQueryHandler(pricing_handler, pattern="^pricing$")
