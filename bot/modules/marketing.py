from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties
from utils.helpers import format_number, format_currency

async def marketing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    active_props = [p for p in properties if p.get("status") == "active"]

    if not active_props:
        text = "🎬 *استوديو التسويق:*\n\nلا توجد عروض نشطة حالياً لإنشاء محتوى تسويقي لها."
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    p = active_props[0]
    pid = p.get("id")
    ploc = p.get("location")
    parea = format_number(p.get("area", 0))
    pprice = format_currency(p.get("price", 0))
    plink = p.get("property_link", "")

    sample_post = (
        "🎬 *استوديو التسويق - صيغة إعلان مميزة جاهزة للنشر*\n\n"
        f"🔥 *فرصة عقارية ممتازة في {ploc}!*\n\n"
        f"🏡 عقار رقم: `{pid}`\n"
        f"📐 المساحة: {parea} م²\n"
        f"📍 الموقع: {ploc}\n"
        f"💰 السعر المطلوب: {pprice}\n\n"
        f"🔗 *التفاصيل الكاملة وحجز المعاينة:*\n{plink}\n\n"
        "📞 للاتصال والاستفسار: 0544699933 | واتساب: 0545888931\n"
        "🏛️ *آفاق الإنجاز للخدمات العقارية*"
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(sample_post, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(sample_post, reply_markup=reply_markup, parse_mode="Markdown")

def get_marketing_handler():
    return CallbackQueryHandler(marketing_handler, pattern="^marketing$")
