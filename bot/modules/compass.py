from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.config import COMPASS_FILE, LOCATIONS
from bot.database import load_properties, load_json, save_json
from utils.helpers import format_currency, format_number

def calculate_compass_data():
    properties = load_properties()
    compass = {}

    for loc in LOCATIONS:
        loc_props = [p for p in properties if p.get("location") == loc and p.get("price") and p.get("area")]
        if loc_props:
            total_price = sum(p["price"] for p in loc_props)
            total_area = sum(p["area"] for p in loc_props)
            avg_meter_price = int(total_price / total_area) if total_area > 0 else 0
            compass[loc] = {
                "avg_sqm_price": avg_meter_price,
                "count": len(loc_props),
                "updated_at": datetime.now().isoformat()
            }
        else:
            compass[loc] = {
                "avg_sqm_price": 0,
                "count": 0,
                "updated_at": datetime.now().isoformat()
            }

    save_json(COMPASS_FILE, compass)
    return compass

async def compass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    compass = calculate_compass_data()

    text = "🧭 *البوصلة العقارية - متوسط سعر المتر حسب المنطقة*\n\n"
    for loc, data in compass.items():
        avg = data.get("avg_sqm_price", 0)
        cnt = data.get("count", 0)
        if avg > 0:
            text += f"📍 *{loc}:* {format_number(avg)} ريال/م² (العروض: {cnt})\n"
        else:
            text += f"📍 *{loc}:* غير متوفر بيانات رسمية\n"

    keyboard = [
        [InlineKeyboardButton("🔄 تحديث يدوي للبوصلة", callback_data="refresh_compass")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def refresh_compass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ تم تحديث بيانات البوصلة العقارية بنجاح!", show_alert=True)
    await compass_handler(update, context)

def get_compass_handler():
    return CallbackQueryHandler(compass_handler, pattern="^compass$")
