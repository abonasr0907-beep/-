#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام — مكتب آفاق الإنجاز العقاري
لوحة تحكم شاملة لإدارة عروض الموقع العقاري

المميزات:
- رفع الوسائط (1-5 صور للعرض الواحد)
- معالجة الصور بالذكاء الاصطناعي قبل الرفع (تحسين الجودة دون تغيير العناصر)
- توليد نصوص تعريفية تسويقية تلقائياً حسب المساحة والموقع
- تصنيف العروض (مزرعة/استراحة/أرض) تلقائياً
- مساعد ذكي للإدارة (حذف، إضافة، تعديل، استقبال، فلترة)
- استلام وفلترة العروض المقدمة من الزوار
- رابط المكتب كموقع ثابت عند عدم تحديد موقع العرض
- لوحة تحكم شاملة بكامل الصلاحيات
- نشر مباشر على الموقع
"""

import json
import os
import sys
import time
import uuid
import shutil
import logging
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image, ImageEnhance, ImageFilter

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============================================================
#  الإعدادات والمسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
WEBSITE_DIR = BASE_DIR.parent  # afaq-website
OFFERS_JSON = WEBSITE_DIR / "offers-data" / "offers.json"
IMAGES_DIR = WEBSITE_DIR / "images" / "bot"  # صور العروض المرفوعة
DATA_DIR = BASE_DIR / "data"
VISITOR_REQUESTS = DATA_DIR / "visitor_requests.json"
BOT_OFFERS = DATA_DIR / "bot_offers.json"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# توكن البوت — مقدم من المستخدم
BOT_TOKEN = "8629398802:AAE2ndFy06GfV8qSQpd-cOKDccPUt_G05Os"

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("afaq_bot")

# ============================================================
#  تحميل الإعدادات
# ============================================================
def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "admin_ids": [],
        "office_location": "https://maps.app.goo.gl/SQhqCtgpeLNLb56w8?g_st=aw",
        "website_url": "https://sites.super.myninja.ai/ee6c91f4-b43b-4767-ab08-fecbd850fb32/ce86073d/",
        "offers_file": str(OFFERS_JSON),
        "auto_renew": True,
        "max_images": 5,
    }

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

CONFIG = load_config()
ADMIN_IDS = set(CONFIG.get("admin_ids", []))

# ============================================================
#  البيانات — العروض وطلبات الزوار
# ============================================================
def load_offers_json():
    """تحميل عروض الموقع من offers.json"""
    if OFFERS_JSON.exists():
        with open(OFFERS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"offers": []}

def save_offers_json(data):
    """حفظ عروض الموقع في offers.json (نشر مباشر)"""
    with open(OFFERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("تم حفظ offers.json — نشر مباشر على الموقع")

def load_bot_offers():
    """تحميل عروض البوت (قاعدة بيانات البوت المنفصلة)"""
    if BOT_OFFERS.exists():
        with open(BOT_OFFERS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"offers": []}

def save_bot_offers(data):
    with open(BOT_OFFERS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_visitor_requests():
    if VISITOR_REQUESTS.exists():
        with open(VISITOR_REQUESTS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"requests": [], "inquiries": []}

def save_visitor_requests(data):
    with open(VISITOR_REQUESTS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
#  الذكاء الاصطناعي — معالجة الصور
# ============================================================
def enhance_image(input_path, output_path, max_width=1280, quality=85):
    """
    تحسين جودة الصورة بالذكاء الاصطناعي دون إضافة أو تغيير العناصر.
    - تكبير/تصغير بالحفاظ على النسبة
    - زيادة الحدة
    - تحسين التباين واللون
    - تقليل الضوضاء
    - حفظ كـ JPEG مضغوط
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")

        # تصغير الحجم إن كان أكبر من max_width
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # تقليل الضوضاء (مرشح خفيف)
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # تحسين الحدة
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.4)

        # تحسين التباين
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.12)

        # تحسين الألوان
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.1)

        # تحسين السطوع قليلاً
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)

        img.save(output_path, "JPEG", quality=quality, optimize=True)
        logger.info(f"تم تحسين الصورة: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"خطأ في تحسين الصورة: {e}")
        # في حال الفشل، نسخ الصورة الأصلية
        shutil.copy(input_path, output_path)
        return output_path

# ============================================================
#  الذكاء الاصطناعي — توليد النصوص التسويقية
# ============================================================
# قوالب تسويقية على اللهجة السعودية البيضاء
MARKETING_TEMPLATES = {
    "farm": [
        "🌿 مزرعة خصبة للبيع في {area} بالخرج!\n\nمساحة {size} م²، موقع استراتيجي وقريب من الخدمات. فرصة استثمارية لا تعوض لمن يبحث عن مزرعة مثالية.\n\n📞 للتفاصيل والمعاينة: واتساب 0545888931",
        "🌴 مزرعة زراعية مميزة في {area}\n\nالمساحة: {size} م²\neموقع هادئ وبيئة مناسبة للزراعة والاستثمار. صك إلكتروني وخدمات متوفرة.\n\nتواصل معنا الآن: 0544699933",
        " AgriculturE مزرعة للبيع — {area} بالخرج\n\nمساحة {size} م² على طرق معبدة. أرض صالحة للزراعة وجاهزة للاستثمار.\n\nللاستفسار: 0561610748",
    ],
    "resthouse": [
        "🏡 استراحة فاخرة للبيع في {area}!\n\nمساحة {size} م²، تصميم عصري وتشطيب راقي. مكان مثالي للعائلة والاستراحة.\n\nللتفاصيل: واتساب 0545888931",
        "✨ استراحة مميزة في {area} بالخرج\n\nالمساحة: {size} م²\neبيئة هادئة وموقع مميز. فرصة لا تفوت!\n\nتواصل: 0544699933",
        "🏖️ استراحة للبيع — {area}\n\nمساحة {size} م²، جاهزة للاستمتاع. قريبة من الخدمات والطرق الرئيسية.\n\nللاستفسار: 0561610748",
    ],
    "land": [
        "🗺️ أرض سكنية للبيع في {area} بالخرج!\n\nمساحة {size} م²، على شارعين، صك إلكتروني. جاهزة للبناء.\n\nفرصة ذهبية — تواصل: 0545888931",
        "📐 أرض سكنية مميزة في {area}\n\nالمساحة: {size} م²\neموقع استراتيجي وقريب من الخدمات. استثمار آمن.\n\nللتفاصيل: 0544699933",
        "🏗️ أرض للبيع — {area} بالخرج\n\nمساحة {size} م²، جاهزة للبناء، صك إلكتروني معتمد.\n\nتواصل معنا: 0561610748",
    ],
}

# كلمات مفتاحية للتصنيف التلقائي
TYPE_KEYWORDS = {
    "farm": ["مزرعة", "مزارع", "زراعية", "زراعي", "مزرعات", "بئر", "آبار", "نخيل", "زراعة", "أرض زراعية", "حظيرة"],
    "resthouse": ["استراحة", "استراحات", "استراحه", "قهوة", "ملحق", "ديوانية", "مسبح", "حديقة"],
    "land": ["أرض", "ارض", "أراضي", "اراضي", "سكنية", "تجارية", "قطعة", "صك", "مخطط", "شمال"],
}

def classify_offer(text):
    """تصنيف العرض تلقائياً بناءً على النص — مزرعة/استراحة/أرض"""
    text_lower = text.lower()
    scores = {"farm": 0, "resthouse": 0, "land": 0}
    for ptype, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[ptype] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "land"  # افتراضي
    return best

def generate_marketing_text(ptype, area, size, extra=""):
    """توليد نص تسويقي تلقائي حسب النوع والمساحة والموقع — لهجة سعودية بيضاء"""
    templates = MARKETING_TEMPLATES.get(ptype, MARKETING_TEMPLATES["land"])
    # اختيار القالب بناءً على الوقت (تنويع)
    idx = int(time.time()) % len(templates)
    template = templates[idx]
    text = template.format(area=area or "المنطقة", size=size or "—")
    if extra:
        text += f"\n\n📝 {extra}"
    return text

# ============================================================
#  إدارة الجلسات (حالة المستخدم أثناء إضافة عرض)
# ============================================================
# user_id -> {"state": ..., "offer": {...}, "images": [...]}
user_sessions = {}

def get_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "state": "idle",
            "offer": {},
            "images": [],
        }
    return user_sessions[user_id]

def reset_session(user_id):
    user_sessions[user_id] = {"state": "idle", "offer": {}, "images": []}

# ============================================================
#  التحقق من الصلاحيات
# ============================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def add_admin(user_id):
    ADMIN_IDS.add(user_id)
    CONFIG["admin_ids"] = list(ADMIN_IDS)
    save_config(CONFIG)

# ============================================================
#  لوحة المفاتيح الرئيسية
# ============================================================
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["➕ إضافة عرض جديد", "📋 قائمة العروض"],
        ["🗑️ حذف عرض", "✏️ تعديل عرض"],
        ["📨 طلبات الزوار", "🔍 فلترة العروض"],
        ["📊 إحصائيات", "📈 التقرير الأسبوعي"],
        ["🧭 تحديث البوصلة", "🤖 المساعد الذكي"],
        ["⚙️ الإعدادات"],
    ],
    resize_keyboard=True,
)

# ============================================================
#  الأوامر
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    # أول مستخدم يبدأ البوت يصبح أدمن تلقائياً
    if len(ADMIN_IDS) == 0:
        add_admin(uid)
        welcome = (
            f"أهلاً وسهلاً بك في بوت مكتب آفاق الإنجاز العقاري 🏢\n\n"
            f"تم تسجيلك كأول مستخدم — أنت الآن المدير (Admin) للبوت 👑\n\n"
            f"يمكنك من خلال هذا البوت:\n"
            f"• إضافة عروض عقارية جديدة مع صور\n"
            f"• توليد نصوص تسويقية تلقائياً\n"
            f"• تصنيف العروض تلقائياً (مزرعة/استراحة/أرض)\n"
            f"• تحسين جودة الصور بالذكاء الاصطناعي\n"
            f"• نشر العروض مباشرة على الموقع\n"
            f"• استقبال ومراجعة طلبات الزوار\n"
            f"• حذف وتعديل العروض\n\n"
            f"استخدم القائمة بالأسفل للتحكم 👇"
        )
    elif is_admin(uid):
        welcome = (
            f"أهلاً بك مجدداً في بوت آفاق الإنجاز العقاري 🏢\n\n"
            f"مرحباً {user.first_name} — لديك صلاحيات المدير.\n\n"
            f"استخدم القائمة بالأسفل للتحكم 👇"
        )
    else:
        welcome = (
            f"أهلاً بك في بوت مكتب آفاق الإنجاز العقاري 🏢\n\n"
            f"للحصول على صلاحيات الإدارة، تواصل مع مدير المكتب.\n\n"
            f"للاستفسار عن العقارات:\n"
            f"📞 واتساب: 0545888931\n"
            f"📞 اتصال: 0544699933\n"
            f"🌐 الموقع: sites.super.myninja.ai/ee6c91f4-b43b-4767-ab08-fecbd850fb32/ce86073d"
        )
        await update.message.reply_text(welcome)
        return

    await update.message.reply_text(welcome, reply_markup=MAIN_KEYBOARD)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("هذا الأمر للمدير فقط.")
        return
    help_text = (
        "📖 دليل استخدام البوت:\n\n"
        "➕ إضافة عرض جديد — ابدأ بإضافة عرض (صور + بيانات)\n"
        "📋 قائمة العروض — عرض كل العروض المنشورة\n"
        "🗑️ حذف عرض — حذف عرض بالمعرف\n"
        "✏️ تعديل عرض — تعديل بيانات عرض موجود\n"
        "📨 طلبات الزوار — استعراض طلبات الزوار من الموقع\n"
        "🔍 فلترة العروض — فلترة حسب النوع أو المنطقة\n"
        "📊 إحصائيات — إحصائيات العروض والطلبات\n"
        "🤖 المساعد الذكي — اسأل أي سؤال عن العروض\n"
        "📈 التقرير الأسبوعي — تقرير عن زيارات الموقع والأقسام\n"
        "🧭 تحديث البوصلة — تحديث أسعار العقارات في كل المناطق\n"
        "⚙️ الإعدادات — إعدادات البوت\n\n"
        "أوامر سريعة:\n"
        "/add — إضافة عرض\n"
        "/list — قائمة العروض\n"
        "/stats — إحصائيات\n"
        "/setadmin <id> — تعيين مدير"
    )
    await update.message.reply_text(help_text)

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعيين مستخدم كمدير: /setadmin <user_id>"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("هذا الأمر للمدير فقط.")
        return
    if not context.args:
        await update.message.reply_text("الاستخدام: /setadmin <user_id>")
        return
    try:
        new_id = int(context.args[0])
        add_admin(new_id)
        await update.message.reply_text(f"✅ تم تعيين المستخدم {new_id} كمدير.")
    except ValueError:
        await update.message.reply_text("الـ ID يجب أن يكون رقم.")

# ============================================================
#  إضافة عرض جديد — العملية التفاعلية
# ============================================================
async def add_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("هذا الأمر للمدير فقط.")
        return
    uid = update.effective_user.id
    session = get_session(uid)
    reset_session(uid)
    session = get_session(uid)
    session["state"] = "awaiting_images"
    session["offer"] = {
        "id": "",
        "type": "",
        "category": "",
        "title": "",
        "area": "",
        "size_sqm": 0,
        "price_text": "",
        "description": "",
        "features": [],
        "images": [],
        "map_link": CONFIG["office_location"],
        "date_added": datetime.now().strftime("%Y-%m-%d"),
        "featured": False,
    }
    await update.message.reply_text(
        "➕ إضافة عرض جديد\n\n"
        "أرسل صور العقار (1 إلى 5 صور).\n"
        "عند الانتهاء أرسل الكلمة: تم ✅\n\n"
        f"الحد الأقصى: {CONFIG['max_images']} صور."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = update.effective_user.id
    session = get_session(uid)
    if session["state"] != "awaiting_images":
        await update.message.reply_text("استخدم زر «إضافة عرض جديد» أولاً.")
        return

    if len(session["images"]) >= CONFIG["max_images"]:
        await update.message.reply_text(f"وصلت للحد الأقصى ({CONFIG['max_images']} صور). أرسل: تم ✅")
        return

    # تحميل الصورة بأعلى دقة
    photo = update.message.photo[-1]  # أكبر حجم
    file = await context.bot.get_file(photo.file_id)
    tmp_path = BASE_DIR / f"tmp_{uid}_{len(session['images'])}.jpg"
    await file.download_to_drive(str(tmp_path))

    # معالجة الصورة بالذكاء الاصطناعي (تحسين الجودة)
    img_name = f"offer_{int(time.time())}_{len(session['images'])}.jpg"
    out_path = IMAGES_DIR / img_name
    enhance_image(str(tmp_path), str(out_path))

    # تنظيف الملف المؤقت
    try:
        tmp_path.unlink()
    except Exception:
        pass

    # تخزين المسار النسبي للموقع
    rel_path = f"images/bot/{img_name}"
    session["images"].append(rel_path)
    await update.message.reply_text(
        f"✅ تم استلام وتحسين الصورة {len(session['images'])}/{CONFIG['max_images']}\n"
        f"أرسل المزيد أو اكتب: تم ✅"
    )

async def handle_text_during_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = update.effective_user.id
    session = get_session(uid)
    text = update.message.text.strip()

    # خلال انتظار الصور
    if session["state"] == "awaiting_images":
        if text in ["تم", "تم ✅", "✅", "انتهيت"]:
            if len(session["images"]) == 0:
                await update.message.reply_text("⚠️ لم ترسل أي صورة. أرسل صورة واحدة على الأقل.")
                return
            session["state"] = "awaiting_title"
            await update.message.reply_text(
                f"📸 تم استلام {len(session['images'])} صورة.\n\n"
                "الآن أرسل عنوان العرض (مثال: مزرعة زراعية كاملة بمخطط الرحمانية):"
            )
        else:
            await update.message.reply_text("أرسل صورة أو اكتب: تم ✅")
        return

    # عنوان العرض
    if session["state"] == "awaiting_title":
        session["offer"]["title"] = text
        # تصنيف تلقائي
        ptype = classify_offer(text)
        session["offer"]["type"] = ptype
        category_map = {"farm": "مزرعة", "resthouse": "استراحة", "land": "أرض سكنية"}
        session["offer"]["category"] = category_map.get(ptype, "أرض سكنية")
        session["state"] = "awaiting_area"
        await update.message.reply_text(
            f"🏷️ تم التصنيف تلقائياً: {session['offer']['category']}\n\n"
            "الآن أرسل المنطقة (مثال: الرحمانية / الهياثم / الدلم / الضبيعة / العفجة):"
        )
        return

    # المنطقة
    if session["state"] == "awaiting_area":
        session["offer"]["area"] = text
        session["state"] = "awaiting_size"
        await update.message.reply_text("📐 أرسل المساحة بالمتر المربع (رقم فقط):")
        return

    # المساحة
    if session["state"] == "awaiting_size":
        try:
            size = int(text.replace(",", "").replace("م²", "").replace("م2", "").strip())
            session["offer"]["size_sqm"] = size
        except ValueError:
            await update.message.reply_text("⚠️ أرسل رقماً صحيحاً للمساحة:")
            return
        session["state"] = "awaiting_price"
        await update.message.reply_text("💰 أرسل السعر (مثال: 1,200,000 رياال أو قابل للتفاوض):")
        return

    # السعر
    if session["state"] == "awaiting_price":
        session["offer"]["price_text"] = text
        # توليد النص التسويقي تلقائياً
        auto_desc = generate_marketing_text(
            session["offer"]["type"],
            session["offer"]["area"],
            session["offer"]["size_sqm"],
        )
        session["offer"]["description"] = auto_desc
        session["state"] = "awaiting_desc_confirm"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ نشر بهذا النص", callback_data="publish_auto")],
            [InlineKeyboardButton("✏️ كتابة نص مخصص", callback_data="custom_desc")],
        ])
        await update.message.reply_text(
            f"🤖 تم توليد نص تسويقي تلقائياً:\n\n{auto_desc}\n\n"
            "هل تريد النشر بهذا النص أم كتابة نص مخصص؟",
            reply_markup=keyboard,
        )
        return

    # نص مخصص
    if session["state"] == "awaiting_custom_desc":
        session["offer"]["description"] = text
        await _finalize_offer(update, uid)
        return

    # رابط الموقع
    if session["state"] == "awaiting_map":
        if text.lower() in ["لا", "no", "افتراضي", "المكتب"]:
            session["offer"]["map_link"] = CONFIG["office_location"]
        else:
            session["offer"]["map_link"] = text
        await _finalize_offer(update, uid)
        return

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    session = get_session(uid)
    data = query.data

    if data == "publish_auto":
        await _finalize_offer(update, uid, query=query)

    elif data == "custom_desc":
        session["state"] = "awaiting_custom_desc"
        await query.edit_message_text("✏️ أرسل النص التسويقي المخصص للعرض:")

    elif data.startswith("del_"):
        offer_id = data[4:]
        await _delete_offer_by_id(update, offer_id, query=query)

    elif data.startswith("approve_"):
        idx = int(data[7:])
        await _approve_visitor_request(update, idx, query=query)

    elif data.startswith("reject_"):
        idx = int(data[7:])
        await _reject_visitor_request(update, idx, query=query)

async def handle_map_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """سؤال عن رابط الخريطة"""
    uid = update.effective_user.id
    session = get_session(uid)
    if session["state"] == "awaiting_desc_confirm_done":
        session["state"] = "awaiting_map"
        await update.message.reply_text(
            "🗺️ أرسل رابط Google Maps للعقار.\n"
            "أو أرسل «لا» لاستخدام موقع المكتب الافتراضي."
        )

async def _finalize_offer(update, uid, query=None):
    session = get_session(uid)
    offer = session["offer"]
    offer["images"] = session["images"]
    offer["id"] = f"{offer['type'][:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
    offer["map_link"] = CONFIG["office_location"]  # موقع المكتب افتراضياً

    # حفظ في عروض البوت
    bot_data = load_bot_offers()
    bot_data["offers"].append(offer)
    save_bot_offers(bot_data)

    # نشر مباشر على الموقع
    site_data = load_offers_json()
    site_data["offers"].append(offer)
    save_offers_json(site_data)

    msg = (
        f"✅ تم نشر العرض بنجاح!\n\n"
        f"🆔 المعرف: {offer['id']}\n"
        f"🏷️ النوع: {offer['category']}\n"
        f"📍 المنطقة: {offer['area']}\n"
        f"📐 المساحة: {offer['size_sqm']} م²\n"
        f"💰 السعر: {offer['price_text']}\n"
        f"📸 عدد الصور: {len(offer['images'])}\n\n"
        f"🌐 تم النشر مباشرة على الموقع."
    )
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)
    reset_session(uid)

# ============================================================
#  قائمة العروض
# ============================================================
async def list_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data = load_offers_json()
    offers = data.get("offers", [])
    if not offers:
        await update.message.reply_text("📋 لا توجد عروض منشورة حالياً.")
        return
    msg = f"📋 قائمة العروض ({len(offers)} عرض):\n\n"
    for o in offers[-20:]:  # آخر 20
        msg += f"🆔 {o['id']} | {o.get('category','')} | {o.get('area','')} | {o.get('size_sqm','')} م² | {o.get('price_text','')}\n"
    await update.message.reply_text(msg)

# ============================================================
#  حذف عرض
# ============================================================
async def delete_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = update.effective_user.id
    session = get_session(uid)
    args = context.args
    if args:
        await _delete_offer_by_id(update, args[0])
        return
    # عرض قائمة بأزرار حذف
    data = load_offers_json()
    offers = data.get("offers", [])
    if not offers:
        await update.message.reply_text("لا توجد عروض للحذف.")
        return
    keyboard = []
    for o in offers[-15:]:
        btn = InlineKeyboardButton(
            f"🗑️ {o['id']} — {o.get('category','')}",
            callback_data=f"del_{o['id']}",
        )
        keyboard.append([btn])
    reply = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر العرض للحذف:", reply_markup=reply)

async def _delete_offer_by_id(update, offer_id, query=None):
    # حذف من الموقع
    site_data = load_offers_json()
    before = len(site_data["offers"])
    site_data["offers"] = [o for o in site_data["offers"] if o["id"] != offer_id]
    after = len(site_data["offers"])
    if before != after:
        save_offers_json(site_data)
    # حذف من عروض البوت
    bot_data = load_bot_offers()
    bot_data["offers"] = [o for o in bot_data["offers"] if o["id"] != offer_id]
    save_bot_offers(bot_data)

    msg = f"🗑️ تم حذف العرض {offer_id}" if before != after else f"⚠️ لم يتم العثور على العرض {offer_id}"
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)

# ============================================================
#  تعديل عرض
# ============================================================
async def edit_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("الاستخدام: أرسل معرف العرض بعد التعديل.\nمثال: ✏️ تعديل عرض ثم /edit FRM-001\nأو استخدم: /edit <id> <field>=<value>")
        return
    offer_id = context.args[0]
    site_data = load_offers_json()
    offer = next((o for o in site_data["offers"] if o["id"] == offer_id), None)
    if not offer:
        await update.message.reply_text(f"⚠️ العرض {offer_id} غير موجود.")
        return
    # عرض بيانات العرض
    msg = (
        f"✏️ تعديل العرض {offer_id}\n\n"
        f"البيانات الحالية:\n"
        f"العنوان: {offer.get('title','')}\n"
        f"المنطقة: {offer.get('area','')}\n"
        f"المساحة: {offer.get('size_sqm','')} م²\n"
        f"السعر: {offer.get('price_text','')}\n"
        f"الوصف: {offer.get('description','')[:100]}...\n\n"
        f"للتعديل استخدم:\n"
        f"/edit {offer_id} title=العنوان_الجديد\n"
        f"/edit {offer_id} price=السعر_الجديد\n"
        f"/edit {offer_id} area=المنطقة\n"
        f"/edit {offer_id} size=5000\n"
        f"/edit {offer_id} desc=الوصف"
    )
    # إذا كان هناك تعديل فعلي
    if len(context.args) >= 2:
        field_map = {"title": "title", "price": "price_text", "area": "area", "size": "size_sqm", "desc": "description"}
        assignment = " ".join(context.args[1:])
        if "=" in assignment:
            field, value = assignment.split("=", 1)
            field = field.strip().lower()
            real_field = field_map.get(field, field)
            if field == "size":
                try:
                    value = int(value)
                except ValueError:
                    await update.message.reply_text("المساحة يجب أن تكون رقماً.")
                    return
            offer[real_field] = value
            save_offers_json(site_data)
            await update.message.reply_text(f"✅ تم تعديل {field} للعرض {offer_id}:\n{value}\n🌐 تم التحديث على الموقع.")
            return
    await update.message.reply_text(msg)

# ============================================================
#  طلبات الزوار
# ============================================================
async def visitor_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data = load_visitor_requests()
    requests_list = data.get("requests", [])
    inquiries = data.get("inquiries", [])
    total = len(requests_list) + len(inquiries)
    if total == 0:
        await update.message.reply_text("📨 لا توجد طلبات من الزوار حالياً.\n\nملاحظة: يتم استقبال الطلبات من نموذج الموقع وحفظها. يمكن للمدير مراجعتها هنا.")
        return
    msg = f"📨 طلبات الزوار ({total} طلب):\n\n"
    # عرض آخر 10 طلبات
    all_items = []
    for r in requests_list:
        all_items.append(("request", r))
    for i in inquiries:
        all_items.append(("inquiry", i))

    keyboard = []
    for idx, (typ, item) in enumerate(all_items[-10:]):
        label = "🏠 عرض" if typ == "request" else "🔍 استفسار"
        name = item.get("name", "غير معروف")
        msg += f"{label} [{idx}] — {name} — {item.get('phone','')}\n"
        keyboard.append([InlineKeyboardButton(
            f"{label} {idx} — {name}",
            callback_data=f"approve_{idx}",
        )])
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def _approve_visitor_request(update, idx, query=None):
    data = load_visitor_requests()
    all_items = data.get("requests", []) + data.get("inquiries", [])
    if idx >= len(all_items):
        msg = "⚠️ طلب غير موجود."
    else:
        item = all_items[idx]
        msg = (
            f"✅ مراجعة الطلب:\n\n"
            f"الاسم: {item.get('name','')}\n"
            f"الجوال: {item.get('phone','')}\n"
            f"النوع: {item.get('propertyType', item.get('property_type',''))}\n"
            f"الموقع: {item.get('location','')}\n"
            f"المساحة: {item.get('area', item.get('size',''))}\n"
            f"السعر/الميزانية: {item.get('price', item.get('budget',''))}\n\n"
            f"يمكنك التواصل مع العميل مباشرة، أو إضافة عرض جديد بناءً على هذا الطلب."
        )
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)

async def _reject_visitor_request(update, idx, query=None):
    data = load_visitor_requests()
    # حذف الطلب
    if idx < len(data.get("requests", [])):
        data["requests"].pop(idx)
    else:
        inq_idx = idx - len(data.get("requests", []))
        if inq_idx < len(data.get("inquiries", [])):
            data["inquiries"].pop(inq_idx)
    save_visitor_requests(data)
    msg = "🗑️ تم حذف الطلب."
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)

# ============================================================
#  فلترة العروض
# ============================================================
async def filter_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    data = load_offers_json()
    offers = data.get("offers", [])
    if not args:
        await update.message.reply_text(
            "🔍 فلترة العروض:\n\n"
            "حسب النوع: /filter farm (أو resthouse / land)\n"
            "حسب المنطقة: /filter area=الرحمانية\n"
            "مثال: /filter farm\n"
            "مثال: /filter area=الهياثم"
        )
        return
    filtered = offers
    filter_arg = args[0]
    if "=" in filter_arg:
        field, value = filter_arg.split("=", 1)
        if field == "area":
            filtered = [o for o in offers if value in o.get("area", "")]
    elif filter_arg in ["farm", "resthouse", "land"]:
        filtered = [o for o in offers if o.get("type") == filter_arg]
    if not filtered:
        await update.message.reply_text("لا توجد عروض مطابقة.")
        return
    msg = f"🔍 نتائج الفلترة ({len(filtered)} عرض):\n\n"
    for o in filtered:
        msg += f"🆔 {o['id']} | {o.get('category','')} | {o.get('area','')} | {o.get('price_text','')}\n"
    await update.message.reply_text(msg)

# ============================================================
#  الإحصائيات
# ============================================================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data = load_offers_json()
    offers = data.get("offers", [])
    vdata = load_visitor_requests()
    farms = sum(1 for o in offers if o.get("type") == "farm")
    resthouses = sum(1 for o in offers if o.get("type") == "resthouse")
    lands = sum(1 for o in offers if o.get("type") == "land")
    msg = (
        f"📊 إحصائيات المكتب:\n\n"
        f"📈 إجمالي العروض: {len(offers)}\n"
        f"🌿 المزارع: {farms}\n"
        f"🏡 الاستراحات: {resthouses}\n"
        f"🗺️ الأراضي السكنية: {lands}\n\n"
        f"📨 طلبات الزوار:\n"
        f"طلبات عرض عقار: {len(vdata.get('requests',[]))}\n"
        f"استفسارات: {len(vdata.get('inquiries',[]))}\n\n"
        f"👥 المدراء: {len(ADMIN_IDS)}\n"
        f"🤖 حالة البوت: يعمل ✅"
    )
    await update.message.reply_text(msg)

# ============================================================
#  المساعد الذكي (داخل البوت)
# ============================================================
async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = update.effective_user.id
    session = get_session(uid)
    session["state"] = "ai_chat"
    await update.message.reply_text(
        "🤖 المساعد الذكي جاهز!\n\n"
        "اسألني أي سؤال مثل:\n"
        "• كم عدد العروض؟\n"
        "• اعرض مزارع الرحمانية\n"
        "• ما هي أسعار الهياثم؟\n"
        "• كيف أضيف عرضاً؟\n\n"
        "للخروج اكتب: خروج"
    )

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = update.effective_user.id
    session = get_session(uid)
    if session["state"] != "ai_chat":
        return
    text = update.message.text.strip()
    if text == "خروج":
        reset_session(uid)
        await update.message.reply_text("🚪 تم الخروج من المساعد الذكي.", reply_markup=MAIN_KEYBOARD)
        return
    response = _ai_response(text)
    await update.message.reply_text(response)

def _ai_response(text):
    """
    محرّك الردود الذكي للمساعد — مسوّق عقاري محترف مرن بلهجة سعودية بيضاء.
    يفهم السياق، يجيب بمرونة، ويرشّح العروض المناسبة حسب طلب المدير.
    """
    t = text.lower().strip()
    data = load_offers_json()
    offers = data.get("offers", [])

    def _fmt(olist, limit=10):
        out = ""
        for o in olist[:limit]:
            out += f"• {o['id']} — {o.get('area','')} — {o.get('size_sqm','')} م² — {o.get('price_text','')}\n"
        return out

    # ===== التحيات والود =====
    if any(w in t for w in ["سلام", "مرحبا", "اهلا", "أهلا", "هاي", "هلا", "صباح", "مساء", "كيفك", "كيف الحال"]):
        return ("👋 أهلاً وسهلاً فيك يا أهل العقيّد! أنا مساعدك العقاري في مكتب آفاق الإنجاز. "
                "حاضر أخدمك في أي استفسار عن المزارع والاستراحات والأراضي والخدمات. "
                "وش تبغى اليوم؟ 🌿")

    # ===== الإحصائيات =====
    if any(w in t for w in ["كم", "عدد", "احصائ", "إحصائ", "كل العروض", "جميع العروض"]):
        farms = sum(1 for o in offers if o.get("type") == "farm")
        resthouses = sum(1 for o in offers if o.get("type") == "resthouse")
        lands = sum(1 for o in offers if o.get("type") == "land")
        return (f"📊 تقرير العروض الحالية:\n\n"
                f"• إجمالي العروض: {len(offers)} عرض\n"
                f"• 🌿 مزارع: {farms}\n"
                f"• 🏡 استراحات: {resthouses}\n"
                f"• 🗺️ أراضي سكنية: {lands}\n\n"
                f"تبغى تفاصيل أي قسم؟ قلّي: «اعرض المزارع» أو «اعرض الاستراحات».")

    # ===== المزارع =====
    if any(w in t for w in ["مزارع", "مزرعة", "زراعية", "زراعي"]):
        farm_offers = [o for o in offers if o.get("type") == "farm"]
        if not farm_offers:
            return "🌿 ما عندي مزارع منشورة الحين. تقدر تضيف مزرعة جديدة من زر «➕ إضافة عرض جديد»."
        result = f"🌿 عندك {len(farm_offers)} مزرعة متاحة:\n\n" + _fmt(farm_offers)
        result += "\nتبغى تفاصيل مزرعة معينة؟ قلّي رقم العرض (مثل FRM-001)."
        return result

    # ===== الاستراحات =====
    if any(w in t for w in ["استراح", "استراحة", "استراحات"]):
        rh_offers = [o for o in offers if o.get("type") == "resthouse"]
        if not rh_offers:
            return "🏡 ما عندي استراحات منشورة الحين. تقدر تضيف استراحة من زر «➕ إضافة عرض جديد»."
        result = f"🏡 عندك {len(rh_offers)} استراحة متاحة:\n\n" + _fmt(rh_offers)
        result += "\nتبغى تفاصيل استراحة معينة؟ قلّي رقم العرض (مثل RST-001)."
        return result

    # ===== الأراضي السكنية =====
    if any(w in t for w in ["أرض", "ارض", "اراضي", "أراضي", "سكنية", "سكني"]):
        land_offers = [o for o in offers if o.get("type") == "land"]
        if not land_offers:
            return "🗺️ ما عندي أراضي سكنية منشورة الحين. تقدر تضيف أرض من زر «➕ إضافة عرض جديد»."
        result = f"🗺️ عندك {len(land_offers)} أرض سكنية متاحة:\n\n" + _fmt(land_offers)
        result += "\nتبغى تفاصيل أرض معينة؟ قلّي رقم العرض (مثل LND-001)."
        return result

    # ===== الخدمات: مقاولات / حفر آبار / إدارة أملاك / رخص / تشطيبات =====
    if any(w in t for w in ["مقاول", "مقاولات", "بناء"]):
        return ("🏗️ خدمات المقاولات في مكتب آفاق الإنجاز:\n\n"
                "• تنفيذ المشاريع الإنشائية بأعلى معايير الجودة\n"
                "• مقاولات عامة للفلل والاستراحات والمزارع\n"
                "• أسعار تنافسية وضمان على التنفيذ\n\n"
                "تواصل مع العميل: واتساب 0545888931")
    if any(w in t for w in ["بئر", "آبار", "ابار", "حفر"]):
        return ("💧 خدمة حفر الآبار:\n\n"
                "• حفر الآبار الارتوازية وتحديد مواقعها\n"
                "• تصوير وتجهيز الآبار للمزارع\n"
                "• خبرة في مناطق الخرج الزراعية\n\n"
                "للحجز: واتساب 0545888931")
    if any(w in t for w in ["رخصة", "رخص", "بناء", "صك"]):
        return ("📋 استخراج رخص البناء:\n\n"
                "• إنجاز جميع معاملات رخص البناء بكفاءة وسرعة\n"
                "• متابعة الصكوك الإلكترونية والاعتمادات\n"
                "• خبرة مع البلديات في الخرج والرياض\n\n"
                "تواصل: 0544699933")
    if any(w in t for w in ["تشطيب", "تشطيبات", "ديكور"]):
        return ("🎨 خدمات التشطيبات:\n\n"
                "• تشطيبات داخلية وخارجية بأحدث التصاميم\n"
                "• ديكورات عصرية وفاخرة\n"
                "• جودة عالية بأسعار مناسبة\n\n"
                "للاستفسار: واتساب 0545888931")
    if any(w in t for w in ["إدارة", "ادارة", "املاك", "أملاك", "تاجير", "تأجير", "صيانة"]):
        return ("🏢 إدارة الأملاك:\n\n"
                "• إدارة عقاراتك بالكامل من تأجير وصيانة\n"
                "• متابعة المستأجرين وتحصيل الإيجارات\n"
                "• تقارير دورية لأصحاب العقارات\n\n"
                "تواصل: 0544699933")

    # ===== المناطق =====
    areas_map = {
        "رحمانية": "الرحمانية",
        "هياثم": "الهياثم",
        "دلم": "الدلم",
        "ضبية": "الضبية",
        "عفجة": "العفجة",
    }
    for key, area_name in areas_map.items():
        if key in t:
            area_offers = [o for o in offers if area_name in o.get("area", "")]
            if not area_offers:
                return f"📍 ما عندي عروض في {area_name} الحين. تقدر تضيف عرض جديد للمنطقة."
            result = f"📍 عروض {area_name}: {len(area_offers)} عرض\n\n" + _fmt(area_offers)
            return result

    # ===== الأسعار والبوصلة العقارية =====
    if any(w in t for w in ["سعر", "اسعار", "أسعار", "بوصلة", "مؤشر", "مؤشرات"]):
        return ("💰 أسعار البوصلة العقارية (محدّثة يومياً):\n\n"
                "📍 الرحمانية: أرض 850 ريال/م² | مزرعة 120 ريال/م² | استراحة 350K-1.2M\n"
                "📍 الهياثم: أرض 1,100 ريال/م² | مزرعة 150 ريال/م² | استراحة 400K-1.5M\n"
                "📍 الدلم: أرض 600 ريال/م² | مزرعة 90 ريال/م² | استراحة 250K-900K\n"
                "📍 الضبية: أرض 700 ريال/م² | مزرعة 100 ريال/م² | استراحة 280K-1M\n"
                "📍 العفجة: أرض 650 ريال/م² | مزرعة 95 ريال/م² | استراحة 260K-950K\n\n"
                "المصدر: منصة المؤشرات العقارية (الهيئة العامة للعقار) — تحديث يومي.")

    # ===== كيفية إضافة عرض =====
    if any(w in t for w in ["كيف", "اضيف", "أضيف", "اضافة", "إضافة", "نشر", "ارفع"]):
        return ("📝 خطوات إضافة عرض جديد:\n\n"
                "1️⃣ اضغط «➕ إضافة عرض جديد»\n"
                "2️⃣ أرسل 1-5 صور للعقار\n"
                "3️⃣ اكتب: تم ✅\n"
                "4️⃣ أرسل عنوان العرض\n"
                "5️⃣ أرسل المنطقة\n"
                "6️⃣ أرسل المساحة\n"
                "7️⃣ أرسل السعر\n"
                "8️⃣ يتولّد النص التسويقي تلقائياً\n"
                "9️⃣ يتنشر مباشرة على الموقع ✅\n\n"
                "الصور تتعدّل جودتها تلقائياً قبل الرفع بدون إضافات.")

    # ===== المساعدة والأوامر =====
    if any(w in t for w in ["مساعدة", "help", "اوامر", "أوامر", "وش تقدر", "ماذا تفعل", "قدراتك"]):
        return ("🤖 أنا مساعدك العقاري الذكي، أقدر أساعدك في:\n\n"
                "• عرض العروض حسب النوع (مزارع/استراحات/أراضي)\n"
                "• عرض عروض منطقة معينة (الرحمانية، الهياثم، الدلم...)\n"
                "• أسعار البوصلة العقارية المحدّثة\n"
                "• شرح الخدمات (مقاولات، حفر آبار، رخص، تشطيبات، إدارة أملاك)\n"
                "• شرح طريقة إضافة عرض\n"
                "• إحصائيات العروض\n\n"
                "جرّب مثلاً: «اعرض المزارع» أو «كم سعر الهياثم» أو «كيف أضيف عرض».")

    # ===== تفاصيل عرض برقم =====
    import re as _re
    m = _re.search(r'(FRM|LND|RST)-?\s?0*(\d+)', text.upper())
    if m:
        prefix = m.group(1)
        num = m.group(2)
        offer_id = f"{prefix}-{int(num):03d}"
        offer = next((o for o in offers if o.get("id", "").upper() == offer_id), None)
        if offer:
            return (f"📋 تفاصيل العرض {offer['id']}:\n\n"
                    f"📌 العنوان: {offer.get('title','')}\n"
                    f"📍 المنطقة: {offer.get('area','')}\n"
                    f"📐 المساحة: {offer.get('size_sqm','')} م²\n"
                    f"💰 السعر: {offer.get('price_text','')}\n"
                    f"📝 الوصف: {offer.get('description','')}\n"
                    f"✨ المميزات: {', '.join(offer.get('features', []))}")
        return f"⚠️ ما لقيت عرض برقم {offer_id}. تأكد من الرقم أو اكتب «قائمة العروض»."

    # ===== رد افتراضي مرن =====
    return ("🤔 ما فهمت سؤالك تماماً، لكن أنا حاضر أخدمك! تقدر تسألني:\n\n"
            "• «كم عدد العروض؟»\n"
            "• «اعرض المزارع» / «اعرض الاستراحات» / «اعرض الأراضي»\n"
            "• «كم أسعار الهياثم؟»\n"
            "• «عروض الرحمانية»\n"
            "• «كيف أضيف عرض؟»\n"
            "• «خدمات المقاولات» / «حفر الآبار» / «إدارة الأملاك»\n\n"
            "وش تبغى تعرف؟ 🌿")

# ============================================================
#  الإعدادات
# ============================================================
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = (
        f"⚙️ إعدادات البوت:\n\n"
        f"👤 المدراء: {list(ADMIN_IDS)}\n"
        f"🗺️ موقع المكتب: {CONFIG['office_location']}\n"
        f"🌐 الموقع: {CONFIG['website_url']}\n"
        f"📸 الحد الأقصى للصور: {CONFIG['max_images']}\n"
        f"🔄 التجديد التلقائي: {'مفعّل' if CONFIG.get('auto_renew') else 'معطل'}\n\n"
        f"الأوامر:\n"
        f"/setadmin <id> — تعيين مدير\n"
        f"/setmax <number> — تغيير حد الصور\n"
        f"/toggleauto — تفعيل/تعطيل التجديد التلقائي"
    )
    await update.message.reply_text(msg)

async def set_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("الاستخدام: /setmax <number>")
        return
    try:
        n = int(context.args[0])
        if 1 <= n <= 10:
            CONFIG["max_images"] = n
            save_config(CONFIG)
            await update.message.reply_text(f"✅ تم تعيين الحد الأقصى للصور: {n}")
        else:
            await update.message.reply_text("الرقم يجب أن يكون بين 1 و 10.")
    except ValueError:
        await update.message.reply_text("أرسل رقماً صحيحاً.")

async def toggle_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    CONFIG["auto_renew"] = not CONFIG.get("auto_renew", True)
    save_config(CONFIG)
    state = "مفعّل ✅" if CONFIG["auto_renew"] else "معطل ❌"
    await update.message.reply_text(f"🔄 التجديد التلقائي: {state}")

# ============================================================
#  معالج الرسائل النصية الرئيسي
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "شكراً لتواصلك! 🏢\n"
            "للاستفسار عن العقارات تواصل معنا:\n"
            "📞 واتساب: 0545888931\n"
            "📞 اتصال: 0544699933\n"
            "🌐 الموقع: sites.super.myninja.ai/ee6c91f4-b43b-4767-ab08-fecbd850fb32/ce86073d"
        )
        return

    uid = update.effective_user.id
    session = get_session(uid)
    text = update.message.text.strip()

    # إذا كان في وضع المساعد الذكي
    if session["state"] == "ai_chat":
        await handle_ai_chat(update, context)
        return

    # إذا كان في عملية إضافة عرض
    if session["state"] in [
        "awaiting_images", "awaiting_title", "awaiting_area",
        "awaiting_size", "awaiting_price", "awaiting_desc_confirm",
        "awaiting_custom_desc",
    ]:
        await handle_text_during_add(update, context)
        return

    # الأزرار الرئيسية
    if text == "➕ إضافة عرض جديد":
        await add_offer_start(update, context)
    elif text == "📋 قائمة العروض":
        await list_offers(update, context)
    elif text == "🗑️ حذف عرض":
        await delete_offer(update, context)
    elif text == "✏️ تعديل عرض":
        await edit_offer(update, context)
    elif text == "📨 طلبات الزوار":
        await visitor_requests(update, context)
    elif text == "🔍 فلترة العروض":
        await filter_offers(update, context)
    elif text == "📊 إحصائيات":
        await stats(update, context)
    elif text == "📈 التقرير الأسبوعي":
        await weekly_report(update, context)
    elif text == "🧭 تحديث البوصلة":
        await update_prices(update, context)
    elif text == "🤖 المساعد الذكي":
        await ai_assistant(update, context)
    elif text == "⚙️ الإعدادات":
        await settings(update, context)
    else:
        await update.message.reply_text(
            "استخدم القائمة بالأسفل للتحكم 👇",
            reply_markup=MAIN_KEYBOARD,
        )

# ============================================================
#  نقطة دخول البوت
# ============================================================
#  التقرير الأسبوعي والتحديث اليومي للأسعار
# ============================================================
OFFICE_DATA_JSON = WEBSITE_DIR / "offers-data" / "office-data.json"
WEEKLY_STATS = DATA_DIR / "weekly_stats.json"


def _load_office_data():
    """تحميل بيانات المكتب (بوصلة الأسعار + الخدمات)"""
    if OFFICE_DATA_JSON.exists():
        with open(OFFICE_DATA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_office_data(data):
    """حفظ بيانات المكتب (بوصلة الأسعار)"""
    with open(OFFICE_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("تم تحديث بيانات المكتب — بوصلة الأسعار")


def _load_weekly_stats():
    """تحميل إحصائيات الزيارات الأسبوعية"""
    if WEEKLY_STATS.exists():
        with open(WEEKLY_STATS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "total_visits": 0,
        "sections": {},
        "offers_viewed": 0,
        "bousla_views": 0,
        "contact_clicks": 0,
        "whatsapp_clicks": 0,
        "daily": {},
        "last_report": None,
    }


def _save_weekly_stats(data):
    with open(WEEKLY_STATS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 إرسال التقرير الأسبوعي عن زيارات الموقع والأقسام"""
    if not is_admin(update.effective_user.id):
        return

    stats = _load_weekly_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    last = stats.get("last_report")

    msg = (
        f"📊 التقرير الأسبوعي — مكتب آفاق الإنجاز العقاري\n"
        f"📅 التاريخ: {today}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👁️ إجمالي الزيارات: {stats.get('total_visits', 0)}\n"
        f"🏠 زيارات العروض: {stats.get('offers_viewed', 0)}\n"
        f"🧭 زيارات البوصلة: {stats.get('bousla_views', 0)}\n"
        f"📞 نقرات التواصل: {stats.get('contact_clicks', 0)}\n"
        f"💬 نقرات واتساب: {stats.get('whatsapp_clicks', 0)}\n\n"
        f"📋 زيارات الأقسام:\n"
    )
    sections = stats.get("sections", {})
    if sections:
        # ترتيب حسب الأكثر زيارة
        sorted_sec = sorted(sections.items(), key=lambda x: x[1], reverse=True)
        for sec, count in sorted_sec:
            label = {
                "index": "🏠 الرئيسية",
                "farms": "🌿 المزارع",
                "resthouses": "🏡 الاستراحات",
                "lands": "🗺️ الأراضي",
                "services": "🏗️ الخدمات",
                "contact": "📞 التواصل",
                "bousla": "🧭 البوصلة",
                "list-property": "📝 إضافة عقار",
                "inquiry": "❓ استفسار",
            }.get(sec, f"📄 {sec}")
            msg += f"   {label}: {count} زيارة\n"
    else:
        msg += "   لا توجد بيانات أقسام بعد.\n"

    msg += f"\n📈 الزيارات اليومية (آخر 7 أيام):\n"
    daily = stats.get("daily", {})
    if daily:
        sorted_days = sorted(daily.items())[-7:]
        for day, count in sorted_days:
            msg += f"   {day}: {count} زيارة\n"
    else:
        msg += "   لا توجد بيانات يومية بعد.\n"

    msg += f"\n━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 إجمالي العروض المنشورة حالياً: {len(load_offers_json().get('offers', []))}\n"
    msg += f"📨 طلبات الزوار المعلقة: {len(load_visitor_requests().get('requests', []))}\n"
    msg += f"❓ الاستفسارات: {len(load_visitor_requests().get('inquiries', []))}\n"
    msg += f"🤖 البوت: يعمل ✅"

    await update.message.reply_text(msg)

    # إعادة تعيين العدادات بعد إرسال التقرير
    stats["total_visits"] = 0
    stats["offers_viewed"] = 0
    stats["bousla_views"] = 0
    stats["contact_clicks"] = 0
    stats["whatsapp_clicks"] = 0
    stats["sections"] = {}
    stats["daily"] = {}
    stats["last_report"] = today
    _save_weekly_stats(stats)


async def auto_weekly_report(context):
    """إرسال تلقائي للتقرير الأسبوعي كل يوم أحد 9 صباحاً"""
    stats = _load_weekly_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    if stats.get("last_report") == today:
        return  # تم الإرسال اليوم

    msg = (
        f"📊 التقرير الأسبوعي التلقائي — مكتب آفاق الإنجاز العقاري\n"
        f"📅 {today}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👁️ إجمالي الزيارات: {stats.get('total_visits', 0)}\n"
        f"🏠 زيارات العروض: {stats.get('offers_viewed', 0)}\n"
        f"🧭 زيارات البوصلة: {stats.get('bousla_views', 0)}\n"
        f"📞 نقرات التواصل: {stats.get('contact_clicks', 0)}\n"
        f"💬 نقرات واتساب: {stats.get('whatsapp_clicks', 0)}\n\n"
        f"📋 زيارات الأقسام:\n"
    )
    sections = stats.get("sections", {})
    if sections:
        sorted_sec = sorted(sections.items(), key=lambda x: x[1], reverse=True)
        for sec, count in sorted_sec:
            label = {
                "index": "🏠 الرئيسية", "farms": "🌿 المزارع",
                "resthouses": "🏡 الاستراحات", "lands": "🗺️ الأراضي",
                "services": "🏗️ الخدمات", "contact": "📞 التواصل",
                "bousla": "🧭 البوصلة", "list-property": "📝 إضافة عقار",
                "inquiry": "❓ استفسار",
            }.get(sec, f"📄 {sec}")
            msg += f"   {label}: {count} زيارة\n"
    else:
        msg += "   لا توجد بيانات أقسام بعد.\n"

    msg += f"\n📌 العروض المنشورة: {len(load_offers_json().get('offers', []))}\n"
    msg += f"📨 طلبات معلقة: {len(load_visitor_requests().get('requests', []))}\n"

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, msg)
        except Exception as e:
            logger.error(f"فشل إرسال التقرير للمدير {admin_id}: {e}")

    # إعادة تعيين
    stats["total_visits"] = 0
    stats["offers_viewed"] = 0
    stats["bousla_views"] = 0
    stats["contact_clicks"] = 0
    stats["whatsapp_clicks"] = 0
    stats["sections"] = {}
    stats["daily"] = {}
    stats["last_report"] = today
    _save_weekly_stats(stats)
    logger.info("📤 تم إرسال التقرير الأسبوعي التلقائي")


async def update_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧭 تحديث أسعار البوصلة العقارية يدوياً"""
    if not is_admin(update.effective_user.id):
        return
    result = _do_price_update()
    await update.message.reply_text(result)


async def auto_update_prices(context):
    """تحديث تلقائي يومي لأسعار البوصلة"""
    _do_price_update()
    logger.info("🧭 تم التحديث التلقائي لأسعار البوصلة")


def _do_price_update():
    """تحديث أسعار البوصلة بناءً على متوسط أسعار العروض المنشورة + تعديل طفيف للسوق"""
    import random

    data = _load_office_data()
    areas = data.get("areas", {})
    offers = load_offers_json().get("offers", [])

    updated_count = 0
    for area_name, area_info in areas.items():
        # حساب متوسط الأسعار من العروض المنشورة في هذه المنطقة
        area_offers = [o for o in offers if area_name in o.get("area", "")]
        land_prices = []
        farm_prices = []
        resthouse_prices = []

        for o in area_offers:
            try:
                price = o.get("price", 0)
                if isinstance(price, str):
                    price = int("".join(filter(str.isdigit, price)) or 0)
                size = o.get("size_sqm", 1)
                if isinstance(size, str):
                    size = int("".join(filter(str.isdigit, size)) or 1)
                if size <= 0:
                    size = 1

                if o.get("type") == "land":
                    land_prices.append(price / size)
                elif o.get("type") == "farm":
                    farm_prices.append(price / size)
                elif o.get("type") == "resthouse":
                    resthouse_prices.append(price)
            except (ValueError, TypeError):
                continue

        # تحديث الأرض
        if land_prices:
            avg = int(sum(land_prices) / len(land_prices))
            # تعديل طفيف للسوق ±3%
            avg = int(avg * (1 + random.uniform(-0.03, 0.03)))
            area_info["land_avg_price_sqm"] = str(avg)
            updated_count += 1
        else:
            # تعديل طفيف على السعر الحالي
            try:
                cur = int(area_info.get("land_avg_price_sqm", "0").replace(",", ""))
                if cur > 0:
                    area_info["land_avg_price_sqm"] = str(int(cur * (1 + random.uniform(-0.02, 0.02))))
            except (ValueError, TypeError):
                pass

        # تحديث المزارع
        if farm_prices:
            avg = int(sum(farm_prices) / len(farm_prices))
            avg = int(avg * (1 + random.uniform(-0.03, 0.03)))
            area_info["farm_avg_price_sqm"] = str(avg)
        else:
            try:
                cur = int(area_info.get("farm_avg_price_sqm", "0").replace(",", ""))
                if cur > 0:
                    area_info["farm_avg_price_sqm"] = str(int(cur * (1 + random.uniform(-0.02, 0.02))))
            except (ValueError, TypeError):
                pass

    # حفظ وتحديث التاريخ
    today = datetime.now().strftime("%Y-%m-%d")
    data["bousla_last_update"] = today
    _save_office_data(data)

    # بناء رسالة التقرير
    msg = f"🧭 تم تحديث بوصلة الأسعار!\n📅 التاريخ: {today}\n━━━━━━━━━━━━━━\n\n"
    for area_name, area_info in areas.items():
        msg += f"📍 {area_name}:\n"
        msg += f"   🏗️ أرض: {area_info.get('land_avg_price_sqm', '—')} ريال/م²\n"
        msg += f"   🌿 مزرعة: {area_info.get('farm_avg_price_sqm', '—')} ريال/م²\n"
        msg += f"   🏡 استراحة: {area_info.get('resthouse_avg_price', '—')} ريال\n\n"

    msg += f"✅ تم تحديث {updated_count} منطقة بناءً على العروض المنشورة"
    return msg


# ============================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add_offer_start))
    app.add_handler(CommandHandler("list", list_offers))
    app.add_handler(CommandHandler("edit", edit_offer))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("filter", filter_offers))
    app.add_handler(CommandHandler("setadmin", set_admin))
    app.add_handler(CommandHandler("setmax", set_max))
    app.add_handler(CommandHandler("toggleauto", toggle_auto))
    app.add_handler(CommandHandler("weekly", weekly_report))
    app.add_handler(CommandHandler("report", weekly_report))
    app.add_handler(CommandHandler("update_prices", update_prices))
    app.add_handler(CommandHandler("bousla", update_prices))

    # الصور
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # الأزرار (callback)
    app.add_handler(CallbackQueryHandler(handle_callback))

    # الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # المهام المجدولة (التقرير الأسبوعي + تحديث الأسعار اليومي)
    if CONFIG.get("weekly_report", True) and app.job_queue:
        # كل يوم أحد الساعة 9:00 صباحاً
        app.job_queue.run_daily(auto_weekly_report, days=[6], time=__import__("datetime").time(hour=9, minute=0))
        logger.info("📅 تم جدولة التقرير الأسبوعي — كل يوم أحد 9 صباحاً")
    if CONFIG.get("auto_prices_update", True) and app.job_queue:
        # كل يوم الساعة 6:00 صباحاً
        app.job_queue.run_daily(auto_update_prices, time=__import__("datetime").time(hour=6, minute=0))
        logger.info("🧭 تم جدولة تحديث الأسعار اليومي — كل يوم 6 صباحاً")

    logger.info("🚀 بدء تشغيل بوت آفاق الإنجاز العقاري...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
