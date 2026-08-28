import os
import json
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List
from pydantic import BaseModel

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, InputMediaVideo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

# ============ الإعدادات ============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", "8080"))

DATA_FILE = "data/properties.json"
PHOTOS_DIR = "data/photos"

os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)

# ============ حالات المحادثة ============
(
    SELECTING_TYPE,      # اختيار نوع العقار
    SELECTING_LOCATION,  # اختيار الموقع
    ENTERING_AREA,       # إدخال المساحة
    ENTERING_PRICE,      # إدخال السعر
    SELECTING_STREETS,   # اختيار عدد الشوارع
    SELECTING_FACADE,    # اختيار الواجهة
    SELECTING_FEATURES,  # اختيار المميزات (أزرار متعددة)
    ENTERING_DESCRIPTION,# إدخال الوصف
    UPLOADING_PHOTOS,    # رفع الصور
    ENTERING_VIDEO       # رفع الفيديو
) = range(10)

# ============ القواميس ============
TYPE_NAMES = {
    "farms": "🌾 مزرعة",
    "resthouses": "🏠 استراحة",
    "lands": "🗺️ أرض سكنية"
}

FEATURE_NAMES = {
    "water": "💧 ماء",
    "electricity": "⚡ كهرباء",
    "well": "🕳️ بئر",
    "mosque": "🕌 مسجد",
    "school": "🏫 مدرسة",
    "market": "🛒 سوق",
    "fence": "🧱 سور كامل",
    "palm": "🌴 نخيل",
    "olive": "🫒 زيتون",
    "citrus": "🍊 حمضيات",
    "pool": "🏊 مسبح",
    "garden": "🌳 حديقة",
    "paved": "🛤️ طرق معبدة",
    "warehouse": "🏭 مستودع",
    "house": "🏡 بيت",
    "cameras": "📹 كاميرات مراقبة"
}

# ============ دوال المساعدة ============
def normalize_property(p, idx=1):
    """توحيد هيكلية العقار لتحقيق التوافق التام"""
    if not isinstance(p, dict):
        return None

    # تحويل ID إلى عدد صحيح أو رقم مميز
    raw_id = p.get("id")
    if isinstance(raw_id, str) and raw_id.startswith("PROP-"):
        try:
            prop_id = int(raw_id.replace("PROP-", ""))
        except ValueError:
            prop_id = idx
    elif isinstance(raw_id, int):
        prop_id = raw_id
    else:
        prop_id = idx

    # توحيد النوع
    ptype = p.get("type", "lands")
    if ptype in ["مزرعة", "farm"]:
        ptype = "farms"
    elif ptype in ["استراحة", "resthouse"]:
        ptype = "resthouses"
    elif ptype in ["أرض", "land"]:
        ptype = "lands"

    # توحيد المساحة
    area_val = p.get("area", p.get("size_sqm", 0))
    try:
        area = int(area_val)
    except (ValueError, TypeError):
        area = 0

    # توحيد السعر
    price_val = p.get("price", 0)
    try:
        price = int(price_val)
    except (ValueError, TypeError):
        price = 0

    # توحيد باقي الحقول
    streets = str(p.get("streets", "1"))
    facade = p.get("facade", p.get("facing", "غير محدد"))
    features = p.get("features", [])
    if not isinstance(features, list):
        features = []

    description = p.get("description", "")
    photos = p.get("photos", p.get("images", []))
    if not isinstance(photos, list):
        photos = []

    video = p.get("video", None)
    date_str = p.get("date", p.get("date_added", datetime.now().isoformat()))
    status = p.get("status", "active")

    return {
        "id": prop_id,
        "type": ptype,
        "location": p.get("location", "غير محدد"),
        "area": area,
        "price": price,
        "streets": streets,
        "facade": facade,
        "features": features,
        "description": description,
        "photos": photos,
        "video": video,
        "date": date_str,
        "status": status
    }

def load_properties():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_list = []
                if isinstance(data, dict) and "properties" in data:
                    raw_list = data["properties"]
                elif isinstance(data, list):
                    raw_list = data

                normalized = []
                for i, p in enumerate(raw_list, start=1):
                    norm = normalize_property(p, i)
                    if norm:
                        normalized.append(norm)
                return normalized
        except Exception as e:
            print(f"Error loading properties: {e}")
    return []

def save_properties(properties):
    normalized = []
    for i, p in enumerate(properties, start=1):
        norm = normalize_property(p, i)
        if norm:
            normalized.append(norm)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"properties": normalized}, f, ensure_ascii=False, indent=2)

def migrate_properties():
    """هجرة البيانات القديمة تلقائياً إلى الهيكل الموحد"""
    props = load_properties()
    if props:
        save_properties(props)
        print("✅ تم هجرة وتوحيد قاعدة البيانات بنجاح")

def add_demo_properties():
    """إضافة عقارات تجريبية إذا كان الملف فارغاً"""
    if not os.path.exists(DATA_FILE) or len(load_properties()) == 0:
        demo = [
            {
                "id": 1,
                "type": "farms",
                "location": "الرحمانية",
                "area": 10000,
                "price": 1200000,
                "streets": "2",
                "facade": "شمال",
                "features": ["water", "electricity", "well", "palm"],
                "description": "مزرعة زراعية كاملة ببئر ارتوازي ونخيل",
                "photos": [],
                "video": None,
                "date": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": 2,
                "type": "resthouses",
                "location": "الهياثم",
                "area": 2500,
                "price": 850000,
                "streets": "1",
                "facade": "جنوب",
                "features": ["water", "electricity", "pool", "fence"],
                "description": "استراحة فاخرة مع مسبح وحديقة",
                "photos": [],
                "video": None,
                "date": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": 3,
                "type": "lands",
                "location": "الدلم",
                "area": 600,
                "price": 180000,
                "streets": "2",
                "facade": "شمالية شرقية",
                "features": ["water", "electricity", "paved"],
                "description": "أرض سكنية في مخطط الدلم",
                "photos": [],
                "video": None,
                "date": datetime.now().isoformat(),
                "status": "active"
            }
        ]
        save_properties(demo)
        print("✅ تم إضافة 3 عقارات تجريبية")

# ============ معالجات القائمة الرئيسية ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """القائمة الرئيسية - 3 أزرار"""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة عقار جديد", callback_data="add_property")],
        [InlineKeyboardButton("📋 قائمة العقارات", callback_data="list_properties")],
        [InlineKeyboardButton("🔄 تهيئة البيانات", callback_data="reset_data")],
    ]
    text = (
        "🏡 بوت مكتب آفاق الإنجاز العقاري\n\n"
        "يمكنك من خلال هذا البوت:\n"
        "• إضافة عقارات جديدة\n"
        "• عرض قائمة العقارات\n"
        "• إدارة البيانات\n\n"
        "اختر إحدى الخيارات:"
    )
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def reset_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """زر تهيئة البيانات - طلب تأكيد"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("✅ نعم، احذف الكل", callback_data="confirm_reset"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_reset")
        ],
    ]
    await query.edit_message_text(
        "⚠️ تحذير!\n\nهل أنت متأكد من حذف جميع العقارات والصور؟\n"
        "هذا الإجراء لا يمكن التراجع عنه.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد الحذف"""
    query = update.callback_query
    await query.answer()
    save_properties([])
    # حذف الصور
    if os.path.exists(PHOTOS_DIR):
        for f in os.listdir(PHOTOS_DIR):
            try:
                os.remove(os.path.join(PHOTOS_DIR, f))
            except Exception:
                pass
    await query.edit_message_text("✅ تم حذف جميع البيانات بنجاح!", parse_mode="Markdown")

async def cancel_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء الحذف"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ تم الإلغاء.")

def safe_fmt_int(val):
    """تحويل وتنسيق الأرقام بأمان لتجنب استثناءات التنسيق"""
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)

async def list_properties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة العقارات"""
    query = update.callback_query
    await query.answer()
    properties = load_properties()
    if not properties:
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_menu")]]
        await query.edit_message_text(
            "📭 *لا توجد عقارات مسجلة.*\n\nاضغط إضافة عقار جديد لبدء التسجيل.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    text = "📋 *قائمة العقارات:*\n\n"
    for p in properties[-10:]:
        ptype = p.get('type', '')
        type_emoji = "🌾" if ptype == 'farms' else "🏠" if ptype == 'resthouses' else "🗺️"
        loc = p.get('location', 'غير محدد')
        price_str = safe_fmt_int(p.get('price', 0))
        area_str = safe_fmt_int(p.get('area', 0))
        text += f"#{p.get('id', '?')} {type_emoji} *{loc}*\n   💰 {price_str} ريال | 📏 {area_str} م²\n\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_menu")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للقائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ إضافة عقار جديد", callback_data="add_property")],
        [InlineKeyboardButton("📋 قائمة العقارات", callback_data="list_properties")],
        [InlineKeyboardButton("🔄 تهيئة البيانات", callback_data="reset_data")],
    ]
    await query.edit_message_text(
        "🏡 بوت مكتب آفاق الإنجاز العقاري\n\nاختر إحدى الخيارات:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============ خطوات إضافة العقار ============
async def start_add_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الخطوة 1: اختيار نوع العقار - 3 أزرار"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(TYPE_NAMES["farms"], callback_data="type_farms")],
        [InlineKeyboardButton(TYPE_NAMES["resthouses"], callback_data="type_resthouses")],
        [InlineKeyboardButton(TYPE_NAMES["lands"], callback_data="type_lands")],
    ]
    await query.edit_message_text(
        "🏡 *الخطوة 1 من 9*\n\nاختر نوع العقار:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECTING_TYPE

async def select_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الخطوة 2: اختيار الموقع - 5 أزرار"""
    query = update.callback_query
    await query.answer()
    property_type = query.data.replace("type_", "")
    context.user_data["property"] = {"type": property_type, "features": []}

    keyboard = [
        [InlineKeyboardButton("📍 الرحمانية", callback_data="loc_الرحمانية")],
        [InlineKeyboardButton("📍 الهياثم", callback_data="loc_الهياثم")],
        [InlineKeyboardButton("📍 الدلم", callback_data="loc_الدلم")],
        [InlineKeyboardButton("📍 الضبيعة", callback_data="loc_الضبيعة")],
        [InlineKeyboardButton("📍 العفجة", callback_data="loc_العفجة")],
    ]
    await query.edit_message_text(
        f"🏡 *الخطوة 2 من 9*\n\nالنوع: {TYPE_NAMES.get(property_type)}\n\nاختر الموقع:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECTING_LOCATION

async def enter_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الخطوة 3: إدخال المساحة"""
    query = update.callback_query
    await query.answer()
    location = query.data.replace("loc_", "")
    context.user_data["property"]["location"] = location

    await query.edit_message_text(
        f"🏡 *الخطوة 3 من 9*\n\n"
        f"النوع: {TYPE_NAMES.get(context.user_data['property']['type'])}\n"
        f"الموقع: {location}\n\n"
        f"📏 أدخل المساحة بالمتر المربع (مثال: *10000*):",
        parse_mode="Markdown"
    )
    return ENTERING_AREA

async def validate_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من المساحة"""
    text = update.message.text.strip().replace(",", "").replace("م²", "").replace("م", "")
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text(
            "❌ خطأ!\n\nالرجاء إدخال رقم صحيح فقط (مثال: 10000):",
            parse_mode="Markdown"
        )
        return ENTERING_AREA
    context.user_data["property"]["area"] = int(text)
    await update.message.reply_text(
        f"🏡 *الخطوة 4 من 9*\n\n"
        f"📏 المساحة: {int(text):,} م²\n\n"
        f"💰 أدخل السعر بالريال (مثال: *1200000*):",
        parse_mode="Markdown"
    )
    return ENTERING_PRICE

async def validate_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من السعر"""
    text = update.message.text.strip().replace(",", "").replace("ريال", "")
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text(
            "❌ خطأ!\n\nالرجاء إدخال رقم صحيح فقط (مثال: 1200000):",
            parse_mode="Markdown"
        )
        return ENTERING_PRICE
    context.user_data["property"]["price"] = int(text)

    keyboard = [
        [InlineKeyboardButton("1 شارع", callback_data="streets_1")],
        [InlineKeyboardButton("2 شارع", callback_data="streets_2")],
        [InlineKeyboardButton("3 شوارع", callback_data="streets_3")],
        [InlineKeyboardButton("4 شوارع", callback_data="streets_4")],
    ]
    await update.message.reply_text(
        f"🏡 *الخطوة 5 من 9*\n\n"
        f"💰 السعر: {int(text):,} ريال\n\n"
        f"🛣️ اختر عدد الشوارع:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECTING_STREETS

async def select_facade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الخطوة 6: اختيار الواجهة - 6 أزرار"""
    query = update.callback_query
    await query.answer()
    streets = query.data.replace("streets_", "")
    context.user_data["property"]["streets"] = streets

    keyboard = [
        [InlineKeyboardButton("🧭 شمال", callback_data="facade_شمال")],
        [InlineKeyboardButton("🧭 جنوب", callback_data="facade_جنوب")],
        [InlineKeyboardButton("🧭 شرق", callback_data="facade_شرق")],
        [InlineKeyboardButton("🧭 غرب", callback_data="facade_غرب")],
        [InlineKeyboardButton("🧭 شمالية شرقية", callback_data="facade_شمالية شرقية")],
        [InlineKeyboardButton("🧭 جنوبية غربية", callback_data="facade_جنوبية غربية")],
    ]
    await query.edit_message_text(
        f"🏡 *الخطوة 6 من 9*\n\n"
        f"🛣️ الشوارع: {streets}\n\n"
        f"🧭 اختر الواجهة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECTING_FACADE

async def show_features_menu(query, context):
    """عرض قائمة المميزات - 16 زر"""
    features = context.user_data["property"].get("features", [])
    keyboard = []
    row = []
    for key, name in FEATURE_NAMES.items():
        mark = "✅" if key in features else "⬜"
        row.append(InlineKeyboardButton(f"{mark} {name}", callback_data=f"feat_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ التالي", callback_data="feat_done")])

    selected = ", ".join([FEATURE_NAMES.get(f, f) for f in features]) or "لا شيء"

    await query.edit_message_text(
        f"🏡 *الخطوة 7 من 9*\n\n"
        f"✨ المميزات المختارة: *{selected}*\n\n"
        f"اختر المزيد أو اضغط التالي:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def select_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الخطوة 7: اختيار المميزات"""
    query = update.callback_query
    await query.answer()
    facade = query.data.replace("facade_", "")
    context.user_data["property"]["facade"] = facade

    await show_features_menu(query, context)
    return SELECTING_FEATURES

async def toggle_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبديل ميزة (إضافة/إزالة)"""
    query = update.callback_query
    await query.answer()
    if query.data == "feat_done":
        return await enter_description(update, context)

    feature = query.data.replace("feat_", "")
    features = context.user_data["property"].get("features", [])

    if feature in features:
        features.remove(feature)
    else:
        features.append(feature)

    context.user_data["property"]["features"] = features
    await show_features_menu(query, context)
    return SELECTING_FEATURES

async def enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الخطوة 8: إدخال الوصف"""
    query = update.callback_query
    await query.answer()
    features = context.user_data["property"].get("features", [])
    feature_list = ", ".join([FEATURE_NAMES.get(f, f) for f in features]) or "لا يوجد"

    await query.edit_message_text(
        f"🏡 *الخطوة 8 من 9*\n\n"
        f"✨ المميزات: {feature_list}\n\n"
        f"📝 أدخل وصف العقار (اختياري):\n"
        f"اضغط /skip للتخطي:",
        parse_mode="Markdown"
    )
    return ENTERING_DESCRIPTION

async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي الوصف"""
    context.user_data["property"]["description"] = ""
    return await request_photos(update, context)

async def save_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ الوصف"""
    context.user_data["property"]["description"] = update.message.text
    return await request_photos(update, context)

async def request_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب الصور"""
    await update.message.reply_text(
        f"🏡 الخطوة 9 من 9\n\n"
        f"📸 أرسل صور العقار الآن.\n"
        f"يمكن إرسال عدة صور دفعة واحدة.\n\n"
        f"عند الانتهاء اضغط: /done",
        parse_mode="Markdown"
    )
    context.user_data["property"]["photos"] = []
    return UPLOADING_PHOTOS

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال صورة وحفظ file_id بدلاً من فتح ملفات محلية فقط"""
    photo = update.message.photo[-1]  # أعلى دقة
    file_id = photo.file_id

    # تحسين الحفظ: تخزين file_id لدعم التخزين الدائم دون الاعتماد على الحاوية
    photos = context.user_data["property"].get("photos", [])
    photos.append(file_id)
    context.user_data["property"]["photos"] = photos

    # تنزيل احتياطي محلي إن أمكن دون كسر البوت
    try:
        file = await photo.get_file()
        filename = f"{PHOTOS_DIR}/prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.file_id[:8]}.jpg"
        await file.download_to_drive(filename)
    except Exception as e:
        logger.warning(f"Could not save local photo copy: {e}")

    await update.message.reply_text(
        f"✅ تم استلام الصورة ({len(photos)} صور)\n"
        f"أرسل المزيد أو اضغط /done"
    )

async def finish_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الانتهاء من الصور - طلب الفيديو"""
    return await request_video(update, context)

async def request_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب الفيديو اختياري"""
    await update.message.reply_text(
        "🎥 فيديو جولة العقار (اختياري)\n\n"
        "أرسل فيديو أو اضغط /skip للتخطي:",
        parse_mode="Markdown"
    )
    context.user_data["property"]["video"] = None
    return ENTERING_VIDEO

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال فيديو"""
    video = update.message.video
    file = await video.get_file()
    filename = f"{PHOTOS_DIR}/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    await file.download_to_drive(filename)

    context.user_data["property"]["video"] = filename
    return await save_property(update, context)

async def skip_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي الفيديو"""
    return await save_property(update, context)

async def save_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ العقار وعرض المعاينة"""
    properties = load_properties()
    new_property = context.user_data["property"]
    new_property["id"] = len(properties) + 1
    new_property["date"] = datetime.now().isoformat()
    new_property["status"] = "active"
    properties.append(new_property)
    save_properties(properties)

    # بناء نص المعاينة
    feature_list = ", ".join([FEATURE_NAMES.get(f, f) for f in new_property.get("features", [])])
    photo_count = len(new_property.get("photos", []))
    video_status = "✅" if new_property.get("video") else "❌"

    area_fmt = safe_fmt_int(new_property.get('area', 0))
    price_fmt = safe_fmt_int(new_property.get('price', 0))
    ptype_str = TYPE_NAMES.get(new_property.get('type'), new_property.get('type', ''))

    preview = (
        f"✅ *تم حفظ العقار بنجاح!*\n\n"
        f"🏷️ النوع: {ptype_str}\n"
        f"📍 الموقع: {new_property.get('location', 'غير محدد')}\n"
        f"📏 المساحة: {area_fmt} م²\n"
        f"💰 السعر: {price_fmt} ريال\n"
        f"🛣️ الشوارع: {new_property.get('streets', '1')}\n"
        f"🧭 الواجهة: {new_property.get('facade', 'غير محدد')}\n"
        f"✨ المميزات: {feature_list or 'لا يوجد'}\n"
        f"📝 الوصف: {new_property.get('description') or 'لا يوجد'}\n"
        f"📸 الصور: {photo_count} صور\n"
        f"🎥 الفيديو: {video_status}\n\n"
        f"🆔 رقم العقار: #{new_property.get('id')}"
    )

    await update.message.reply_text(preview, parse_mode="Markdown")

    # إرسال الصور كمعاينة
    photos = new_property.get("photos", [])
    if photos:
        media = []
        opened_files = []
        for p in photos[:10]:  # أقصى 10 صور
            if isinstance(p, str) and (p.startswith("AgAC") or not os.path.exists(p)):
                # استخدام Telegram file_id مباشرة
                media.append(InputMediaPhoto(media=p))
            elif isinstance(p, str) and os.path.exists(p):
                f = open(p, 'rb')
                opened_files.append(f)
                media.append(InputMediaPhoto(media=f))
        if media:
            try:
                await update.message.reply_media_group(media)
            except Exception as e:
                logger.error(f"Photo send error: {e}")
            finally:
                for f in opened_files:
                    try:
                        f.close()
                    except Exception:
                        pass

    # إرسال الفيديو إن وجد
    video_item = new_property.get("video")
    if video_item:
        if isinstance(video_item, str) and os.path.exists(video_item):
            try:
                with open(video_item, 'rb') as f:
                    await update.message.reply_video(video=f)
            except Exception as e:
                logger.error(f"Video send error: {e}")
        elif isinstance(video_item, str):
            try:
                await update.message.reply_video(video=video_item)
            except Exception as e:
                logger.error(f"Video send error: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة"""
    await update.message.reply_text("❌ تم إلغاء إضافة العقار.")
    return ConversationHandler.END

# ============ FastAPI App models & Lifespan ============
class PropertyMapRequest(BaseModel):
    area: Optional[str] = "all"
    type: Optional[str] = "all"
    min_price: Optional[int] = None
    max_price: Optional[int] = None

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العام للبوت لمنع انهيار الخدمة"""
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ غير متوقع أثناء معالجة الطلب، ولكن البوت ما زال يعمل بنجاح."
            )
        except Exception:
            pass

telegram_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    migrate_properties()
    add_demo_properties()
    if BOT_TOKEN:
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        telegram_app.add_error_handler(global_error_handler)

        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(start_add_property, pattern="^add_property$")],
            states={
                SELECTING_TYPE: [CallbackQueryHandler(select_location, pattern="^type_")],
                SELECTING_LOCATION: [CallbackQueryHandler(enter_area, pattern="^loc_")],
                ENTERING_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, validate_area)],
                ENTERING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, validate_price)],
                SELECTING_STREETS: [CallbackQueryHandler(select_facade, pattern="^streets_")],
                SELECTING_FACADE: [CallbackQueryHandler(select_features, pattern="^facade_")],
                SELECTING_FEATURES: [CallbackQueryHandler(toggle_feature, pattern="^feat_")],
                ENTERING_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_description),
                    CommandHandler("skip", skip_description)
                ],
                UPLOADING_PHOTOS: [
                    MessageHandler(filters.PHOTO, receive_photo),
                    CommandHandler("done", finish_photos)
                ],
                ENTERING_VIDEO: [
                    MessageHandler(filters.VIDEO, receive_video),
                    CommandHandler("skip", skip_video)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_message=True,
            per_chat=True,
            per_user=True,
        )

        telegram_app.add_handler(conv_handler)
        telegram_app.add_handler(CommandHandler("start", start))
        telegram_app.add_handler(CallbackQueryHandler(list_properties, pattern="^list_properties$"))
        telegram_app.add_handler(CallbackQueryHandler(reset_data_handler, pattern="^reset_data$"))
        telegram_app.add_handler(CallbackQueryHandler(confirm_reset, pattern="^confirm_reset$"))
        telegram_app.add_handler(CallbackQueryHandler(cancel_reset, pattern="^cancel_reset$"))
        telegram_app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))

        await telegram_app.initialize()
        await telegram_app.start()

        if WEBHOOK_URL:
            webhook_path = f"/bot/{BOT_TOKEN}"
            full_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
            await telegram_app.bot.set_webhook(
                url=full_url,
                allowed_updates=["message", "callback_query", "inline_query"]
            )
            print(f"✅ Webhook set: {full_url}")
            print(f"📊 Properties: {len(load_properties())}")

    yield

    if telegram_app:
        await telegram_app.stop()
        await telegram_app.shutdown()

app = FastAPI(title="Afaq Al-Injaz Real Estate Bot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/bot/{token}")
async def webhook(token: str, request: Request):
    if token != BOT_TOKEN:
        return JSONResponse(status_code=403, content={"error": "Invalid token"})
    data = await request.json()
    if telegram_app:
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "status": "running",
        "bot": "Afaq Al-Injaz Real Estate",
        "properties_count": len(load_properties())
    }

@app.get("/api/properties")
async def get_properties():
    return load_properties()

@app.post("/api/properties/map")
async def get_properties_map_post(request: Optional[PropertyMapRequest] = None):
    props = load_properties()
    if request:
        if request.area and request.area != "all":
            props = [p for p in props if p.get("location") == request.area or p.get("area") == request.area]
        if request.type and request.type != "all":
            props = [p for p in props if p.get("type") == request.type]
        if request.min_price is not None:
            props = [p for p in props if p.get("price", 0) >= request.min_price]
        if request.max_price is not None:
            props = [p for p in props if p.get("price", 0) <= request.max_price]
    return {"properties": props}

@app.get("/api/properties/map")
async def get_properties_map_get(
    area: Optional[str] = "all",
    type: Optional[str] = "all",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None
):
    req = PropertyMapRequest(area=area, type=type, min_price=min_price, max_price=max_price)
    return await get_properties_map_post(req)

@app.get("/api/properties/{property_id}")
async def get_property(property_id: int):
    for p in load_properties():
        if p["id"] == property_id:
            return p
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.get("/api/photos/{filename}")
async def get_photo(filename: str):
    path = os.path.join(PHOTOS_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse(status_code=404, content={"error": "Photo not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
