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
from utils.price_utils import parse_price_input, format_price_ar, format_price_en

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

CANCEL_BUTTON = [InlineKeyboardButton("❌ إلغاء", callback_data="action_cancel")]

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
    per_page = 6
    total_pages = (len(areas) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))

    start_idx = page * per_page
    page_areas = areas[start_idx:start_idx + per_page]

    keyboard = []
    row = []
    for area in page_areas:
        row.append(InlineKeyboardButton(f"{format_number(area)} م²", callback_data=f"area_val_{area}"))
        if len(row) == 3:
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
    keyboard.append(CANCEL_BUTTON)
    return InlineKeyboardMarkup(keyboard)

async def start_add_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    context.user_data.clear()
    context.user_data["property"] = {"features": {}, "photos": []}

    keyboard = [
        [
            InlineKeyboardButton("🏡 أرض سكنية", callback_data="type_land"),
            InlineKeyboardButton("🏠 استراحة", callback_data="type_resthouse"),
            InlineKeyboardButton("🚜 مزرعة", callback_data="type_farm")
        ],
        CANCEL_BUTTON
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "📍 *الخطوة 1: اختر نوع العقار*"

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

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
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append(CANCEL_BUTTON)
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
        [
            InlineKeyboardButton("شارع واحد", callback_data="streets_1"),
            InlineKeyboardButton("شارعين", callback_data="streets_2"),
            InlineKeyboardButton("أكثر من شارعين", callback_data="streets_3+")
        ],
        CANCEL_BUTTON
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
            ("land_kind", "نوع الأرض", [("فضاء", "فضاء"), ("أرض مسورة أو فضاء", "مسورة")]),
        ]
        if features.get("land_kind") in ["مسورة", "مصورة", "أرض مسورة أو فضاء"]:
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
        reply_markup = InlineKeyboardMarkup([CANCEL_BUTTON])
        await query.edit_message_text(
            "💰 *الخطوة 6: أدخل السعر بالريال*\n\n(مثال: 425000)",
            reply_markup=reply_markup,
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

    keyboard.append(CANCEL_BUTTON)
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
    raw_text = update.message.text or ""
    price = parse_price_input(raw_text) or validate_price(raw_text)
    if not price or price <= 0:
        reply_markup = InlineKeyboardMarkup([CANCEL_BUTTON])
        await update.message.reply_text("❌ سعر غير صحيح. الرجاء إدخال رقم موجب (مثال: 425000 أو ٤٢٥٠٠٠):", reply_markup=reply_markup)
        return ENTERING_PRICE

    context.user_data["property"]["price"] = price
    price_ar = format_price_ar(price)
    price_en = format_price_en(price)

    reply_markup = InlineKeyboardMarkup([CANCEL_BUTTON])
    await update.message.reply_text(
        f"✅ تم تحديد السعر:\n"
        f"• بالعربية: {price_ar}\n"
        f"• بالإنجليزية: {price_en}\n\n"
        f"📸 *الخطوة 7: قم برفع صور العقار (1 - 5 صور)*\n\nأرسل الصور واحدة تلو الأخرى، ثم أرسل كلمة *تم* أو *انتهاء* أو اكتب /done عند الانتهاء.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return UPLOADING_PHOTOS

async def handle_photo_upload_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data["property"].get("photos", [])
    finish_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تم الانتهاء", callback_data="photos_done")],
        CANCEL_BUTTON
    ])

    if update.message and update.message.photo:
        if len(photos) >= 5:
            await update.message.reply_text("⚠️ وصلت للحد الأقصى للصور (5 صور). اضغط [✅ تم الانتهاء] للمتابعة.", reply_markup=finish_kb)
            return UPLOADING_PHOTOS
        file_id = update.message.photo[-1].file_id
        photos.append(file_id)
        context.user_data["property"]["photos"] = photos
        await update.message.reply_text(f"✅ تم استلام الصورة ({len(photos)}/5). أرسل المزيد أو اضغط [✅ تم الانتهاء].", reply_markup=finish_kb)
        return UPLOADING_PHOTOS

    if update.message and update.message.text:
        raw_text = update.message.text.strip().lstrip("/")
        norm_txt = raw_text.lower()
        if norm_txt in {"done", "تم", "انتهاء", "انتهى"}:
            return await finish_photo_upload(update, context)
        elif norm_txt in {"إلغاء", "cancel"}:
            return await cancel_add_property(update, context)
        else:
            await update.message.reply_text("📸 الرجاء رفع صور العقار أو إرسال كلمة *تم* / */done* لإتمام الإضافة.", reply_markup=finish_kb, parse_mode="Markdown")
            return UPLOADING_PHOTOS

    if update.callback_query and update.callback_query.data == "photos_done":
        await update.callback_query.answer()
        return await finish_photo_upload(update, context)

    return UPLOADING_PHOTOS

async def finish_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data["property"].get("photos", [])
    if not photos:
        reply_markup = InlineKeyboardMarkup([CANCEL_BUTTON])
        if update.message:
            await update.message.reply_text("⚠️ يجب إضافة صورة واحدة على الأقل. قم برفع صورة:", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text("⚠️ يجب إضافة صورة واحدة على الأقل. قم برفع صورة:", reply_markup=reply_markup)
        return UPLOADING_PHOTOS

    return await show_preview(update, context)

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prop = context.user_data["property"]
    type_labels = {"land": "🏡 أرض سكنية", "resthouse": "🏠 استراحة", "farm": "🚜 مزرعة"}

    text = (
        "🏠 *معاينة العرض:*\n\n"
        f"🏡 *النوع:* {type_labels.get(prop.get('type'), prop.get('type'))}\n"
        f"📐 *المساحة:* {format_number(prop.get('area'))} م²\n"
        f"📍 *المنطقة:* {prop.get('location')}\n"
        f"💰 *السعر:* {format_number(prop.get('price'))} ريال\n"
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

    # Extract telegram photo URLs if possible
    photo_urls = []
    bot_token = os.environ.get("BOT_TOKEN")
    for file_id in prop.get("photos", []):
        try:
            tg_file = await context.bot.get_file(file_id)
            if tg_file and tg_file.file_path:
                if tg_file.file_path.startswith("http"):
                    photo_urls.append(tg_file.file_path)
                elif bot_token:
                    photo_urls.append(f"https://api.telegram.org/file/bot{bot_token}/{tg_file.file_path}")
        except Exception:
            pass

    prop["id"] = new_id
    prop["status"] = status
    prop["video_url"] = None
    prop["is_vip"] = False
    prop["photo_urls"] = photo_urls
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
    context.user_data.clear()
    msg_text = "🔄 تم الإلغاء"
    if update.message:
        await update.message.reply_text(msg_text)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg_text)
    return ConversationHandler.END

def get_add_property_handler():
    common_handlers = [
        MessageHandler(filters.Regex("إلغاء") | filters.Regex("❌ إلغاء"), cancel_add_property),
        CallbackQueryHandler(cancel_add_property, pattern="^(cancel|action_cancel)$"),
        MessageHandler(filters.Regex("إضافة عرض جديد") | filters.Regex("اضافة عرض جديد"), start_add_property)
    ]

    return ConversationHandler(
        conversation_timeout=900,
        entry_points=[
            CallbackQueryHandler(start_add_property, pattern="^(add_prop|add_property)$"),
            CommandHandler("add_property", start_add_property),
            MessageHandler(filters.Regex("إضافة عرض جديد") | filters.Regex("اضافة عرض جديد"), start_add_property)
        ],
        states={
            SELECTING_TYPE: [
                CallbackQueryHandler(select_type, pattern="^type_"),
                *common_handlers
            ],
            SELECTING_AREA: [
                CallbackQueryHandler(handle_area_callback, pattern="^area_"),
                *common_handlers
            ],
            SELECTING_LOCATION: [
                CallbackQueryHandler(select_location, pattern="^loc_"),
                *common_handlers
            ],
            SELECTING_STREETS: [
                CallbackQueryHandler(select_streets, pattern="^streets_"),
                *common_handlers
            ],
            SELECTING_FEATURES: [
                CallbackQueryHandler(handle_feature_callback, pattern="^featval_"),
                *common_handlers
            ],
            ENTERING_PRICE: [
                *common_handlers,
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input)
            ],
            UPLOADING_PHOTOS: [
                *common_handlers,
                CallbackQueryHandler(handle_photo_upload_step, pattern="^photos_done$"),
                MessageHandler(filters.PHOTO | filters.TEXT | filters.COMMAND, handle_photo_upload_step)
            ],
            PREVIEW: [
                CallbackQueryHandler(handle_preview_action, pattern="^action_"),
                *common_handlers
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_add_property),
            MessageHandler(filters.Regex("إلغاء") | filters.Regex("❌ إلغاء"), cancel_add_property),
            CallbackQueryHandler(cancel_add_property, pattern="^(cancel|action_cancel)$")
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
