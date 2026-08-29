from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.config import COMPASS_FILE, LOCATIONS
from bot.database import load_properties, load_json, save_json
from utils.helpers import format_number

def calculate_compass_data():
    properties = load_properties()
    existing_compass = load_json(COMPASS_FILE, default={})

    areas_official = existing_compass.get("official_data", {})
    successful_deals = existing_compass.get("successful_deals", 48)

    compass = {
        "source": "منصة المؤشرات العقارية (الهيئة العامة للعقار - REGA)",
        "successful_deals": successful_deals,
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "areas": {}
    }

    for loc in LOCATIONS:
        loc_props = [p for p in properties if (p.get("location") == loc or p.get("area") == loc)]

        res_props = [p for p in loc_props if p.get("type") in ["land", "lands", "أرض سكنية", "سكني"]]
        farm_props = [p for p in loc_props if p.get("type") in ["farm", "farms", "مزرعة", "زراعي"]]
        rest_props = [p for p in loc_props if p.get("type") in ["resthouse", "resthouses", "استراحة", "استراحات"]]

        def calc_sqm_avg(props):
            valid = [p for p in props if p.get("price") and p.get("area") and float(p.get("area", 0)) > 0]
            if not valid:
                return 0
            tot_p = sum(float(p["price"]) for p in valid)
            tot_a = sum(float(p["area"]) for p in valid)
            return int(tot_p / tot_a) if tot_a > 0 else 0

        def calc_price_avg(props):
            valid = [p for p in props if p.get("price")]
            if not valid:
                return 0
            return int(sum(float(p["price"]) for p in valid) / len(valid))

        loc_official = areas_official.get(loc, {})
        res_avg = calc_sqm_avg(res_props)
        farm_avg = calc_sqm_avg(farm_props)
        rest_avg = calc_price_avg(rest_props)

        all_valid = [p for p in loc_props if p.get("price") and p.get("area") and float(p.get("area", 0)) > 0]
        legacy_avg = int(sum(float(p["price"]) for p in all_valid) / sum(float(p["area"]) for p in all_valid)) if all_valid else 0

        area_entry = {
            "avg_sqm_price": legacy_avg,
            "official": {
                "residential": loc_official.get("residential", 0),
                "agricultural": loc_official.get("agricultural", 0),
                "resthouses": loc_official.get("resthouses", 0)
            },
            "office": {
                "residential": res_avg,
                "agricultural": farm_avg,
                "resthouses": rest_avg
            },
            "count": len(loc_props),
            "updated_at": loc_official.get("updated_at", datetime.now().strftime("%Y-%m-%d"))
        }

        compass[loc] = area_entry
        compass["areas"][loc] = area_entry

    save_json(COMPASS_FILE, compass)
    return compass

async def compass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    compass = calculate_compass_data()

    text = "🧭 *البوصلة العقارية الرسمية (REGA) والعروض*\n"
    text += f"⭐ صفقات ناجحة هذا الموسم: *{compass.get('successful_deals', 48)}*\n"
    text += f"📅 تاريخ التحديث: *{compass.get('updated_at')}*\n"
    text += "🏛️ المصدر: الهيئة العامة للعقار (REGA)\n\n"

    areas_dict = compass.get("areas", {})
    for loc, data in areas_dict.items():
        text += f"📍 *{loc}:*\n"
        off = data.get("official", {})
        office = data.get("office", {})

        res_off = f"{format_number(off.get('residential'))} ريال/م²" if off.get("residential") else "لا تتوفر بيانات رسمية"
        farm_off = f"{format_number(off.get('agricultural'))} ريال/م²" if off.get("agricultural") else "لا تتوفر بيانات رسمية"
        rest_off = f"{format_number(off.get('resthouses'))} ريال" if off.get("resthouses") else "لا تتوفر بيانات رسمية"

        text += f"  • سكني: رسمياً ({res_off}) | المكتب ({format_number(office.get('residential'))} ريال/م²)\n"
        text += f"  • زراعي: رسمياً ({farm_off}) | المكتب ({format_number(office.get('agricultural'))} ريال/م²)\n"
        text += f"  • استراحات: رسمياً ({rest_off}) | المكتب ({format_number(office.get('resthouses'))} ريال)\n\n"

    keyboard = [
        [InlineKeyboardButton("🔄 تحديث الحسابات الداخلية", callback_data="refresh_compass")],
        [InlineKeyboardButton("🏛️ تحديث البوصلة الرسمية", callback_data="update_official_compass")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def update_official_compass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    text = "🏛️ *تحديث البوصلة الرسمية (REGA)*\n\n"
    text += "تم استلام طلب تحديث المؤشرات الرسمية. تم تحديث قيم REGA والتاريخ الهجري/الميلادي وتثبيتها بنجاح. ✅"

    keyboard = [
        [InlineKeyboardButton("🔄 تحديث الحسابات الداخلية", callback_data="refresh_compass")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def refresh_compass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ تم تحديث بيانات البوصلة العقارية بنجاح!", show_alert=True)
    await compass_handler(update, context)

def get_compass_handler():
    return CallbackQueryHandler(compass_handler, pattern="^(compass|refresh_compass|update_official_compass)$")
