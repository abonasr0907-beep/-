import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from bot.config import LOCATIONS
from bot.database import load_properties, save_properties
from utils.helpers import format_number, generate_property_link
from utils.validators import validate_price

# Conversation States (8 steps)
(
    SELECTING_TYPE,
    SELECTING_AREA,
    SELECTING_LOCATION,
    SELECTING_STREETS,
    SELECTING_FEATURES,
    ENTERING_PRICE,
    UPLOADING_PHOTOS,
    PREVIEW
) = range(8)

def get_area_ranges(prop_type):
    if prop_type == "land":
        res = list(range(200, 10000, 100))
        if 10000 not in res:
            res.append(10000)
        return res
    elif prop_type == "resthouse":
        res = list(range(250, 25000, 500))
        if 25000 not in res:
            res.append(25000)
        return res
    elif prop_type == "farm":
        res = list(range(10000, 190000, 100))
        if 190000 not in res:
            res.append(190000)
        return res
    return list(range(100, 1001, 100))

def build_area_keyboard(prop_type, page=0):
    areas = get_area_ranges(prop_type)
    per_page = 10
    total_pages = (len(areas) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))

    start_idx = page * per_page
    page_areas = areas[start_idx:start_idx + per_page]

    keyboard = []
    row = []
    for area in page_areas:
        row.append(InlineKeyboardButton(f"{format_number(area)} م²", callback_data=f"area_val_{area}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ السابق", callback_data=f"area_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="area_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("التالي ▶️", callback_data=f"area_page_{page + 1}"))

    keyboard.append(nav_row)
    return InlineKeyboardMarkup(keyboard)

async def start_add_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("🏡 أرض سكنية", callback_data="type_land")],
        [InlineKeyboardButton("🏠 استراحة", callback_data="type_resthouse")],
        [InlineKeyboardButton("🚜 مزرعة", callback_data="type_farm")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "📍 *الخطوة 1: اختر نوع العقار*"

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    context.user_data["property"] = {"features": {}, "photos": []}
    return SELECTING_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prop_type = query.data.replace("type_", "")
    context.user_data["property"]["type"] = prop_type
    context.user_data["area_page"] = 0

    reply_markup = build_area_keyboard(prop_type, page=0)
    await query.edit_message_text("📐 *الخطوة 2: اختر المساحة (م²)*", reply_markup=reply_markup, parse_mode="Markdown")
    return SELECTING_AREA

async def handle_area_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("area_page_"):
        page = int(data.replace("area_page_", ""))
        context.user_data["area_page"] = page
        prop_type = context.user_data["property"].get("type", "land")
        reply_markup = build_area_keyboard(prop_type, page=page)
        await query.edit_message_text("📐 *الخطوة 2: اختر المساحة (م²)*", reply_markup=reply_markup, parse_mode="Markdown")
        return SELECTING_AREA
    elif data.startswith("area_val_"):
        area = int(data.replace("area_val_", ""))
        context.user_data["property"]["area"] = area

        keyboard = []
        row = []
        for loc in LOCATIONS:
            row.append(InlineKeyboardButton(loc, callback_data=f"loc_{loc}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📍 *الخطوة 3: اختر المنطقة*", reply_markup=reply_markup, parse_mode="Markdown")
        return SELECTING_LOCATION
    return SELECTING_AREA

async def select_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    location = query.data.replace("loc_", "")
    context.user_data["property"]["location"] = location

    keyboard = [
        [InlineKeyboardButton("شارع واحد", callback_data="streets_1")],
        [InlineKeyboardButton("شارعين", callback_data="streets_2")],
        [InlineKeyboardButton("أكثر من شارعين", callback_data="streets_3+")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🛣️ *الخطوة 4: اختر عدد الشوارع*", reply_markup=reply_markup, parse_mode="Markdown")
    return SELECTING_STREETS

async def select_streets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    streets = query.data.replace("streets_", "")
    context.user_data["property"]["streets"] = streets
    context.user_data["feature_step"] = 0

    return await render_feature_step(query, context)

def get_feature_steps(prop_type, features):
    if prop_type == "land":
        steps = [
            ("land_kind", "نوع الأرض", [("فضاء", "فضاء"), ("مصورة", "مصورة")]),
        ]
        if features.get("land_kind") == "مصورة":
            steps.extend([
                ("facade", "الواجهة", [("شرقية", "شرقية"), ("شمالية", "شمالية"), ("جنوبية", "جنوبية"), ("غربية", "غربية")]),
                ("electricity", "عداد كهرباء", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
                ("water_tank", "خزان مياه", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
                ("well", "بئر", [("نعم ✅", "نعم"), ("لا ❌", "لا")])
            ])
        return steps
    elif prop_type == "resthouse":
        return [
            ("pool", "مسبح", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("green_areas", "مسطحات خضراء", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("fruit_trees", "أشجار مثمرة", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("building_finish", "مبنى مشطب", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("building_type", "نوع المبنى", [("عادي", "عادي"), ("VIP", "VIP")]),
            ("guard_room", "غرف حارس", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("parking", "موقف سيارات", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("majlis_count", "عدد المجالس", [(str(i), str(i)) for i in range(1, 11)]),
            ("bedrooms_count", "عدد غرف النوم", [(str(i), str(i)) for i in range(1, 11)]),
            ("tents_count", "عدد الخيم", [(str(i), str(i)) for i in range(1, 21)]),
            ("kitchens_count", "عدد المطابخ", [(str(i), str(i)) for i in range(1, 6)])
        ]
    elif prop_type == "farm":
        return [
            ("trees_count", "عدد الأشجار", [(str(i), str(i)) for i in range(50, 301, 10)]),
            ("facade", "الواجهة", [("شرقية", "شرقية"), ("شمالية", "شمالية"), ("جنوبية", "جنوبية"), ("غربية", "غربية")]),
            ("fenced", "مسيفة", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("greenhouses_count", "بيوت محمية", [(str(i), str(i)) for i in range(10, 251, 10)]),
            ("tanks_count", "عدد الخزانات", [(str(i), str(i)) for i in range(1, 11)]),
            ("wells_count", "عدد الآبار", [(str(i), str(i)) for i in range(1, 11)]),
            ("plots_count", "عدد القطعات", [(str(i), str(i)) for i in range(1, 51)]),
            ("sprinkler", "رشاش", [("نعم ✅", "نعم"), ("لا ❌", "لا")]),
            ("design", "تصميم", [("عادي", "عادي"), ("VIP", "VIP")]),
            ("bedrooms_count", "غرف النوم", [(str(i), str(i)) for i in range(1, 11)]),
            ("internal_resthouses", "استراحات داخلية", [(str(i), str(i)) for i in range(1, 6)]),
            ("majlis_count", "مجالس", [(str(i), str(i)) for i in range(1, 6)])
        ]
    return []

async def render_feature_step(query, context):
    prop_type = context.user_data["property"].get("type")
    step = context.user_data.get("feature_step", 0)
    features = context.user_data["property"].get("features", {})

    steps = get_feature_steps(prop_type, features)

    if step >= len(steps):
        await query.edit_message_text(
            "💰 *الخطوة 6: أدخل السعر بالريال*\n\n(مثال: 425000)",
            parse_mode="Markdown"
        )
        return ENTERING_PRICE

    key, title, options = steps[step]
    keyboard = []
    row = []
    for label, val in options:
        row.append(InlineKeyboardButton(label, callback_data=f"featval_{key}:{val}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"✨ *الخطوة 5: المميزات - {title}*", reply_markup=reply_markup, parse_mode="Markdown")
    return SELECTING_FEATURES

async def handle_feature_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.replace("featval_", "")
    parts = data.split(":", 1)
    if len(parts) == 2:
        key, val = parts
        context.user_data["property"]["features"][key] = val

    context.user_data["feature_step"] = context.user_data.get("feature_step", 0) + 1
    return await render_feature_step(query, context)

async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = validate_price(update.message.text)
    if not price:
        await update.message.reply_text("❌ سعر غير صحيح. الرجاء إدخال رقم موجب (مثال: 425000):")
        return ENTERING_PRICE

    context.user_data["property"]["price"] = price
    await update.message.reply_text(
        "📸 *الخطوة 7: قم برفع صور العقار (1 - 5 صور)*\n\nأرسل الصور واحدة تلو الأخرى، ثم اكتب /done عند الانتهاء.",
        parse_mode="Markdown"
    )
    return UPLOADING_PHOTOS

async def handle_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data["property"].get("photos", [])
    if len(photos) >= 5:
        await update.message.reply_text("⚠️ وصلت للحد الأقصى للصور (5 صور). اكتب /done للمتابعة.")
        return UPLOADING_PHOTOS

    file_id = update.message.photo[-1].file_id
    photos.append(file_id)
    context.user_data["property"]["photos"] = photos

    await update.message.reply_text(f"✅ تم استلام الصورة ({len(photos)}/5). أرسل المزيد أو اكتب /done للإنهاء.")
    return UPLOADING_PHOTOS

async def finish_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data["property"].get("photos", [])
    if not photos:
        await update.message.reply_text("⚠️ يجب إضافة صورة واحدة على الأقل. قم برفع صورة:")
        return UPLOADING_PHOTOS

    return await show_preview(update, context)

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prop = context.user_data["property"]
    type_labels = {"land": "🏡 أرض سكنية", "resthouse": "🏠 استراحة", "farm": "🚜 مزرعة"}

    features_str = "\n".join([f"• {k}: {v}" for k, v in prop.get("features", {}).items()]) or "لا يوجد"

    text = (
        "📋 *الخطوة 8: معاينة العرض قبل النشر:*\n\n"
        f"🏡 *النوع:* {type_labels.get(prop.get('type'), prop.get('type'))}\n"
        f"📐 *المساحة:* {format_number(prop.get('area'))} م²\n"
        f"📍 *المنطقة:* {prop.get('location')}\n"
        f"🛣️ *عدد الشوارع:* {prop.get('streets')}\n"
        f"💰 *السعر:* {format_number(prop.get('price'))} ريال\n\n"
        f"✨ *المميزات:*\n{features_str}\n\n"
        f"📸 *عدد الصور:* {len(prop.get('photos', []))}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ نشر", callback_data="action_publish"),
            InlineKeyboardButton("💾 مسودة", callback_data="action_draft"),
            InlineKeyboardButton("❌ إلغاء", callback_data="action_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    photos = prop.get("photos", [])
    if photos and update.message:
        try:
            media = [InputMediaPhoto(media=pid) for pid in photos[:5]]
            await update.message.reply_media_group(media=media)
        except Exception:
            pass

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    return PREVIEW

async def handle_preview_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data.replace("action_", "")
    if action == "cancel":
        await query.edit_message_text("❌ تم إلغاء إضافة العرض.")
        return ConversationHandler.END

    status = "active" if action == "publish" else "draft"
    properties = load_properties()

    new_id = f"PROP-{len(properties) + 1:010d}"
    prop = context.user_data["property"]
    prop["id"] = new_id
    prop["status"] = status
    prop["video_url"] = None
    prop["is_vip"] = False
    prop["created_at"] = datetime.now().isoformat()
    prop["archived_at"] = None
    prop["property_link"] = generate_property_link(new_id)

    properties.append(prop)
    save_properties(properties)

    msg = "🎉 *تم نشر العرض بنجاح!*" if action == "publish" else "💾 *تم حفظ العرض كمسودة.*"
    link_text = f"\n🔗 [عرض العقار في الموقع]({prop['property_link']})" if action == "publish" else ""
    await query.edit_message_text(
        f"{msg}\n\n🆔 رقم العرض: `{new_id}`{link_text}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel_add_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("❌ تم إلغاء العملية.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

def get_add_property_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_property, pattern="^(add_prop|add_property)$"),
            CommandHandler("add_property", start_add_property),
            MessageHandler(filters.Regex("^➕ إضافة عرض جديد$"), start_add_property)
        ],
        states={
            SELECTING_TYPE: [CallbackQueryHandler(select_type, pattern="^type_")],
            SELECTING_AREA: [CallbackQueryHandler(handle_area_callback, pattern="^area_")],
            SELECTING_LOCATION: [CallbackQueryHandler(select_location, pattern="^loc_")],
            SELECTING_STREETS: [CallbackQueryHandler(select_streets, pattern="^streets_")],
            SELECTING_FEATURES: [CallbackQueryHandler(handle_feature_callback, pattern="^featval_")],
            ENTERING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input)],
            UPLOADING_PHOTOS: [
                MessageHandler(filters.PHOTO, handle_photo_upload),
                CommandHandler("done", finish_photo_upload)
            ],
            PREVIEW: [CallbackQueryHandler(handle_preview_action, pattern="^action_")]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_add_property),
            CallbackQueryHandler(cancel_add_property, pattern="^action_cancel$")
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
