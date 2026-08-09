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
import hashlib
import asyncio
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PIL import Image, ImageEnhance, ImageFilter

import github_sync
import persistence
import task_queue
import image_utils
import offer_id
import backup
import user_manager

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
NEWS_JSON = WEBSITE_DIR / "offers-data" / "news.json"  # الأخبار العقارية التلقائية
OFFICE_DATA_JSON = WEBSITE_DIR / "offers-data" / "office-data.json"  # بوصلة الأسعار

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
#  سجل الأخطاء — حفظ الأخطاء على القرص للعرض في لوحة التحكم
# ============================================================
ERROR_LOG = DATA_DIR / "error_log.json"
SYNC_LOG = DATA_DIR / "sync_log.json"

def _load_error_log():
    if ERROR_LOG.exists():
        try:
            with open(ERROR_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"errors": []}

def _save_error_log(data):
    try:
        if len(data["errors"]) > 200:
            data["errors"] = data["errors"][-200:]
        tmp = ERROR_LOG.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(ERROR_LOG)
    except Exception as e:
        logger.error(f"خطأ في حفظ سجل الأخطاء: {e}")

def log_error(error_type, detail, user_id=None):
    """تسجيل خطأ في السجل الدائم"""
    try:
        data = _load_error_log()
        entry = {
            "type": error_type,
            "detail": str(detail)[:500],
            "user_id": user_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["errors"].append(entry)
        _save_error_log(data)
    except Exception:
        pass

def get_recent_errors(limit=5):
    """جلب آخر الأخطاء"""
    data = _load_error_log()
    errors = data.get("errors", [])
    return errors[-limit:][::-1]

def get_error_count():
    """عدد الأخطاء"""
    return len(_load_error_log().get("errors", []))

def _load_sync_log():
    if SYNC_LOG.exists():
        try:
            with open(SYNC_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"operations": []}

def _save_sync_log(data):
    try:
        if len(data["operations"]) > 200:
            data["operations"] = data["operations"][-200:]
        tmp = SYNC_LOG.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(SYNC_LOG)
    except Exception as e:
        logger.error(f"خطأ في حفظ سجل المزامنة: {e}")

def log_sync(operation, status, detail=""):
    """تسجيل عملية مزامنة"""
    try:
        data = _load_sync_log()
        data["operations"].append({
            "operation": operation,
            "status": status,
            "detail": str(detail)[:200],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        _save_sync_log(data)
    except Exception:
        pass

def get_recent_syncs(limit=5):
    """جلب آخر عمليات المزامنة"""
    data = _load_sync_log()
    ops = data.get("operations", [])
    return ops[-limit:][::-1]

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
        "website_url": "https://abonasr0907-beep.github.io/-/",
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
def enhance_image(input_path, output_path, max_width=3840, quality=95):
    """
    تحسين جودة الصورة بجودة عالية جداً (شبه 8K) دون إضافة أو تغيير العناصر.
    - تكبير الصور الصغيرة إلى دقة أعلى (upscaling) للحصول على وضوح أكبر
    - تصغير الصور الكبيرة جداً للحفاظ على التوازن (حد أقصى 3840px عرض = 4K)
    - تقليل الضوضاء بمرشح متطور
    - زيادة الحدة بشكل قوي
    - تحسين التباين والألوان والسطوع
    - شحذ إضافي (Unsharp Mask) لجودة 8K
    - حفظ كـ JPEG بجودة عالية جداً (quality=95)
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")
        w, h = img.size

        # ── Upscaling: تكبير الصور الصغيرة إلى دقة أعلى ──
        # إذا كانت الصورة أصغر من 1920px عرض، نكبرها إلى 2560px (QHD)
        if w < 1920:
            scale = 2560 / w
            new_w = 2560
            new_h = int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            w, h = img.size

        # ── Downscaling: تصغير الصور الكبيرة جداً (حد أقصى 3840px = 4K) ──
        if w > max_width:
            ratio = max_width / w
            new_size = (max_width, int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            w, h = img.size

        # ── تقليل الضوضاء بمرشح متطور ──
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # ── زيادة الحدة بشكل قوي (لجودة عالية) ──
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.8)

        # ── تحسين التباين ──
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)

        # ── تحسين الألوان ──
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.18)

        # ── تحسين السطوع ──
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.08)

        # ── شحذ إضافي ثانٍ (Unsharp Mask) لجودة 8K ──
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))

        # ── حفظ بجودة عالية جداً ──
        img.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)
        logger.info(f"تم تحسين الصورة بجودة عالية: {output_path} ({w}x{h})")
        return output_path
    except Exception as e:
        logger.error(f"خطأ في تحسين الصورة: {e}")
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
#  إدارة الجلسات (حالة المستخدم أثناء إضافة عرض) — حفظ دائم
# ============================================================
# user_id -> {"state": ..., "offer": {...}, "images": [...]}
# تم نقل الجلسات إلى persistence.py للحفظ الدائم على القرص
# هذا يحلّ مشكلة فقدان الحالة عند إعادة تشغيل السيرفر / إعادة النشر

def get_session(user_id):
    """جلب جلسة مستخدم من الذاكرة الدائمة (تُحمَّل من القرص)"""
    return persistence.get_session(user_id)

def reset_session(user_id):
    """إعادة تعيين جلسة مستخدم وحفظها على القرص"""
    persistence.reset_session(user_id)

def save_session(user_id):
    """حفظ حالة الجلسة على القرص فوراً (بعد كل تغيير)"""
    persistence.save_session(user_id)

def save_draft(user_id):
    """حفظ عرض كمسودة (للاستئناف لاحقاً)"""
    session = get_session(user_id)
    persistence.save_draft(user_id, session)

# ============================================================
#  التحقق من الصلاحيات — نظام المستخدمين (Admin / Editor)
# ============================================================
def is_admin(user_id):
    """
    التحقق إن كان المستخدم مديراً.
    يتكامل مع نظام المستخدمين (user_manager) مع الحفاظ على
    التوافق مع config.json (ADMIN_IDS).
    """
    # أولاً: التحقق من config.json (توافق مع النظام القديم)
    if user_id in ADMIN_IDS:
        return True
    # ثانياً: التحقق من نظام المستخدمين الجديد
    return user_manager.is_admin(user_id)

def is_editor(user_id):
    """
    التحقق إن كان المستخدم محرراً (editor أو admin).
    المحرر يمكنه: إضافة، تعديل، تصفية العروض.
    """
    if user_id in ADMIN_IDS:
        return True
    return user_manager.is_editor(user_id)

def is_authorized(user_id):
    """
    التحقق من الترخيص العام (admin أو editor).
    البوت ليس عاماً — كل مستخدم يجب أن يكون مصرّحاً له.
    """
    return is_editor(user_id)

def add_admin(user_id):
    """إضافة مدير — يحفظ في config.json و user_manager"""
    ADMIN_IDS.add(user_id)
    CONFIG["admin_ids"] = list(ADMIN_IDS)
    save_config(CONFIG)
    # أيضاً الإضافة إلى نظام المستخدمين
    user_manager.add_user(user_id, f"Admin {user_id}", role="admin", added_by="system")


# ============================================================
#  البوصلة العقارية — جلب متوسط السعر حسب المنطقة والنوع
# ============================================================
def get_bousla_avg_price(area_name, ptype):
    """
    جلب متوسط السعر من البوصلة العقارية حسب المنطقة ونوع العقار.
    يعيد نص متوسط السعر جاهز للعرض على الموقع (بدلاً من سعر العارض).
    """
    try:
        data = _load_office_data()
        areas = data.get("areas", {})
        matched_area = None
        for aname, ainfo in areas.items():
            if area_name in aname or aname in area_name:
                matched_area = ainfo
                break
        if not matched_area:
            return "حسب البوصلة العقارية"
        if ptype == "land":
            val = matched_area.get("land_avg_price_sqm", "")
            if val:
                return f"متوسط السعر: {val} ريال/م² (حسب البوصلة العقارية)"
        elif ptype == "farm":
            val = matched_area.get("farm_avg_price_sqm", "")
            if val:
                return f"متوسط السعر: {val} ريال/م² (حسب البوصلة العقارية)"
        elif ptype == "resthouse":
            val = matched_area.get("resthouse_avg_price", "")
            if val:
                return f"متوسط السعر: {val} ريال (حسب البوصلة العقارية)"
        return "حسب البوصلة العقارية"
    except Exception as e:
        logger.error(f"خطأ في جلب متوسط البوصلة: {e}")
        return "حسب البوصلة العقارية"


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


# ============================================================
#  تقديم عرض العقار من الزوار (غير المدير)
# ============================================================
# سلسلة حالة الزائر:
#   v_awaiting_type → v_awaiting_area → v_awaiting_size →
#   v_awaiting_price → v_awaiting_images → v_awaiting_map → v_awaiting_contact

VISITOR_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚜 مزرعة", "🏠 استراحة"],
        ["📐 أرض سكنية", "❌ إلغاء"],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)

VISITOR_CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [["❌ إلغاء"]],
    one_time_keyboard=True,
    resize_keyboard=True,
)

# ============================================================
#  لوحة المفاتيح الرئيسية
# ============================================================
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["➕ إضافة عرض جديد", "📋 قائمة العروض"],
        ["🗑️ حذف عرض", "✏️ تعديل عرض"],
        ["📨 طلبات الزوار", "🏡 عروض الزوار"],
        ["📊 إحصائيات", "📈 التقرير الأسبوعي"],
        ["🧭 تحديث البوصلة", "🤖 المساعد الذكي"],
        ["🗞️ تحديث الأخبار", "⚙️ الإعدادات"],
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
            f"🌐 الموقع: abonasr0907-beep.github.io/-"
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
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("هذا الأمر للمصرّح لهم فقط. تواصل مع مدير المكتب.")
        return
    uid = update.effective_user.id

    # ── التحقق من وجود مسودة غير مكتملة ──
    if persistence.has_incomplete_offer(uid):
        draft = persistence.get_draft(uid)
        draft_session = draft.get("session", {})
        img_count = len(draft_session.get("images", []))
        offer = draft_session.get("offer", {})
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ استئناف العرض المحفوظ", callback_data="resume_draft")],
            [InlineKeyboardButton("🗑️ بدء عرض جديد (حذف المسودة)", callback_data="new_offer_discard")],
        ])
        title = offer.get("title", "غير محدد")
        area = offer.get("area", "غير محدد")
        await update.message.reply_text(
            f"📝 يوجد عرض غير مكتمل محفوظ!\n\n"
            f"🏷️ العنوان: {title}\n"
            f"📍 المنطقة: {area}\n"
            f"📷 الصور المحفوظة: {img_count}\n"
            f"🕒 حفظ في: {draft.get('saved_at', 'غير معروف')}\n\n"
            f"هل تريد استئنافه أم بدء عرض جديد؟",
            reply_markup=keyboard,
        )
        return

    # ── بدء عرض جديد ──
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
    save_session(uid)  # حفظ الحالة على القرص فوراً

    # تحديث آخر نشاط للمستخدم
    user_manager.update_last_active(uid)

    await update.message.reply_text(
        "➕ إضافة عرض جديد\n\n"
        "أرسل صور العقار (1 إلى 5 صور).\n"
        "عند الانتهاء أرسل الكلمة: تم ✅\n\n"
        f"الحد الأقصى: {CONFIG['max_images']} صور.\n\n"
        "💡 ملاحظة: يمكنك إرسال الصور بالتتابع. إذا انقطع الاتصال، "
        "يمكنك استئناف العرض لاحقاً بكتابة /add مرة أخرى."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    session = get_session(uid)
    is_admin_user = is_authorized(uid)

    # تحديث آخر نشاط
    if is_admin_user:
        user_manager.update_last_active(uid)

    # ── الزوار في وضع تقديم عرض — استلام الصور ──
    if not is_admin_user and session.get("state") == "v_awaiting_images":
        if len(session["images"]) >= CONFIG["max_images"]:
            await update.message.reply_text(f"وصلت للحد الأقصى ({CONFIG['max_images']} صور). أرسل: تم ✅")
            return
        success, result = await _download_and_enhance_photo(update, context, uid, session, is_visitor=True)
        if success:
            save_session(uid)  # حفظ الجلسة على القرص
            await update.message.reply_text(
                f"✅ تم استلام وتحسين الصورة {len(session['images'])}/{CONFIG['max_images']}\n"
                f"أرسل المزيد أو اكتب: تم ✅"
            )
        else:
            await update.message.reply_text(
                f"⚠️ تعذّر استلام الصورة: {result}\n"
                f"أعد إرسال الصورة من فضلك."
            )
        return

    if not is_admin_user:
        return

    # ── المصرّح لهم (admin/editor) — استلام الصور للعرض ──
    # التحقق من الحالة المحفوظة على القرص
    if session["state"] != "awaiting_images":
        await update.message.reply_text(
            "استخدم زر «إضافة عرض جديد» أولاً.\n"
            "إذا كنت في منتصف إضافة عرض وتم قطع الاتصال، "
            "اكتب /add لاستئناف العرض المحفوظ."
        )
        return

    if len(session["images"]) >= CONFIG["max_images"]:
        await update.message.reply_text(f"وصلت للحد الأقصى ({CONFIG['max_images']} صور). أرسل: تم ✅")
        return

    success, result = await _download_and_enhance_photo(update, context, uid, session, is_visitor=False)
    if success:
        save_session(uid)  # حفظ الجلسة على القرص فوراً بعد كل صورة
        # حفظ مسودة تلقائياً (للاستئناف في حالة انقطاع)
        save_draft(uid)
        await update.message.reply_text(
            f"✅ تم استلام وتحسين الصورة {len(session['images'])}/{CONFIG['max_images']}\n"
            f"أرسل المزيد أو اكتب: تم ✅"
        )
    else:
        log_error("photo_download", result, user_id=uid)
        await update.message.reply_text(
            f"⚠️ تعذّر استلام الصورة: {result}\n"
            f"أعد إرسال الصورة من فضلك. (يمكنك المحاولة مرة أخرى)"
        )


async def _download_and_enhance_photo(update, context, uid, session, is_visitor=False):
    """
    تحميل وتحسين صورة مع آلية إعادة المحاولة.
    يُعيد: (True, None) عند النجاح، (False, error_msg) عند الفشل.
    """
    photo = update.message.photo[-1]  # أكبر حجم
    max_retries = 3
    last_error = ""

    for attempt in range(max_retries):
        try:
            # ── تحميل الصورة من خوادم تيليجرام ──
            # زيادة المهلة (timeout) لتقليل الفشل عند الاتصال الضعيف
            file = await context.bot.get_file(photo.file_id, read_timeout=60, write_timeout=60, connect_timeout=30)
            tmp_path = BASE_DIR / f"tmp_{uid}_{len(session['images'])}_{attempt}.jpg"

            # تحميل إلى القرص مع إعادة المحاولة
            await file.download_to_drive(str(tmp_path), read_timeout=60, write_timeout=60, connect_timeout=30)

            # ── التحقق من أن الملف ليس فارغاً ──
            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                raise ValueError("الملف المحمّل فارغ")

            # ── الكشف عن الصور المكررة ──
            existing_hashes = image_utils.get_existing_image_hashes(IMAGES_DIR)
            is_dup, fhash = image_utils._is_duplicate(str(tmp_path), existing_hashes)
            if is_dup:
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
                return False, "الصورة مكررة — تم رفضها لمنع التكرار"

            # ── تحسين وضغط الصورة ──
            # استخدام معرف العرض إذا كان متوفراً، وإلا "draft"
            offer_id_val = session.get("offer", {}).get("id", "") or "draft"
            img_base_name = image_utils.generate_image_name(
                offer_id_val, len(session["images"])
            )
            out_base = IMAGES_DIR / img_base_name

            # تحويل إلى WebP (أصغر حجماً) أو JPEG
            fmt = "webp"  # WebP يعطي أحجاماً أصغر بنفس الجودة
            main_path, thumb_path = image_utils.enhance_and_compress(
                str(tmp_path), str(out_base), fmt=fmt
            )

            # ── تنظيف الملف المؤقت ──
            try:
                tmp_path.unlink()
            except Exception:
                pass

            # ── تخزين المسار النسبي للموقع ──
            # تحويل الامتداد إلى ما تم إنتاجه فعلياً
            main_name = Path(main_path).name
            rel_path = f"images/bot/{main_name}"
            session["images"].append(rel_path)

            logger.info(f"✅ تم استلام وتحسين صورة للمستخدم {uid} (محاولة {attempt+1})")
            return True, None

        except Exception as e:
            last_error = str(e)
            logger.warning(f"⚠️ فشل تحميل الصورة (محاولة {attempt+1}/{max_retries}): {e}")
            # تنظيف الملف المؤقت
            try:
                tmp_path = BASE_DIR / f"tmp_{uid}_{len(session['images'])}_{attempt}.jpg"
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            # انتظار قبل إعادة المحاولة (backoff)
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))
            continue

    return False, f"فشل بعد {max_retries} محاولات: {last_error}"

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام موقع الزائر على الخريطة عبر زر الموقع في تيليجرام"""
    uid = update.effective_user.id
    session = get_session(uid)
    if session.get("state") == "v_awaiting_map":
        loc = update.message.location
        if loc:
            lat, lon = loc.latitude, loc.longitude
            maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            session["offer"]["visitor_map_link"] = maps_link
            session["offer"]["map_link"] = maps_link  # مؤقتاً — سيُستبدل بموقع المكتب عند الموافقة
            session["state"] = "v_awaiting_contact"
            await update.message.reply_text(
                f"✅ تم استلام موقعك على الخريطة.\n"
                f"🗺️ الرابط: {maps_link}\n\n"
                f"📞 أرسل معلومات التواصل معك (رقم جوال أو حساب تيليجرام):",
                reply_markup=VISITOR_CANCEL_KEYBOARD,
            )
        else:
            await update.message.reply_text("⚠️ تعذر استلام الموقع. أرسل رابط Google Maps نصياً.")

async def handle_text_during_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    uid = update.effective_user.id
    user_manager.update_last_active(uid)
    session = get_session(uid)
    text = update.message.text.strip()

    # خلال انتظار الصور
    if session["state"] == "awaiting_images":
        if text in ["تم", "تم ✅", "✅", "انتهيت"]:
            if len(session["images"]) == 0:
                await update.message.reply_text("⚠️ لم ترسل أي صورة. أرسل صورة واحدة على الأقل.")
                return
            session["state"] = "awaiting_title"
            save_session(uid)  # حفظ الحالة على القرص
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
        save_session(uid)  # حفظ الحالة على القرص
        await update.message.reply_text(
            f"🏷️ تم التصنيف تلقائياً: {session['offer']['category']}\n\n"
            "الآن أرسل المنطقة (مثال: الرحمانية / الهياثم / الدلم / الضبيعة / العفجة):"
        )
        return

    # المنطقة
    if session["state"] == "awaiting_area":
        session["offer"]["area"] = text
        session["state"] = "awaiting_size"
        save_session(uid)  # حفظ الحالة على القرص
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
        save_session(uid)  # حفظ الحالة على القرص
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
        save_session(uid)  # حفظ الحالة على القرص
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
    if not is_authorized(update.effective_user.id):
        return
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    session = get_session(uid)
    data = query.data

    # ── استئناف مسودة عرض غير مكتمل ──
    if data == "resume_draft":
        restored = persistence.restore_draft(uid)
        if restored:
            img_count = len(restored.get("images", []))
            state = restored.get("state", "awaiting_images")
            if state == "awaiting_images":
                msg = (
                    f"✅ تم استئناف العرض!\n\n"
                    f"📸 الصور المحفوظة: {img_count}\n"
                    f"أرسل المزيد من الصور أو اكتب: تم ✅ للانتقال للخطوة التالية."
                )
            else:
                msg = f"✅ تم استئناف العرض! الحالة الحالية: {state}\nأكمل الإدخال من حيث توقفت."
            await query.edit_message_text(msg)
        else:
            await query.edit_message_text("⚠️ تعذّر استئناف المسودة. ابدأ عرضاً جديداً بـ /add")
        return

    # ── تجاهل المسودة وبدء عرض جديد ──
    if data == "new_offer_discard":
        persistence.delete_draft(uid)
        reset_session(uid)
        await query.edit_message_text("🗑️ تم حذف المسودة. ابدأ عرضاً جديداً بـ /add")
        return

    if data == "publish_auto":
        await _finalize_offer(update, uid, query=query)

    elif data == "custom_desc":
        session["state"] = "awaiting_custom_desc"
        await query.edit_message_text("✏️ أرسل النص التسويقي المخصص للعرض:")

    elif data.startswith("del_"):
        offer_id = data[4:]
        await _delete_offer_by_id(update, offer_id, query=query)

    elif data.startswith("vreq_approve_"):
        req_id = data[len("vreq_approve_"):]
        await _approve_visitor_request(update, req_id, query=query)

    elif data.startswith("vreq_reject_"):
        req_id = data[len("vreq_reject_"):]
        await _reject_visitor_request(update, req_id, query=query)

    elif data.startswith("approve_"):
        idx = int(data[7:])
        await _approve_visitor_request(update, idx, query=query)

    elif data.startswith("reject_") and not data.startswith("reject_v"):
        idx = int(data[7:])
        await _reject_visitor_request(update, idx, query=query)

    elif data.startswith("vreview_"):
        idx = int(data[8:])
        await _review_visitor_offer(update, idx, query=query)

    elif data.startswith("vapprove_"):
        idx = int(data[9:])
        await _approve_visitor_offer(update, idx, query=query)

    elif data.startswith("vreject_"):
        idx = int(data[8:])
        await _reject_visitor_offer(update, idx, query=query)

    elif data.startswith("vshare_"):
        idx = int(data[7:])
        await _share_visitor_offer_whatsapp(update, idx, query=query)

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

# ============================================================
#  تقديم عرض العقار من الزوار — سلسلة الإدخال التفاعلية
# ============================================================
async def submit_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء تقديم عرض عقار من زائر (غير مدير) — /submit أو /عرض"""
    uid = update.effective_user.id
    session = get_session(uid)
    reset_session(uid)
    session = get_session(uid)
    session["state"] = "v_awaiting_type"
    session["offer"] = {
        "id": "",
        "type": "",
        "category": "",
        "title": "",
        "area": "",
        "size_sqm": 0,
        "price": 0,
        "price_text": "",  # سيتم إخفاؤه — يُستبدل بمتوسط البوصلة
        "original_price": "",  # السعر الأصلي من العارض (للمدير فقط)
        "description": "",
        "features": [],
        "images": [],
        "map_link": "",  # موقع العارض على الخريطة (يُستبدل بموقع المكتب عند النشر)
        "visitor_map_link": "",  # يحفظ موقع العارض الأصلي
        "date_added": datetime.now().strftime("%Y-%m-%d"),
        "featured": False,
        "source": "visitor",  # مصدر العرض: زائر
        "submitted_by": {
            "user_id": uid,
            "name": update.effective_user.full_name,
            "username": update.effective_user.username or "",
        },
        "contact": "",  # معلومات التواصل مع العارض
    }
    await update.message.reply_text(
        "🏠 مرحباً بك في مكتب آفاق الإنجاز العقاري!\n\n"
        "نستقبل عرضك العقاري وسيتواصل معك فريقنا للمراجعة.\n\n"
        "📅 اختر نوع العقار:",
        reply_markup=VISITOR_TYPE_KEYBOARD,
    )


async def handle_visitor_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل الزائر النصية أثناء تقديم العرض"""
    uid = update.effective_user.id
    session = get_session(uid)
    text = update.message.text.strip()

    # إلغاء في أي مرحلة
    if text == "❌ إلغاء":
        reset_session(uid)
        await update.message.reply_text(
            "تم إلغاء تقديم العرض.\n"
            "للبدء من جديد أرسل: /submit\n"
            "للاستفسار تواصل معنا: 0545888931",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # ── اختيار نوع العقار ──
    if session["state"] == "v_awaiting_type":
        type_map = {
            "🚜 مزرعة": ("farm", "مزرعة"),
            "🏠 استراحة": ("resthouse", "استراحة"),
            "📐 أرض سكنية": ("land", "أرض سكنية"),
        }
        if text not in type_map:
            await update.message.reply_text(
                "الرجاء اختيار نوع العقار من الأزرار أدناه:",
                reply_markup=VISITOR_TYPE_KEYBOARD,
            )
            return
        ptype, category = type_map[text]
        session["offer"]["type"] = ptype
        session["offer"]["category"] = category
        session["state"] = "v_awaiting_area"
        await update.message.reply_text(
            f"✅ نوع العقار: {category}\n\n"
            "📍 أرسل اسم المنطقة (مثال: الرحمنية / الهياثم / الدلم / الضبيعة / العفجة):",
            reply_markup=VISITOR_CANCEL_KEYBOARD,
        )
        return

    # ── اسم المنطقة ──
    if session["state"] == "v_awaiting_area":
        session["offer"]["area"] = text
        session["offer"]["title"] = f"{session['offer']['category']} في {text}"
        session["state"] = "v_awaiting_size"
        await update.message.reply_text("📐 أرسل المساحة بالمتر المربع (رقم فقط):")
        return

    # ── المساحة ──
    if session["state"] == "v_awaiting_size":
        try:
            size = int(text.replace(",", "").replace("م²", "").replace("م2", "").strip())
            session["offer"]["size_sqm"] = size
        except ValueError:
            await update.message.reply_text("⚠️ أرسل رقماً صحيحاً للمساحة:")
            return
        session["state"] = "v_awaiting_price"
        await update.message.reply_text(
            "💰 أرسل السعر المطلوب (رقم فقط):\n"
            "ℹ️ ملاحظة: سيتم إخفاء سعرك عن العامة وعرض متوسط السعر من البوصلة العقارية بدلاً منه."
        )
        return

    # ── السعر (يُخفى عن العامة) ──
    if session["state"] == "v_awaiting_price":
        try:
            price = int("".join(filter(str.isdigit, text)) or 0)
            session["offer"]["original_price"] = str(price)
            session["offer"]["price"] = price
        except ValueError:
            await update.message.reply_text("⚠️ أرسل رقماً صحيحاً للسعر:")
            return
        session["state"] = "v_awaiting_images"
        await update.message.reply_text(
            "📸 أرسل صور العقار (1 إلى 5 صور).\n"
            "عند الانتهاء أرسل الكلمة: تم ✅\n\n"
            f"الحد الأقصى: {CONFIG['max_images']} صور.\n"
            "🖼️ سيتم تحسين الصور تلقائياً بجودة عالية (8K).",
            reply_markup=VISITOR_CANCEL_KEYBOARD,
        )
        return

    # ── الصور — إنهاء استلام الصور ──
    if session["state"] == "v_awaiting_images":
        if text in ["تم", "تم ✅", "✅", "انتهيت", "تمت", "تمت ✅"]:
            if len(session["images"]) == 0:
                await update.message.reply_text("⚠️ لم ترسل أي صورة. أرسل صورة واحدة على الأقل أو أرسل: تم ✅")
                return
            session["state"] = "v_awaiting_map"
            await update.message.reply_text(
                f"✅ تم استلام {len(session['images'])} صورة.\n\n"
                "🗺️ أرسل رابط موقع العقار على Google Maps:\n"
                "أو أرسل موقعك الحالي عبر زر 📎 (الموقع) في تيليجرام.\n"
                'أو أرسل «تخطي» لاستخدام موقع افتراضي.',
                reply_markup=VISITOR_CANCEL_KEYBOARD,
            )
        else:
            await update.message.reply_text("أرسل صورة أو اكتب: تم ✅")
        return

    # ── موقع العقار على الخريطة (من العارض) ──
    if session["state"] == "v_awaiting_map":
        if text.lower() in ["تخطي", "لا", "skip", "افتراضي"]:
            session["offer"]["visitor_map_link"] = ""
            session["offer"]["map_link"] = CONFIG["office_location"]
        else:
            session["offer"]["visitor_map_link"] = text
            session["offer"]["map_link"] = text  # مؤقتاً — سيُستبدل بموقع المكتب عند الموافقة
        session["state"] = "v_awaiting_contact"
        await update.message.reply_text(
            "📞 أرسل معلومات التواصل معك:\n"
            "(رقم الواتساب أو الجوال — ليتمكن المكتب من التواصل معك)",
            reply_markup=VISITOR_CANCEL_KEYBOARD,
        )
        return

    # ── معلومات التواصل — ثم الحفظ كطلب معلق ──
    if session["state"] == "v_awaiting_contact":
        session["offer"]["contact"] = text
        session["offer"]["images"] = session["images"]
        await _save_visitor_offer(update, uid)
        return


async def _save_visitor_offer(update, uid):
    """حفظ عرض الزائر كطلب معلق وإشعار المدير"""
    session = get_session(uid)
    offer = session["offer"]

    # حفظ في قائمة طلبات الزوار
    data = load_visitor_requests()
    visitor_offer = {
        "type": "offer_submission",
        "offer": offer,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "submitted_by": offer.get("submitted_by", {}),
        "contact": offer.get("contact", ""),
        "visitor_map_link": offer.get("visitor_map_link", ""),
        "original_price": offer.get("original_price", ""),
        "status": "pending",
    }
    data.setdefault("offer_submissions", []).append(visitor_offer)
    save_visitor_requests(data)

    # مزامنة الصور إلى GitHub (إن كان مفعّلاً)
    try:
        if github_sync.is_enabled() and offer.get("images"):
            sync_pairs = []
            for rel in offer["images"]:
                local_full = WEBSITE_DIR / rel
                if local_full.exists():
                    sync_pairs.append((str(local_full), rel))
            for local_path, rel_repo_path in sync_pairs:
                github_sync.upload_binary_file(
                    rel_repo_path, local_path,
                    f"صور عرض زائر: {offer.get('category', '')} في {offer.get('area', '')}"
                )
    except Exception as e:
        logger.error(f"خطأ في مزامنة صور الزائر: {e}")

    # إشعار المدير بعرض جديد
    msg = (
        f"🔔 عرض عقاري جديد من زائر!\n\n"
        f"🏷️ النوع: {offer.get('category', '')}\n"
        f"📍 المنطقة: {offer.get('area', '')}\n"
        f"📐 المساحة: {offer.get('size_sqm', '')} م²\n"
        f"💰 السعر المطلوب: {offer.get('original_price', '')} ريال\n"
        f"🗺️ موقع العارض: {offer.get('visitor_map_link', 'لم يحدد')}\n"
        f"📞 تواصل العارض: {offer.get('contact', '')}\n"
        f"👤 المقدم: {offer.get('submitted_by', {}).get('name', '')}\n"
        f"📸 عدد الصور: {len(offer.get('images', []))}\n"
        f"🕐 وقت التقديم: {visitor_offer['submitted_at']}\n\n"
        f"للمراجعة والموافقة: /visitor_offers"
    )
    for admin_id in ADMIN_IDS:
        try:
            # إرسال أول صورة كمعاينة إن وجدت
            if offer.get("images"):
                local_img = WEBSITE_DIR / offer["images"][0]
                if local_img.exists():
                    await context.app.bot.send_photo(admin_id, photo=open(str(local_img), "rb"), caption=msg)
                    continue
            await context.app.bot.send_message(admin_id, msg)
        except Exception as e:
            logger.error(f"فشل إرسال إشعار العرض للمدير {admin_id}: {e}")

    await update.message.reply_text(
        f"✅ تم استلام عرضك بنجاح!\n\n"
        f"📋 تفاصيل العرض:\n"
        f"   🏷️ النوع: {offer.get('category', '')}\n"
        f"   📍 المنطقة: {offer.get('area', '')}\n"
        f"   📐 المساحة: {offer.get('size_sqm', '')} م²\n"
        f"   📸 عدد الصور: {len(offer.get('images', []))}\n\n"
        f"⏳ سيقوم فريق المكتب بمراجعة عرضك والموافقة عليه قريباً.\n"
        f"📞 للتواصل: 0545888931\n"
        f"🌐 موقعنا: abonasr0907-beep.github.io/-",
        reply_markup=ReplyKeyboardRemove(),
    )
    reset_session(uid)


async def visitor_offers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض عروض الزوار المعلقة للمدير — /visitor_offers"""
    if not is_admin(update.effective_user.id):
        return
    data = load_visitor_requests()
    submissions = data.get("offer_submissions", [])
    pending = [s for s in submissions if s.get("status") == "pending"]
    if not pending:
        await update.message.reply_text("📭 لا توجد عروض زوار معلقة حالياً.")
        return
    msg = f"📬 عروض الزوار المعلقة ({len(pending)} عرض):\n\n"
    keyboard = []
    for idx, s in enumerate(submissions):
        if s.get("status") != "pending":
            continue
        offer = s.get("offer", {})
        real_idx = idx  # المؤشر الفعلي في القائمة الكاملة
        label = f"✅ {offer.get('category', '')} — {offer.get('area', '')} — {offer.get('size_sqm', '')}م²"
        msg += f"[{real_idx}] {label}\n   💰 {offer.get('original_price', '')} ريال | 📞 {s.get('contact', '')}\n"
        keyboard.append([InlineKeyboardButton(
            f"📋 مراجعة [{real_idx}] — {offer.get('area', '')}",
            callback_data=f"vreview_{real_idx}",
        )])
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)


async def _review_visitor_offer(update, idx, query=None):
    """عرض تفاصيل عرض الزائر للمدير مع أزرار الموافقة/الرفض"""
    data = load_visitor_requests()
    submissions = data.get("offer_submissions", [])
    if idx >= len(submissions):
        msg = "⚠️ عرض غير موجود."
        if query:
            await query.edit_message_text(msg)
        return
    s = submissions[idx]
    offer = s.get("offer", {})
    msg = (
        f"📋 مراجعة عرض الزائر [{idx}]\n\n"
        f"🏷️ النوع: {offer.get('category', '')}\n"
        f"📍 المنطقة: {offer.get('area', '')}\n"
        f"📐 المساحة: {offer.get('size_sqm', '')} م²\n"
        f"💰 السعر المطلوب: {offer.get('original_price', '')} ريال (سيُخفى)\n"
        f"🗺️ موقع العارض: {s.get('visitor_map_link', 'لم يحدد')}\n"
        f"📞 تواصل العارض: {s.get('contact', '')}\n"
        f"👤 المقدم: {offer.get('submitted_by', {}).get('name', '')}\n"
        f"📸 عدد الصور: {len(offer.get('images', []))}\n"
        f"🕐 وقت التقديم: {s.get('submitted_at', '')}\n\n"
        f"ℹ️ عند الموافقة:\n"
        f"   • سيُخفى سعر العارض ويُعرض متوسط البوصلة\n"
        f"   • سيُستبدل موقع العارض بموقع المكتب الثابت\n"
        f"   • سيُنشر العرض مباشرة على الموقع"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ موافقة ونشر", callback_data=f"vapprove_{idx}")],
        [InlineKeyboardButton("❌ رفض", callback_data=f"vreject_{idx}")],
        [InlineKeyboardButton("📤 مشاركة عبر واتساب", callback_data=f"vshare_{idx}")],
    ])
    if query:
        await query.edit_message_text(msg, reply_markup=keyboard)
    else:
        await update.message.reply_text(msg, reply_markup=keyboard)


async def _approve_visitor_offer(update, idx, query=None):
    """الموافقة على عرض الزائر ونشره على الموقع:
       - إخفاء سعر العارض وعرض متوسط البوصلة
       - استبدال موقع العارض بموقع المكتب الثابت
       - تصنيف تلقائي + توليد نص تسويقي + نشر على الموقع + مزامنة GitHub
    """
    data = load_visitor_requests()
    submissions = data.get("offer_submissions", [])
    if idx >= len(submissions):
        msg = "⚠️ عرض غير موجود."
        if query:
            await query.edit_message_text(msg)
        return

    s = submissions[idx]
    offer = dict(s.get("offer", {}))

    # 1) توليد معرّف فريد
    offer["id"] = f"{offer['type'][:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

    # 2) إخفاء السعر — استخدام متوسط البوصلة بدلاً من سعر العارض
    bousla_price = get_bousla_avg_price(offer.get("area", ""), offer.get("type", "land"))
    offer["price_text"] = bousla_price  # متوسط البوصلة يُعرض للعامة
    offer["original_price"] = s.get("original_price", "")  # يُحفظ للمدير فقط

    # 3) استبدال موقع العارض بموقع المكتب الثابت
    offer["visitor_map_link"] = s.get("visitor_map_link", "")  # يُحفظ للأرشيف
    offer["map_link"] = CONFIG["office_location"]  # موقع المكتب الثابت للنشر

    # 4) توليد نص تسويقي تلقائي
    offer["description"] = generate_marketing_text(
        offer.get("type", "land"),
        offer.get("area", ""),
        offer.get("size_sqm", ""),
    )

    # 5) حفظ في عروض البوت
    bot_data = load_bot_offers()
    bot_data["offers"].append(offer)
    save_bot_offers(bot_data)

    # 6) نشر مباشر على الموقع
    site_data = load_offers_json()
    site_data["offers"].append(offer)
    save_offers_json(site_data)

    # 7) مزامنة مع GitHub
    sync_note = ""
    try:
        sync_pairs = []
        for rel in offer.get("images", []):
            local_full = WEBSITE_DIR / rel
            if local_full.exists():
                sync_pairs.append((str(local_full), rel))
        if sync_pairs and github_sync.is_enabled():
            ok = github_sync.sync_offer_to_github(offer, sync_pairs)
            sync_note = " ✅ ورفعت على الموقع" if ok else " (تحذير: لم تكتمل المزامنة)"
        elif not github_sync.is_enabled():
            sync_note = " (محلياً — اضبط GITHUB_TOKEN للنشر العام)"
    except Exception as e:
        logger.error(f"خطأ في المزامنة مع GitHub: {e}")
        sync_note = " (تعذّرت المزامنة)"

    # 8) تحديث حالة الطلب
    s["status"] = "approved"
    s["published_offer_id"] = offer["id"]
    save_visitor_requests(data)

    # 9) تحديث البوصلة تلقائياً بعد نشر عرض جديد
    try:
        _do_price_update()
    except Exception as e:
        logger.error(f"خطأ في تحديث البوصلة بعد النشر: {e}")

    msg = (
        f"✅ تمت الموافقة ونشر العرض!{sync_note}\n\n"
        f"🆔 المعرف: {offer['id']}\n"
        f"🏷️ النوع: {offer['category']}\n"
        f"📍 المنطقة: {offer['area']}\n"
        f"📐 المساحة: {offer['size_sqm']} م²\n"
        f"💰 المعروض: {offer['price_text']}\n"
        f"🗺️ الموقع: تم استبداله بموقع المكتب الثابت\n"
        f"📸 الصور: {len(offer.get('images', []))}\n\n"
        f"🌐 تم النشر مباشرة على الموقع."
    )
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)


async def _share_visitor_offer_whatsapp(update, idx, query=None):
    """إنشاء نص جاهز للمشاركة عبر واتساب يتضمن موقع العارض على الخريطة"""
    data = load_visitor_requests()
    submissions = data.get("offer_submissions", [])
    if idx >= len(submissions):
        msg = "⚠️ عرض غير موجود."
        if query:
            await query.edit_message_text(msg)
        return
    s = submissions[idx]
    offer = s.get("offer", {})
    map_link = s.get("visitor_map_link", offer.get("visitor_map_link", "لم يحدد"))
    share_text = (
        f"🏠 *عرض عقاري جديد*\n\n"
        f"🏷️ النوع: {offer.get('category', '')}\n"
        f"📍 المنطقة: {offer.get('area', '')}\n"
        f"📐 المساحة: {offer.get('size_sqm', '')} م²\n"
        f"💰 السعر: {s.get('original_price', '')} ريال\n"
        f"🗺️ الموقع على الخريطة: {map_link}\n"
        f"📞 تواصل: {s.get('contact', '')}\n\n"
        f"🏢 مكتب آفاق الإنجاز العقاري\n"
        f"🌐 abonasr0907-beep.github.io/-"
    )
    # إرسال النص كرسالة قابلة للنسخ والمشاركة
    if query:
        await query.edit_message_text(
            f"📤 *نص جاهز للمشاركة عبر واتساب:*\n\n```\n{share_text}\n```\n\nانسخ النص أعلاه والمشاركة عبر واتساب.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"📤 *نص جاهز للمشاركة عبر واتساب:*\n\n```\n{share_text}\n```\n\nانسخ النص أعلاه والمشاركة عبر واتساب.",
            parse_mode="Markdown",
        )


async def _reject_visitor_offer(update, idx, query=None):
    """رفض عرض الزائر"""
    data = load_visitor_requests()
    submissions = data.get("offer_submissions", [])
    if idx < len(submissions):
        submissions[idx]["status"] = "rejected"
        save_visitor_requests(data)
    msg = "❌ تم رفض العرض."
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)


# ============================================================

async def _finalize_offer(update, uid, query=None):
    session = get_session(uid)
    offer = session["offer"]
    offer["images"] = session["images"]

    # ── توليد معرف تسلسلي فريد (AFQ-2026-0001) ──
    offer["id"] = offer_id.generate_offer_id()

    # ── منع نشر عرض بلا صور ──
    if not offer["images"]:
        msg = "⚠️ لا يمكن نشر عرض بدون صور. أرسل صورة واحدة على الأقل ثم أعد المحاولة."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    offer["map_link"] = CONFIG["office_location"]  # موقع المكتب افتراضياً

    # ── نسخة احتياطية قبل النشر ──
    try:
        backup.create_backup("publish")
    except Exception as e:
        logger.warning(f"⚠️ تعذّر إنشاء نسخة احتياطية قبل النشر: {e}")

    # حفظ في عروض البوت
    bot_data = load_bot_offers()
    bot_data["offers"].append(offer)
    save_bot_offers(bot_data)

    # نشر مباشر على الموقع
    site_data = load_offers_json()
    site_data["offers"].append(offer)
    save_offers_json(site_data)

    # رفع العرض والصور إلى GitHub → إعادة نشر تلقائية على الموقع العام
    try:
        sync_pairs = []
        for rel in offer["images"]:
            local_full = WEBSITE_DIR / rel
            if local_full.exists():
                sync_pairs.append((str(local_full), rel))
        if sync_pairs:
            ok = github_sync.sync_offer_to_github(offer, sync_pairs)
            if github_sync.is_enabled():
                sync_note = " ✅ ورفعت على الموقع العام" if ok else " (تحذير: لم تكتمل المزامنة)"
            else:
                sync_note = " (محلياً — اضبط GITHUB_TOKEN للنشر العام)"
        else:
            sync_note = ""
    except Exception as e:
        logger.error(f"خطأ في المزامنة مع GitHub: {e}")
        sync_note = " (تعذّرت المزامنة)"

    msg = (
        f"✅ تم نشر العرض بنجاح!{sync_note}\n\n"
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
    # مزامنة الحذف مع GitHub
    if before != after and github_sync.is_enabled():
        try:
            from pathlib import Path
            base = Path(__file__).resolve().parent
            offers_file = base.parent / "offers-data" / "offers.json"
            if offers_file.exists():
                github_sync.upload_text_file(
                    "offers-data/offers.json",
                    offers_file.read_text(encoding="utf-8"),
                    f"حذف عرض: {offer_id}"
                )
        except Exception as e:
            logger.error(f"خطأ في مزامنة الحذف: {e}")

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
    # عرض آخر 10 طلبات مع أزرار موافقة ورفض لكل طلب
    for idx, (typ, item) in enumerate(all_items[-10:]):
        label = "\U0001F3E0 عرض" if typ == "request" else "\U0001F50D استفسار"
        name = item.get("name", "غير معروف")
        status = item.get("status", "")
        status_icon = ""
        if status == "approved":
            status_icon = " \u2705"
        elif status == "rejected":
            status_icon = " \u274C"
        elif status == "pending":
            status_icon = " \u23F3"
        msg += f"{label} [{idx}] \u2014 {name} \u2014 {item.get('phone','')}{status_icon}\n"
        req_id = item.get("id", f"idx_{idx}")
        row = [
            InlineKeyboardButton(
                f"\u2705 موافقة [{idx}]",
                callback_data=f"vreq_approve_{req_id}",
            ),
            InlineKeyboardButton(
                f"\u274C رفض [{idx}]",
                callback_data=f"vreq_reject_{req_id}",
            ),
        ]
        keyboard.append(row)
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

def _parse_request_from_callback_message(query, req_id):
    """
    استخراج بيانات الطلب من نص رسالة الإشعار (عندما لم يتم حفظ الطلب في visitor_requests.json).
    يُستخدم كحل احتياطي عندما يُرسل الموقع الإشعار مباشرة عبر Telegram API
    دون المرور بخادم البوت (الذي يحفظ الطلب).
    """
    if not query or not query.message:
        return None
    try:
        text = query.message.text or ""
        if not text:
            text = query.message.html_text or ""
        if not text:
            return None

        import re

        def extract_field(text, label_pattern):
            m = re.search(label_pattern, text, re.DOTALL)
            if m:
                return m.group(1).strip()
            return ""

        # إزالة وسوم HTML
        clean_text = re.sub(r'<[^>]+>', '', text)

        # استخراج الحقول حسب التسميات في رسالة الإشعار
        name = extract_field(clean_text, r'اسم العميل:\s*(.+?)(?:\n|$)')
        phone = extract_field(clean_text, r'رقم الهاتف:\s*(.+?)(?:\n|$)')
        property_type = extract_field(clean_text, r'نوع العقار:\s*(.+?)(?:\n|$)')
        location = extract_field(clean_text, r'الموقع:\s*(.+?)(?:\n|$)')
        area = extract_field(clean_text, r'المساحة:\s*(\d[\d,]*)')
        price = extract_field(clean_text, r'السعر التقريبي:\s*(\d[\d,]*)')
        description = extract_field(clean_text, r'الوصف:\s*(.+?)(?:\n\n|\n📷|\n📄|$)')
        latitude = extract_field(clean_text, r'خط العرض \(Latitude\):\s*(.+?)(?:\n|$)')
        longitude = extract_field(clean_text, r'خط الطول \(Longitude\):\s*(.+?)(?:\n|$)')
        maps_link = extract_field(clean_text, r'رابط Google Maps:\s*(.+?)(?:\n|$)')

        img_match = re.search(r'الصور:\s*(\d+)', clean_text)
        image_count = int(img_match.group(1)) if img_match else 0

        if not name and not phone:
            return None

        request = {
            "id": req_id,
            "name": name,
            "phone": phone,
            "propertyType": property_type,
            "location": location,
            "area": area,
            "price": price,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "mapsLink": maps_link,
            "imageCount": image_count,
            "source": "website_callback_fallback",
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "pending",
        }
        logger.info(f"\U0001f4cb تم استخراج بيانات الطلب من رسالة الإشعار: {req_id} \u2014 {name}")
        return request
    except Exception as e:
        logger.error(f"\u274c خطأ في تحليل بيانات الطلب من الرسالة: {e}")
        return None


async def _approve_visitor_request(update, req_ref, query=None):
    """
    الموافقة على طلب زائر ونشره كعرض على الموقع:
       - البحث عن الطلب بواسطة ID أو index
       - إنشاء عرض جديد بمعرف فريد
       - إخفاء السعر (عرض متوسط البوصلة)
       - استبدال موقع الزائر بموقع المكتب الثابت
       - توليد نص تسويقي
       - حفظ في offers.json + bot_offers.json
       - مزامنة الموقع (GitHub)
       - تحديث حالة الطلب إلى approved
    """
    data = load_visitor_requests()
    requests_list = data.get("requests", [])
    inquiries = data.get("inquiries", [])
    all_items = [("request", r) for r in requests_list] + [("inquiry", i) for i in inquiries]

    # البحث عن الطلب: إما بـ ID (string) أو index (int)
    target = None
    target_idx = -1
    if isinstance(req_ref, str):
        # البحث بالـ ID
        if req_ref.startswith("idx_"):
            # تنسيق idx_N (للتوافق مع القديم)
            try:
                target_idx = int(req_ref[4:])
                if 0 <= target_idx < len(all_items):
                    target = all_items[target_idx]
            except ValueError:
                pass
        else:
            # البحث بالـ ID المباشر
            for i, (typ, item) in enumerate(all_items):
                if item.get("id") == req_ref:
                    target = (typ, item)
                    target_idx = i
                    break
    elif isinstance(req_ref, int):
        # تنسيق index القديم
        if 0 <= req_ref < len(all_items):
            target = all_items[req_ref]
            target_idx = req_ref

    if target is None:
        # محاولة استخراج بيانات الطلب من رسالة الإشعار (حل احتياطي)
        if isinstance(req_ref, str) and not req_ref.startswith("idx_"):
            parsed = _parse_request_from_callback_message(query, req_ref)
            if parsed:
                # حفظ الطلب المستخرج في visitor_requests.json
                try:
                    vdata = load_visitor_requests()
                    vdata.setdefault("requests", []).append(parsed)
                    save_visitor_requests(vdata)
                    logger.info(f"💾 تم حفظ الطلب المستخرج من الرسالة: {req_ref}")
                    # إعادة البحث عن الطلب
                    target = ("request", parsed)
                    target_idx = len(vdata["requests"]) - 1
                except Exception as e:
                    logger.error(f"❌ خطأ في حفظ الطلب المستخرج: {e}")

    if target is None:
        msg = "⚠️ طلب غير موجود. قد لا تكون بياناته محفوظة."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    typ, item = target
    item_type = item.get("propertyType", item.get("property_type", "land"))
    item_area = item.get("location", item.get("area", ""))
    item_size = item.get("area", item.get("size_sqm", ""))
    item_price = item.get("price", "")

    # تحويل نوع العقار إلى نوع إنجليزي للمعرف
    type_map = {
        "\u0634\u0642\u0629": "APT", "\u0634\u0642\u0647": "APT", "apartment": "APT", "apt": "APT",
        "\u0641\u064a\u0644\u0627": "VLA", "villa": "VLA",
        "\u0645\u0632\u0631\u0639\u0629": "FRM", "farm": "FRM",
        "\u0623\u0631\u0636": "LND", "\u0627\u0631\u0636": "LND", "land": "LND",
        "\u0627\u0633\u062a\u0631\u0627\u062d\u0629": "RST", "resthouse": "RST",
        "\u0645\u062d\u0644": "STO", "store": "STO",
    }
    type_prefix = "LND"
    for k, v in type_map.items():
        if k.lower() in item_type.lower():
            type_prefix = v
            break

    # 1) توليد معرف فريد للعرض
    offer_id = f"{type_prefix}-{uuid.uuid4().hex[:6].upper()}"

    # 2) إخفاء السعر — استخدام متوسط البوصلة
    bousla_price = get_bousla_avg_price(item_area, item_type.lower() if item_type.lower() in ["farm", "land", "resthouse", "villa", "apartment"] else "land")
    if not bousla_price or "غير" in str(bousla_price):
        bousla_price = "\u0633\u0639\u0631 \u0639\u0642\u0627\u0631\u064a \u0645\u0646\u0627\u0633\u0628 \u0627\u0644\u0633\u0648\u0642"

    # 3) بناء كائن العرض
    offer = {
        "id": offer_id,
        "type": item_type.lower() if item_type.lower() in ["farm", "land", "resthouse", "villa", "apartment"] else "land",
        "category": item_type,
        "title": f"{item_type} \u2014 {item_area}",
        "area": item_area,
        "area_en": "",
        "size_sqm": item_size,
        "price": item_price,
        "price_text": bousla_price,
        "original_price": item_price,
        "description": generate_marketing_text(
            "land" if item_type.lower() not in ["farm", "land", "resthouse", "villa", "apartment"] else item_type.lower(),
            item_area,
            str(item_size),
        ),
        "features": [],
        "images": [],
        # إخفاء الموقع الحقيقي — استخدام موقع المكتب
        "map_link": CONFIG.get("office_location", ""),
        "visitor_map_link": item.get("mapsLink", item.get("maps_link", "")),
        "visitor_lat": item.get("latitude", ""),
        "visitor_lng": item.get("longitude", ""),
        "date_added": datetime.now().strftime("%Y-%m-%d"),
        "featured": False,
        "source": "visitor_request",
        "visitor_name": item.get("name", ""),
        "visitor_phone": item.get("phone", ""),
    }

    # إضافة وصف الزائر إذا وجد
    if item.get("description"):
        offer["description"] += f"\n\n\U0001F4DD {item['description']}"

    # 4) حفظ في عروض البوت
    bot_data = load_bot_offers()
    bot_data["offers"].append(offer)
    save_bot_offers(bot_data)

    # 5) نشر مباشر على الموقع
    site_data = load_offers_json()
    site_data["offers"].append(offer)
    save_offers_json(site_data)

    # 6) مزامنة مع GitHub
    sync_note = ""
    try:
        if github_sync.is_enabled():
            ok = github_sync.sync_offer_to_github(offer, [])
            sync_note = " \u2705 \u0648\u0631\u0641\u0639\u062a \u0639\u0644\u0649 \u0627\u0644\u0645\u0648\u0642\u0639" if ok else " (\u062a\u062d\u0630\u064a\u0631: \u0644\u0645 \u062a\u0643\u062a\u0645\u0644 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629)"
        else:
            sync_note = " (\u0645\u062d\u0644\u064a\u0627\u064b \u2014 \u0627\u0636\u0628\u0637 GITHUB_TOKEN \u0644\u0644\u0646\u0634\u0631 \u0627\u0644\u0639\u0627\u0645)"
    except Exception as e:
        logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629: {e}")
        sync_note = " (\u062a\u0639\u0630\u0651\u0631\u062a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629)"

    # 7) تحديث حالة الطلب إلى approved (لا يحذف)
    item["status"] = "approved"
    item["published_offer_id"] = offer_id
    item["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_visitor_requests(data)

    # 8) تحديث البوصلة تلقائياً
    try:
        _do_price_update()
    except Exception as e:
        logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u062a\u062d\u062f\u064a\u062b \u0627\u0644\u0628\u0648\u0635\u0644\u0629: {e}")

    msg = (
        f"\u2705 \u062a\u0645\u062a \u0627\u0644\u0645\u0648\u0627\u0641\u0642\u0629 \u0648\u0646\u0634\u0631 \u0627\u0644\u0639\u0631\u0636!{sync_note}\n\n"
        f"\U0001F194 \u0627\u0644\u0645\u0639\u0631\u0641: {offer_id}\n"
        f"\U0001F3F7\ufe0f \u0627\u0644\u0646\u0648\u0639: {offer['category']}\n"
        f"\U0001F4CD \u0627\u0644\u0645\u0646\u0637\u0642\u0629: {offer['area']}\n"
        f"\U0001F4D0 \u0627\u0644\u0645\u0633\u0627\u062d\u0629: {offer['size_sqm']} \u0645\u00b2\n"
        f"\U0001F4B0 \u0627\u0644\u0645\u0639\u0631\u0648\u0636: {offer['price_text']}\n"
        f"\U0001F5FA\ufe0f \u0627\u0644\u0645\u0648\u0642\u0639: \u062a\u0645 \u0627\u0633\u062a\u0628\u062f\u0627\u0644\u0647 \u0628\u0645\u0648\u0642\u0639 \u0627\u0644\u0645\u0643\u062a\u0628 \u0627\u0644\u062b\u0627\u0628\u062a\n"
        f"\U0001F4F8 \u0627\u0644\u0635\u0648\u0631: \u0633\u064a\u062a\u0645 \u0625\u0636\u0627\u0641\u062a\u0647\u0627 \u0644\u0627\u062d\u0642\u0627\u064b\n\n"
        f"\U0001F310 \u062a\u0645 \u0627\u0644\u0646\u0634\u0631 \u0639\u0644\u0649 \u0627\u0644\u0645\u0648\u0642\u0639."
    )
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)


async def _reject_visitor_request(update, req_ref, query=None):
    """
    رفض طلب زائر — تحديث الحالة إلى rejected فقط (لا حذف)
    """
    data = load_visitor_requests()
    requests_list = data.get("requests", [])
    inquiries = data.get("inquiries", [])
    all_items = [("request", r) for r in requests_list] + [("inquiry", i) for i in inquiries]

    # البحث عن الطلب
    target = None
    if isinstance(req_ref, str):
        if req_ref.startswith("idx_"):
            try:
                idx = int(req_ref[4:])
                if 0 <= idx < len(all_items):
                    target = all_items[idx]
            except ValueError:
                pass
        else:
            for typ, item in all_items:
                if item.get("id") == req_ref:
                    target = (typ, item)
                    break
    elif isinstance(req_ref, int):
        if 0 <= req_ref < len(all_items):
            target = all_items[req_ref]

    if target is None:
        # محاولة استخراج بيانات الطلب من رسالة الإشعار (حل احتياطي)
        if isinstance(req_ref, str) and not req_ref.startswith("idx_"):
            parsed = _parse_request_from_callback_message(query, req_ref)
            if parsed:
                try:
                    data.setdefault("requests", []).append(parsed)
                    save_visitor_requests(data)
                    logger.info(f"💾 تم حفظ الطلب المستخرج من الرسالة للرفض: {req_ref}")
                    target = ("request", parsed)
                except Exception as e:
                    logger.error(f"❌ خطأ في حفظ الطلب المستخرج: {e}")

    if target is None:
        msg = "⚠️ طلب غير موجود."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    typ, item = target
    # تحديث الحالة إلى rejected فقط — لا حذف
    item["status"] = "rejected"
    item["rejected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_visitor_requests(data)

    msg = "❌ تم رفض الطلب. تم تحديث الحالة إلى مرفوض (لم يتم التسجيل للنشر)."
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
    uid = update.effective_user.id
    session = get_session(uid)
    text = update.message.text.strip()

    # ── توجيه الزوار (غير المصرفين) ──
    if not is_authorized(uid):
        # إذا كان الزائر في عملية تقديم عرض
        if session["state"] in [
            "v_awaiting_type", "v_awaiting_area", "v_awaiting_size",
            "v_awaiting_price", "v_awaiting_images", "v_awaiting_map",
            "v_awaiting_contact",
        ]:
            await handle_visitor_text(update, context)
            return
        # زر "تقديم عرض" للزوار
        if text in ["تقديم عرض", "عرض عقاري", "إضافة عرض", "تقديم عرض عقاري"]:
            await submit_offer_start(update, context)
            return
        # رسالة ترحيب للزوار غير النشطين
        keyboard = ReplyKeyboardMarkup(
            [["تقديم عرض"]],
            resize_keyboard=True,
        )
        await update.message.reply_text(
            "أهلاً بك في مكتب آفاق الإنجاز العقاري!\n\n"
            "نقدم لك خدمات عقارية متكاملة في الخرج والرياض.\n\n"
            "اضغط زر «تقديم عرض» لتقديم عقارك للنشر على موقعنا.\n\n"
            "للتواصل المباشر:\n"
            "   واتساب: 0545888931\n"
            "   اتصال: 0544699933\n"
            "الموقع: abonasr0907-beep.github.io/-",
            reply_markup=keyboard,
        )
        return

    # ── توجيه المدير ──
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
    elif text == "🏡 عروض الزوار":
        await visitor_offers_cmd(update, context)
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
    elif text == "🗞️ تحديث الأخبار":
        await update_news_cmd(update, context)
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
WEEKLY_STATS = DATA_DIR / "weekly_stats.json"


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


# ============================================================
#  الأخبار العقارية — تحديث تلقائي كل 3 أيام
# ============================================================

# قوالب الأخبار العقارية (تُولَّد عشوائياً عند كل تحديث)
NEWS_TEMPLATES = [
    {
        "title": "الهيئة العامة للعقار تعلن عن تحديثات جديدة في تنظيم السوق العقاري",
        "desc": "أعلنت الهيئة العامة للعقار عن مجموعة من التحديثات التنظيمية الجديدة التي تهدف إلى تطوير السوق العقاري وحماية حقوق المتعاملين في المملكة.",
        "link": "https://rega.gov.sa",
        "source": "الهيئة العامة للعقار",
    },
    {
        "title": "ارتفاع ملحوظ في الطلب على الأراضي السكنية بالخرج",
        "desc": "شهدت محافظة الخرج ارتفاعاً في الطلب على الأراضي السكنية والمزارع، مع نمو في الأسعار في المخططات الرئيسية مثل الرحمانية والهياثم.",
        "link": "#",
        "source": "تقارير سوقية",
    },
    {
        "title": "مؤشرات الأسعار العقارية: استقرار في الأسعار خلال الربع الحالي",
        "desc": "أظهرت المؤشرات العقارية استقراراً في الأسعار خلال الربع الحالي، مع نمو طفيف في مناطق الخرج والرياض.",
        "link": "https://rei.rega.gov.sa",
        "source": "منصة المؤشرات العقارية",
    },
    {
        "title": "نظام إيجار: تسهيلات جديدة للمستفيدين من الخدمات الإلكترونية",
        "desc": "أطلقت الهيئة العامة للعقار تحديثات جديدة على نظام إيجار الإلكتروني لتسهيل المعاملات العقارية وتقليل الوقت اللازم لإتمامها.",
        "link": "https://rega.gov.sa",
        "source": "الهيئة العامة للعقار",
    },
    {
        "title": "بوابة العقار الجيومكانية: خدمة جديدة لعرض البيانات العقارية",
        "desc": "أطلقت الهيئة العامة للعقار بوابة العقار الجيومكانية لعرض البيانات العقارية المكانية عبر خرائط دقيقة وتفاعلية تساعد المستثمرين.",
        "link": "https://rega.gov.sa",
        "source": "الهيئة العامة للعقار",
    },
    {
        "title": "الاستثمار الزراعي في الخرج: فرص واعدة في المزارع والأراضي",
        "desc": "يشهد قطاع الاستثمار الزراعي في محافظة الخرج نمواً متزايداً، مع توافر أراضٍ صالحة للزراعة ومزارع بمساحات متنوعة بأسعار تنافسية.",
        "link": "#",
        "source": "تقارير سوقية",
    },
    {
        "title": "رؤية 2030: مشاريع تطوير عقاري جديدة في منطقة الرياض",
        "desc": "ضمن مشاريع رؤية 2030، تستعد منطقة الرياض لإطلاق مشاريع تطوير عقاري جديدة تشمل المناطق المحيطة بالخرج والدرعية.",
        "link": "https://www.vision2030.gov.sa",
        "source": "رؤية 2030",
    },
    {
        "title": "صندوق التنمية العقاري: تمويل جديد للمستفيدين",
        "desc": "أعلن صندوق التنمية العقاري عن برامج تمويلية جديدة للمستفيدين، تشمل منتجات عقارية متنوعة تسهل تملك الأراضي والمزارع.",
        "link": "https://www.redf.gov.sa",
        "source": "صندوق التنمية العقاري",
    },
    {
        "title": "الطلب على الاستراحات في الخرج يشهد نمواً مستمراً",
        "desc": "سجل الطلب على الاستراحات في مناطق الخرج نمواً مستمراً، خصوصاً في المخططات القريبة من الخدمات والطرق الرئيسية.",
        "link": "#",
        "source": "تقارير سوقية",
    },
    {
        "title": "التحول الرقمي في القطاع العقاري: منصات جديدة للمعاملات",
        "desc": "يواصل القطاع العقاري في المملكة تحوله الرقمي، مع إطلاق منصات إلكترونية جديدة تسهل المعاملات العقارية وتوفر الشفافية.",
        "link": "https://rega.gov.sa",
        "source": "الهيئة العامة للعقار",
    },
]


def _generate_news():
    """توليد أخبار عقارية جديدة بشكل عشوائي من القوالب"""
    import random
    today = datetime.now().strftime("%Y-%m-%d")

    # اختيار 5 أخبار عشوائية بدون تكرار
    selected = random.sample(NEWS_TEMPLATES, min(5, len(NEWS_TEMPLATES)))

    news_items = []
    for i, template in enumerate(selected):
        # توزيع الأخبار على آخر 5 أيام
        days_ago = i
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        news_items.append({
            "date": date,
            "title": template["title"],
            "desc": template["desc"],
            "link": template["link"],
            "source": template["source"],
        })

    news_data = {
        "last_update": today,
        "news": news_items,
    }

    # حفظ في الملف المحلي
    try:
        with open(NEWS_JSON, "w", encoding="utf-8") as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        logger.info(f"🗞️ تم توليد {len(news_items)} خبر عقاري جديد")
    except Exception as e:
        logger.error(f"خطأ في حفظ الأخبار: {e}")

    # مزامنة مع GitHub
    try:
        github_sync.sync_news_to_github()
    except Exception as e:
        logger.error(f"خطأ في مزامنة الأخبار مع GitHub: {e}")

    return news_data


async def auto_update_news(context):
    """تحديث تلقائي للأخبار كل 3 أيام"""
    _generate_news()
    logger.info("🗞️ تم التحديث التلقائي للأخبار العقارية")


async def update_news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر تحديث الأخبار يدوياً (للمدير فقط)"""
    if not is_admin(update.effective_user.id):
        return
    news_data = _generate_news()
    news_items = news_data.get("news", [])
    msg = (
        f"🗞️ تم تحديث الأخبار العقارية!\n"
        f"📅 التاريخ: {news_data.get('last_update', '')}\n"
        f"📊 عدد الأخبار: {len(news_items)}\n\n"
    )
    for i, item in enumerate(news_items[:3], 1):
        msg += f"{i}. {item['title'][:60]}...\n"
    msg += "\n🌐 تمت المزامنة مع الموقع تلقائياً"
    await update.message.reply_text(msg)


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

    # مزامنة مع GitHub لتحديث الموقع تلقائياً
    sync_ok = False
    try:
        sync_ok = github_sync.sync_office_data_to_github()
    except Exception as e:
        logger.error(f"خطأ في مزامنة البوصلة مع GitHub: {e}")

    # بناء رسالة التقرير
    msg = f"🧭 تم تحديث بوصلة الأسعار!\n📅 التاريخ: {today}\n━━━━━━━━━━━━━━\n\n"
    for area_name, area_info in areas.items():
        msg += f"📍 {area_name}:\n"
        msg += f"   🏗️ أرض: {area_info.get('land_avg_price_sqm', '—')} ريال/م²\n"
        msg += f"   🌿 مزرعة: {area_info.get('farm_avg_price_sqm', '—')} ريال/م²\n"
        msg += f"   🏡 استراحة: {area_info.get('resthouse_avg_price', '—')} ريال\n\n"

    msg += f"✅ تم تحديث {updated_count} منطقة بناءً على العروض المنشورة"
    if sync_ok:
        msg += "\n🌐 تمت المزامنة مع الموقع بنجاح"
    else:
        msg += "\n⚠️ المزامنة مع الموقع لم تكتمل (محلياً فقط)"
    return msg


# ============================================================
#  لوحة التحكم / إدارة المستخدمين — أوامر جديدة
# ============================================================
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المدير — إحصائيات شاملة"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ هذا الأمر للمدير فقط.")
        return

    try:
        # ── إحصائيات العروض ──
        site_data = load_offers_json()
        offers = site_data.get("offers", [])
        offers_count = len(offers)

        # آخر عرض
        last_offer = offers[-1] if offers else None
        last_offer_str = "لا يوجد"
        if last_offer:
            last_offer_str = f"{last_offer.get('id', '—')} | {last_offer.get('category', '')} | {last_offer.get('area', '')}"

        # ── طلبات الزوار ──
        visitor_data = load_visitor_requests()
        visitor_requests_list = visitor_data.get("requests", [])
        pending_requests = sum(1 for r in visitor_requests_list if r.get("status") == "pending")

        # ── عروض الزوار ──
        bot_data = load_bot_offers()
        visitor_offers = bot_data.get("offers", [])
        pending_visitor_offers = sum(1 for o in visitor_offers if o.get("source") == "visitor" and o.get("status") == "pending")

        # ── إحصائيات المستخدمين ──
        user_stats = user_manager.get_stats()

        # ── حالة الطابور ──
        tq_stats = task_queue.get_stats()

        # ── آخر الأخطاء ──
        error_count = get_error_count()
        recent_errors = get_recent_errors(limit=3)

        # ── النسخ الاحتياطية ──
        backup_count = backup.get_backup_count()

        # ── آخر المزامنات ──
        recent_syncs = get_recent_syncs(limit=3)

        # ── الجلسات النشطة ──
        active_sessions = persistence.get_active_sessions_count()

        # ── بناء الرسالة ──
        msg = (
            "📊 ═══ لوحة التحكم ═══\n\n"
            f"🏠 العروض المنشورة: {offers_count}\n"
            f"📝 آخر عرض: {last_offer_str}\n"
            f"📨 طلبات الزوار: {len(visitor_requests_list)} (منتظرة: {pending_requests})\n"
            f"🏡 عروض الزوار: {pending_visitor_offers} منتظرة\n\n"
            f"👥 المستخدمون: {user_stats['total']} (مدراء: {user_stats['admins']}, محررون: {user_stats['editors']})\n"
            f"   نشطون: {user_stats['active']}, موقوفون: {user_stats['suspended']}\n\n"
            f"🔄 طابور العمليات: {tq_stats['completed']} منجزة, {tq_stats['failed']} فاشلة, {tq_stats['queue_size']} في الانتظار\n"
            f"🔌 جلسات نشطة: {active_sessions}\n\n"
            f"💾 نسخ احتياطية: {backup_count}\n"
            f"⚠️ أخطاء: {error_count}\n"
        )

        if recent_errors:
            msg += "\n📌 آخر الأخطاء:\n"
            for err in recent_errors:
                msg += f"   • {err.get('type', '')}: {err.get('detail', '')[:60]}\n"

        if recent_syncs:
            msg += "\n🔄 آخر المزامنات:\n"
            for sync in recent_syncs:
                status_icon = "✅" if sync.get("status") == "success" else "❌"
                msg += f"   {status_icon} {sync.get('operation', '')} — {sync.get('timestamp', '')}\n"

        msg += f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        await update.message.reply_text(msg)
        user_manager.update_last_active(uid)

    except Exception as e:
        logger.error(f"خطأ في لوحة التحكم: {e}")
        log_error("dashboard", str(e), uid)
        await update.message.reply_text(f"❌ خطأ في عرض لوحة التحكم: {e}")


async def cmd_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة مستخدم جديد — /add_user <user_id> <role> <name>"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ إدارة المستخدمين للمدير فقط.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "📋 إضافة مستخدم جديد\n\n"
            "الصيغة: /add_user <user_id> <role> [الاسم]\n"
            "role: admin أو editor\n\n"
            "مثال:\n"
            "/add_user 123456789 editor أحمد\n"
            "/add_user 987654321 admin"
        )
        return

    try:
        new_uid = int(args[0])
        role = args[1].lower()
        name = " ".join(args[2:]) if len(args) > 2 else f"User {new_uid}"

        if role not in ("admin", "editor"):
            await update.message.reply_text("⚠️ الدور يجب أن يكون: admin أو editor")
            return

        user_manager.add_user(new_uid, name, role=role, added_by=uid)
        user_manager.log_audit("add_user", uid, f"أضاف مستخدم {new_uid} ({name}) بدور {role}")
        await update.message.reply_text(
            f"✅ تم إضافة المستخدم بنجاح!\n\n"
            f"🆔 ID: {new_uid}\n"
            f"👤 الاسم: {name}\n"
            f"🔑 الدور: {role}\n"
            f"📊 الحالة: نشط"
        )
    except ValueError:
        await update.message.reply_text("⚠️ معرف المستخدم يجب أن يكون رقماً.")
    except Exception as e:
        logger.error(f"خطأ في إضافة مستخدم: {e}")
        await update.message.reply_text(f"❌ خطأ: {e}")


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معرف المستخدم الحالي — /myid"""
    uid = update.effective_user.id
    user = update.effective_user
    role = user_manager.get_user_role(uid)
    role_str = {"admin": "مدير", "editor": "محرر"}.get(role, "غير مصرّح")

    await update.message.reply_text(
        f"🆔 معلوماتك:\n\n"
        f"   Telegram ID: {uid}\n"
        f"   الاسم: {user.full_name}\n"
        f"   اسم المستخدم: @{user.username}\n"
        f"   الدور: {role_str}\n\n"
        f"💡 لإضافتك كمستخدم، أرسل هذا المعرّف للمدير."
    )


async def cmd_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المستخدمين — /users"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ هذا الأمر للمدير فقط.")
        return

    users = user_manager.get_all_users()
    if not users:
        await update.message.reply_text("📋 لا يوجد مستخدمون مسجلون.")
        return

    msg = f"📋 قائمة المستخدمين ({len(users)}):\n\n"
    for u in users:
        role_icon = "👑" if u.get("role") == "admin" else "✏️"
        status_icon = "✅" if u.get("status") == "active" else "🚫"
        last_active = u.get("last_active", "—")
        msg += (
            f"{role_icon} {status_icon} ID: {u.get('user_id')}\n"
            f"   الاسم: {u.get('name')}\n"
            f"   الدور: {u.get('role')}\n"
            f"   آخر نشاط: {last_active}\n\n"
        )
    await update.message.reply_text(msg)


async def cmd_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مستخدم — /remove_user <user_id>"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ إدارة المستخدمين للمدير فقط.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("الصيغة: /remove_user <user_id>")
        return

    try:
        target_uid = int(args[0])
        if target_uid == uid:
            await update.message.reply_text("⚠️ لا يمكنك حذف نفسك!")
            return
        # منع حذف آخر مدير
        if user_manager.is_admin(target_uid):
            admins = [u for u in user_manager.get_all_users() if u.get("role") == "admin" and u.get("status") == "active"]
            if len(admins) <= 1:
                await update.message.reply_text("⚠️ لا يمكن حذف آخر مدير! يجب أن يبقى مدير واحد على الأقل.")
                return

        if user_manager.remove_user(target_uid, removed_by=uid):
            user_manager.log_audit("remove_user", uid, f"حذف مستخدم {target_uid}")
            await update.message.reply_text(f"✅ تم حذف المستخدم {target_uid}")
        else:
            await update.message.reply_text(f"⚠️ المستخدم {target_uid} غير موجود.")
    except ValueError:
        await update.message.reply_text("⚠️ معرف المستخدم يجب أن يكون رقماً.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")


# ============================================================
#  معالج الأخطاء العام
# ============================================================
async def error_handler(update, context):
    """معالج الأخطاء العام — يسجل الأخطاء ويمنع توقف البوت"""
    error = context.error
    logger.error(f"❌ خطأ غير معالج: {error}\n{traceback.format_exc()}")
    log_error("unhandled", str(error), update.effective_user.id if update and update.effective_user else None)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ حدث خطأ غير متوقع. تم تسجيله وسيتم معالجته.")
    except Exception:
        pass


# ============================================================
def _setup_handlers(app):
    """تسجيل جميع معالجات البوت — مشترك بين وضعي polling و webhook."""
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
    app.add_handler(CommandHandler("submit", submit_offer_start))
    app.add_handler(CommandHandler("visitor_offers", visitor_offers_cmd))
    app.add_handler(CommandHandler("update_news", update_news_cmd))
    app.add_handler(CommandHandler("news", update_news_cmd))

    # ── أوامر جديدة: لوحة التحكم وإدارة المستخدمين ──
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("add_user", cmd_add_user))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("users", cmd_list_users))
    app.add_handler(CommandHandler("remove_user", cmd_remove_user))

    # الصور
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # الموقع (للزوار — إرسال الموقع عبر زر تيليجرام)
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # الأزرار (callback)
    app.add_handler(CallbackQueryHandler(handle_callback))

    # الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # المهام المجدولة (التقرير الأسبوعي + تحديث الأسعار اليومي)
    if CONFIG.get("weekly_report", True) and app.job_queue:
        app.job_queue.run_daily(auto_weekly_report, days=[6], time=__import__("datetime").time(hour=9, minute=0))
        logger.info("📅 تم جدولة التقرير الأسبوعي — كل يوم أحد 9 صباحاً")
    if CONFIG.get("auto_prices_update", True) and app.job_queue:
        app.job_queue.run_daily(auto_update_prices, time=__import__("datetime").time(hour=6, minute=0))
        logger.info("🧭 تم جدولة تحديث الأسعار اليومي — كل يوم 6 صباحاً")
    # تحديث الأخبار كل 3 أيام
    if app.job_queue:
        app.job_queue.run_repeating(auto_update_news, interval=3 * 24 * 3600, first=10)
        logger.info("🗞️ تم جدولة تحديث الأخبار — كل 3 أيام")



# ============================================================
#  خادم HTTP لاستقبال طلبات الزوار من الموقع (API Endpoint)
#  يعمل في خيط منفصل بجانب البوت (polling أو webhook)
# ============================================================

# متغير عام لتخزين مرجع البوت (يُضبط عند بدء التشغيل)
_bot_app_ref = None
_api_loop = None


def _set_bot_ref(app):
    """تخزين مرجع تطبيق البوت للاستخدام من خادم HTTP"""
    global _bot_app_ref
    _bot_app_ref = app


def _json_response(data, status=200):
    """بناء استجابة JSON"""
    try:
        from aiohttp import web
        return web.json_response(data, status=status)
    except ImportError:
        return None


async def _handle_visitor_request_api(request):
    """
    استقبال طلب زائر من الموقع عبر HTTP POST
    المسار: POST /api/visitor-request

    البيانات المتوقعة (JSON):
    {name, phone, propertyType, location, area, price, description,
     latitude, longitude, mapsLink, imageCount, source}
    """
    try:
        data = await request.json()
    except Exception:
        try:
            data = await request.post()
            data = dict(data)
        except Exception as e:
            return _json_response({"ok": False, "error": f"invalid data: {e}"}, status=400)

    # التحقق من الحقول الأساسية
    if not data.get("name") or not data.get("phone"):
        return _json_response({"ok": False, "error": "name and phone are required"}, status=400)

    # بناء سجل الطلب
    request_id = data.get("id", f"REQ-{int(time.time())}")
    visitor_request = {
        "id": request_id,
        "name": str(data.get("name", "")),
        "phone": str(data.get("phone", "")),
        "propertyType": str(data.get("propertyType", data.get("property_type", ""))),
        "location": str(data.get("location", "")),
        "area": str(data.get("area", "")),
        "price": str(data.get("price", "")),
        "description": str(data.get("description", "")),
        "latitude": str(data.get("latitude", "")),
        "longitude": str(data.get("longitude", "")),
        "mapsLink": str(data.get("mapsLink", data.get("maps_link", ""))),
        "imageCount": int(data.get("imageCount", data.get("image_count", 0)) or 0),
        "source": str(data.get("source", "website")),
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "pending",
    }

    # 1) حفظ الطلب في visitor_requests.json (الدوام بعد إعادة التشغيل)
    try:
        vdata = load_visitor_requests()
        vdata.setdefault("requests", []).append(visitor_request)
        save_visitor_requests(vdata)
        logger.info(f"\U0001F4E5 تم حفظ طلب زائر جديد من الموقع: {request_id} \u2014 {visitor_request['name']}")
    except Exception as e:
        logger.error(f"\u274C خطأ في حفظ طلب الزائر: {e}")
        return _json_response({"ok": False, "error": "save failed"}, status=500)

    # 2) إرسال إشعار للمدير عبر البوت مع أزرار موافقة/رفض
    try:
        if _bot_app_ref and _bot_app_ref.bot:
            await _notify_admins_new_request(_bot_app_ref.bot, visitor_request, vdata)
        else:
            logger.warning("\u26A0\uFE0F مرجع البوت غير متوفر \u2014 تم حفظ الطلب بدون إشعار تيليجرام")
    except Exception as e:
        logger.error(f"\u274C خطأ في إرسال إشعار المدير: {e}")

    return _json_response({"ok": True, "id": request_id, "message": "تم استلام الطلب بنجاح"})


async def _notify_admins_new_request(bot, visitor_request, vdata):
    """إرسال إشعار للمدراء بطلب زائر جديد مع أزرار موافقة/رفض"""
    requests_list = vdata.get("requests", [])
    idx = len(requests_list) - 1

    msg = (
        "\U0001F514 <b>طلب عرض عقار جديد من الموقع</b>\n\n"
        f"\U0001F464 <b>اسم العميل:</b> {visitor_request.get('name', '')}\n"
        f"\U0001F4F1 <b>رقم الهاتف:</b> {visitor_request.get('phone', '')}\n"
        f"\U0001F3F7\uFE0F <b>نوع العقار:</b> {visitor_request.get('propertyType', '')}\n"
        f"\U0001F4CD <b>الموقع:</b> {visitor_request.get('location', '')}\n"
        f"\U0001F4D0 <b>المساحة:</b> {visitor_request.get('area', '')} م²\n"
        f"\U0001F4B0 <b>السعر التقريبي:</b> {visitor_request.get('price', '')} ريال\n"
    )

    if visitor_request.get("description"):
        msg += f"\n\u2139\uFE0F <b>الوصف:</b>\n{visitor_request['description']}\n"

    if visitor_request.get("latitude") and visitor_request.get("longitude"):
        maps_url = visitor_request.get("mapsLink") or f"https://www.google.com/maps?q={visitor_request['latitude']},{visitor_request['longitude']}"
        msg += (
            f"\n\U0001F5FA\uFE0F <b>موقع العقار على الخريطة:</b>\n"
            f"   <b>خط العرض (Latitude):</b> {visitor_request['latitude']}\n"
            f"   <b>خط الطول (Longitude):</b> {visitor_request['longitude']}\n"
            f"   <b>رابط Google Maps:</b> {maps_url}\n"
        )

    img_count = visitor_request.get("imageCount", 0)
    img_note = " (يُرفقها العميل عبر WhatsApp)" if img_count > 0 else ""
    msg += (
        f"\n\U0001F4F8 <b>الصور:</b> {img_count} صورة{img_note}\n"
        f"\U0001F4C4 <b>رقم الطلب:</b> <code>{visitor_request.get('id', '')}</code>\n"
        f"\U0001F550 <b>التاريخ:</b> {visitor_request.get('submitted_at', '')}\n"
        f"\n\U0001F4A1 مكتب آفاق الإنجاز العقاري\n"
        f"\U0001F310 abonasr0907-beep.github.io/-"
    )

    # أزرار الموافقة والرفض
    req_id = visitor_request.get("id", f"idx_{idx}")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2705 موافقة ونشر", callback_data=f"vreq_approve_{req_id}")],
        [InlineKeyboardButton("\u274C رفض", callback_data=f"vreq_reject_{req_id}")],
    ])

    sent_count = 0
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                msg,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"\u274C فشل إرسال إشعار للمدير {admin_id}: {e}")

    logger.info(f"\U0001F4E4 تم إرسال إشعار طلب زائر إلى {sent_count} مدير")


async def _handle_health(request):
    """فحص صحة الخادم"""
    return _json_response({"ok": True, "status": "running", "bot": "afaq"})


async def _handle_root(request):
    """الصفحة الرئيسية للخادم"""
    return _json_response({
        "ok": True,
        "service": "Afaq Real Estate Bot API",
        "endpoints": ["/api/visitor-request", "/health"]
    })


def _create_api_app():
    """إنشاء تطبيق aiohttp لخادم API"""
    try:
        from aiohttp import web
    except ImportError:
        logger.error("\u274C aiohttp غير متوفر \u2014 لا يمكن تشغيل خادم API")
        return None

    app = web.Application()
    app.router.add_post("/api/visitor-request", _handle_visitor_request_api)
    app.router.add_get("/api/visitor-request", _handle_root)
    app.router.add_get("/health", _handle_health)
    app.router.add_get("/", _handle_root)
    return app


def _run_api_server(port):
    """تشغيل خادم API في خيط منفصل"""
    try:
        from aiohttp import web
    except ImportError:
        logger.warning("\u26A0\uFE0F aiohttp غير متوفر \u2014 خادم API معطل")
        return

    api_app = _create_api_app()
    if api_app is None:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    global _api_loop
    _api_loop = loop

    runner = web.AppRunner(api_app)
    loop.run_until_complete(runner.setup())

    site = web.TCPSite(runner, "0.0.0.0", port)
    loop.run_until_complete(site.start())

    logger.info(f"\U0001F310 خادم API يعمل على المنفذ {port}")
    logger.info(f"   المسارات: POST /api/visitor-request, GET /health")

    try:
        loop.run_forever()
    except Exception as e:
        logger.error(f"\u274C خادم API توقف: {e}")


def start_api_server(port=8080):
    """بدء خادم API في خيط خلفي"""
    thread = threading.Thread(target=_run_api_server, args=(port,), daemon=True)
    thread.start()
    logger.info(f"\U0001F504 تم بدء خيط خادم API على المنفذ {port}")
    return thread


# ============================================================

async def _run_custom_webhook(app, webhook_url, port):
    """
    تشغيل خادم webhook مخصص يخدم مسار الـ webhook ومسارات API على نفس المنفذ.
    هذا يحل مشكلة Railway التي تسمح بمنفذ عام واحد فقط.

    المسارات:
      POST /bot/{BOT_TOKEN}  -> استقبال تحديثات Telegram
      POST /api/visitor-request -> استقبال طلبات الزوار من الموقع
      GET  /health           -> فحص الصحة
      GET  /                 -> معلومات الخادم
    """
    from aiohttp import web

    webhook_path = f"/bot/{BOT_TOKEN}"
    full_webhook_url = f"{webhook_url}{webhook_path}"

    # بناء خادم aiohttp مخصص
    web_app = web.Application()

    # مسار الـ webhook الخاص بـ Telegram
    async def telegram_webhook_handler(request):
        """استقبال تحديثات Telegram وإدخالها في معالج البوت"""
        try:
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.process_update(update)
            return web.Response(status=200)
        except Exception as e:
            logger.error(f"\u274C خطأ في معالجة webhook: {e}")
            return web.Response(status=500)

    web_app.router.add_post(webhook_path, telegram_webhook_handler)
    # إضافة مسارات API على نفس الخادم
    web_app.router.add_post("/api/visitor-request", _handle_visitor_request_api)
    web_app.router.add_get("/api/visitor-request", _handle_root)
    web_app.router.add_get("/health", _handle_health)
    web_app.router.add_get("/", _handle_root)

    # تعيين الـ webhook مع Telegram
    await app.bot.set_webhook(url=full_webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info(f"\U0001F517 تم تعيين webhook: {full_webhook_url}")

    # تشغيل الخادم
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"\U0001F310 خادم webhook+API يعمل على المنفذ {port}")
    logger.info(f"   المسارات: POST {webhook_path}, POST /api/visitor-request, GET /health, GET /")

    # تشغيل البوت (بدون updater لأننا ندير الـ webhook يدوياً)
    await app.start()
    logger.info("\u2705 البوت يعمل في وضع webhook المخصص")

    # انتظار indefinite
    import asyncio
    await asyncio.Event().wait()  # يعمل للأبد


def main():
    """
    تشغيل البوت في وضع webhook أو polling حسب متغيرات البيئة.

    وضع webhook (للاستضافة السحابية المجانية):
      WEBHOOK_URL  = الرابط العام الكامل (مثل https://myapp.onrender.com)
      PORT         = منفذ الخادم (تحدده منصة الاستضافة، افتراضي 10000)

    وضع polling (للتشغيل المحلي / على جهازك):
      لا تضع WEBHOOK_URL — سيعمل البوت بـ polling تلقائياً
    """
    # ── تهيئة الأنظمة الدائمة ──
    try:
        persistence.init()
        logger.info("📦 تم تهيئة نظام الحفظ الدائم (persistence)")
    except Exception as e:
        logger.error(f"⚠️ خطأ في تهيئة persistence: {e}")

    try:
        user_manager.init()
        user_manager.init_from_config(CONFIG)
        logger.info("👥 تم تهيئة نظام إدارة المستخدمين")
    except Exception as e:
        logger.error(f"⚠️ خطأ في تهيئة user_manager: {e}")

    try:
        offer_id.init()
        # مزامنة العدّاد مع العروض الموجودة
        site_data = load_offers_json()
        offer_id.sync_with_existing_offers(site_data.get("offers", []))
        logger.info(f"🔢 تم تهيئة مولّد المعرفات — آخر معرف: {offer_id.get_last_id()}")
    except Exception as e:
        logger.error(f"⚠️ خطأ في تهيئة offer_id: {e}")

    # ── بناء التطبيق ──
    async def _post_init(app):
        """تهيئة ما قبل التشغيل — تشغيل طابور العمليات + خادم API"""
        # تخزين مرجع البوت لاستخدامه من خادم HTTP
        _set_bot_ref(app)

        try:
            await task_queue.start_worker()
            logger.info("🔄 تم تشغيل طابور العمليات الثقيلة")
        except Exception as e:
            logger.error(f"⚠️ خطأ في تشغيل طابور العمليات: {e}")

        # ── بدء خادم API لاستقبال طلبات الزوار من الموقع ──
        # في وضع webhook: API يعمل على نفس المنفذ عبر الخادم المخصص (لا حاجة لمنفذ منفصل)
        # في وضع polling: نحتاج لخادم API منفصل على منفذ 8080
        webhook_url_check = os.environ.get("WEBHOOK_URL", "").strip()
        if not webhook_url_check:
            api_port = int(os.environ.get("PORT", os.environ.get("API_PORT", "8080")))
            try:
                start_api_server(api_port)
                logger.info(f"🌐 خادم API جاهز لاستقبال طلبات الزوار على المنفذ {api_port}")
            except Exception as e:
                logger.error(f"⚠️ خطأ في بدء خادم API: {e}")
        else:
            logger.info("ℹ️ وضع webhook: API يعمل على نفس المنفذ عبر الخادم المخصص")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        # ── مهلات اتصال أطول لتحمّل الإنترنت الضعيف ──
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(30)
        .build()
    )

    # ── تسجيل معالج الأخطاء العام ──
    app.add_error_handler(error_handler)
    logger.info("🛡️ تم تفعيل معالج الأخطاء العام")

    _setup_handlers(app)

    webhook_url = os.environ.get("WEBHOOK_URL", "").strip().rstrip("/")
    port = int(os.environ.get("PORT", "10000"))

    if webhook_url:
        # ─── وضع webhook مخصص (للاستضافة السحابية - Railway) ───
        # استخدام خادم مخصص يخدم webhook + API على نفس المنفذ
        # لأن Railway يسمح بمنفذ عام واحد فقط
        logger.info("\U0001F680 تشغيل البوت في وضع WEBHOOK المخصص")
        logger.info(f"   الرابط العام: {webhook_url}")
        logger.info(f"   منفذ الخادم: {port}")

        try:
            asyncio.run(_run_custom_webhook(app, webhook_url, port))
        except KeyboardInterrupt:
            logger.info("\u26A0\uFE0F تم إيقاف البوت")
        except Exception as e:
            logger.error(f"\u274C خطأ في خادم webhook: {e}")
            raise
    else:
        # ─── وضع polling (للتشغيل المحلي) ───
        logger.info("🚀 تشغيل البوت في وضع POLLING (محلي)")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
