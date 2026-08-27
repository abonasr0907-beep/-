#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام — مكتب آفاق الإنجاز العقاري
تيليجرام بوت لإضافة عقار جديد عبر أزرار InlineKeyboard
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# المسارات
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = ROOT_DIR / "data"
PROPERTIES_JSON = DATA_DIR / "properties.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("afaq_telegram_bot")

# الجلسات
user_data_store = {}

def get_user_session(user_id):
    if user_id not in user_data_store:
        user_data_store[user_id] = {
            "step": "IDLE",
            "type": None,
            "location": None,
            "area_size": None,
            "price": None,
            "streets": None,
            "facing": None,
            "features": [],
            "description": "",
            "photos": [],
        }
    return user_data_store[user_id]

def reset_user_session(user_id):
    user_data_store[user_id] = {
        "step": "IDLE",
        "type": None,
        "location": None,
        "area_size": None,
        "price": None,
        "streets": None,
        "facing": None,
        "features": [],
        "description": "",
        "photos": [],
    }

def save_property_to_json(prop):
    data = {"properties": []}
    if PROPERTIES_JSON.exists():
        try:
            with open(PROPERTIES_JSON, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "properties" in content:
                    data = content
                elif isinstance(content, list):
                    data = {"properties": content}
        except Exception as e:
            logger.error(f"Error loading properties.json: {e}")

    prop_entry = {
        "id": f"PROP-{int(datetime.now().timestamp())}",
        "type": prop.get("type"),
        "location": prop.get("location"),
        "size_sqm": prop.get("area_size"),
        "price": prop.get("price"),
        "streets": prop.get("streets"),
        "facing": prop.get("facing"),
        "features": prop.get("features", []),
        "description": prop.get("description", ""),
        "images": prop.get("photos", []),
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data["properties"].append(prop_entry)

    with open(PROPERTIES_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved property {prop_entry['id']} to {PROPERTIES_JSON}")

# لوحات المفاتيح
TYPE_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🌾 مزرعة", callback_data="type_farm"),
        InlineKeyboardButton("🏡 استراحة", callback_data="type_resthouse"),
        InlineKeyboardButton("📐 أرض", callback_data="type_land"),
    ]
])

LOCATION_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("الرحمانية", callback_data="loc_الرحمانية")],
    [InlineKeyboardButton("الهياثم", callback_data="loc_الهياثم")],
    [InlineKeyboardButton("الدلم", callback_data="loc_الدلم")],
    [InlineKeyboardButton("الضبيعة", callback_data="loc_الضبيعة")],
    [InlineKeyboardButton("العفجة", callback_data="loc_العفجة")],
])

STREETS_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("1", callback_data="street_1"),
        InlineKeyboardButton("2", callback_data="street_2"),
        InlineKeyboardButton("3", callback_data="street_3"),
        InlineKeyboardButton("4", callback_data="street_4"),
    ]
])

FACING_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("شمال", callback_data="facing_شمال"),
        InlineKeyboardButton("جنوب", callback_data="facing_جنوب"),
    ],
    [
        InlineKeyboardButton("شرق", callback_data="facing_شرق"),
        InlineKeyboardButton("غرب", callback_data="facing_غرب"),
    ],
    [
        InlineKeyboardButton("شمالي شرقي", callback_data="facing_شمالي شرقي"),
        InlineKeyboardButton("جنوبي شرقي", callback_data="facing_جنوبي شرقي"),
    ],
    [
        InlineKeyboardButton("شمالي غريب", callback_data="facing_شمالي غريب"),
        InlineKeyboardButton("جنوبي غريب", callback_data="facing_جنوبي غريب"),
    ]
])

ALL_FEATURES = ["ماء", "كهرباء", "بئر", "مسجد", "مدرسة", "سوق"]

def build_features_keyboard(selected_features):
    buttons = []
    row = []
    for f in ALL_FEATURES:
        prefix = "✅ " if f in selected_features else "▫️ "
        row.append(InlineKeyboardButton(f"{prefix}{f}", callback_data=f"feat_toggle_{f}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("تم الاختيار ➡️", callback_data="feat_done")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reset_user_session(user_id)
    session = get_user_session(user_id)
    session["step"] = "TYPE"

    text = "أهلاً بك في بوت مكتب آفاق الإنجاز العقاري 🏢\n\nيرجى اختيار نوع العقار المراد إضافته:"
    if update.message:
        await update.message.reply_text(text, reply_markup=TYPE_KEYBOARD)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=TYPE_KEYBOARD)

async def add_property_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = get_user_session(user_id)
    data = query.data

    # اختيار النوع
    if data.startswith("type_"):
        ptype = data.replace("type_", "")
        type_map = {"farm": "مزرعة", "resthouse": "استراحة", "land": "أرض"}
        session["type"] = type_map.get(ptype, ptype)
        session["step"] = "LOCATION"
        await query.edit_message_text(
            f"تم اختيار النوع: {session['type']}\n\nاختر موقع العقار:",
            reply_markup=LOCATION_KEYBOARD
        )
        return

    # اختيار الموقع
    if data.startswith("loc_"):
        loc = data.replace("loc_", "")
        session["location"] = loc
        session["step"] = "AREA"
        await query.edit_message_text(
            f"تم اختيار الموقع: {loc}\n\nالرجاء إدخال المساحة بالمتر المربع (أرسل رقم فقط):"
        )
        return

    # اختيار عدد الشوارع
    if data.startswith("street_"):
        st_count = int(data.replace("street_", ""))
        session["streets"] = st_count
        session["step"] = "FACING"
        await query.edit_message_text(
            f"عدد الشوارع: {st_count}\n\nاختر الواجهة:",
            reply_markup=FACING_KEYBOARD
        )
        return

    # اختيار الواجهة
    if data.startswith("facing_"):
        facing = data.replace("facing_", "")
        session["facing"] = facing
        session["step"] = "FEATURES"
        await query.edit_message_text(
            f"الواجهة: {facing}\n\nاختر المميزات الخاصة بالعقار (يمكنك اختيار أكثر من ميزة):",
            reply_markup=build_features_keyboard(session["features"])
        )
        return

    # تبديل المميزات
    if data.startswith("feat_toggle_"):
        feat = data.replace("feat_toggle_", "")
        if feat in session["features"]:
            session["features"].remove(feat)
        else:
            session["features"].append(feat)
        await query.edit_message_reply_markup(
            reply_markup=build_features_keyboard(session["features"])
        )
        return

    # إتمام خيارات المميزات
    if data == "feat_done":
        session["step"] = "DESC"
        feats_text = ", ".join(session["features"]) if session["features"] else "لا يوجد"
        skip_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("تخطي الوصف ➡️", callback_data="skip_desc")]
        ])
        await query.edit_message_text(
            f"المميزات المختارة: {feats_text}\n\nأدخل وصفاً للعقار (أو اضغط تخطي):",
            reply_markup=skip_keyboard
        )
        return

    # تخطي الوصف
    if data == "skip_desc":
        session["description"] = ""
        session["step"] = "PHOTOS"
        done_photos_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("تم إرسال الصور ✅", callback_data="photos_done")]
        ])
        await query.edit_message_text(
            "أرسل صور العقار (يمكنك إرسال أكثر من صورة).\nعند الانتهاء اضغط «تم إرسال الصور ✅»:",
            reply_markup=done_photos_keyboard
        )
        return

    # إنهاء إرسال الصور وحفظ العقار
    if data == "photos_done":
        save_property_to_json(session)
        photos_count = len(session["photos"])
        summary = (
            f"✅ تم حفظ العقار بنجاح في data/properties.json!\n\n"
            f"🏡 النوع: {session['type']}\n"
            f"📍 الموقع: {session['location']}\n"
            f"📐 المساحة: {session['area_size']} م²\n"
            f"💰 السعر: {session['price']} ريال\n"
            f"🛣️ عدد الشوارع: {session['streets']}\n"
            f"🧭 الواجهة: {session['facing']}\n"
            f"✨ المميزات: {', '.join(session['features']) if session['features'] else 'لا يوجد'}\n"
            f"📝 الوصف: {session['description'] or 'بدون'}\n"
            f"📸 الصور: {photos_count} صورة"
        )
        await query.edit_message_text(summary)
        reset_user_session(user_id)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    step = session["step"]
    text = update.message.text.strip() if update.message and update.message.text else ""

    if step == "AREA":
        try:
            val = float(text.replace(",", ""))
            session["area_size"] = val
            session["step"] = "PRICE"
            await update.message.reply_text("تم تسجيل المساحة.\n\nالآن أدخل السعر بالريال (أرسل رقم فقط):")
        except ValueError:
            await update.message.reply_text("يرجى إدخال رقم صحيح للمساحة:")
        return

    if step == "PRICE":
        try:
            val = float(text.replace(",", ""))
            session["price"] = val
            session["step"] = "STREETS"
            await update.message.reply_text("تم تسجيل السعر.\n\nاختر عدد الشوارع:", reply_markup=STREETS_KEYBOARD)
        except ValueError:
            await update.message.reply_text("يرجى إدخال رقم صحيح للسعر:")
        return

    if step == "DESC":
        session["description"] = text
        session["step"] = "PHOTOS"
        done_photos_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("تم إرسال الصور ✅", callback_data="photos_done")]
        ])
        await update.message.reply_text(
            "تم تسجيل الوصف.\n\nالآن أرسل صور العقار (يمكنك إرسال أكثر من صورة).\nعند الانتهاء اضغط زر «تم إرسال الصور ✅» بالأسفل:",
            reply_markup=done_photos_keyboard
        )
        return

    await update.message.reply_text("استخدم الأمر /add أو /start لبدء إضافة عقار جديد.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_user_session(user_id)

    if session["step"] == "PHOTOS":
        photo = update.message.photo[-1]
        file_id = photo.file_id
        session["photos"].append(file_id)
        done_photos_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("تم إرسال الصور ✅", callback_data="photos_done")]
        ])
        await update.message.reply_text(
            f"تم استلام الصورة ({len(session['photos'])}). أرسل المزيد أو اضغط «تم إرسال الصور ✅»:",
            reply_markup=done_photos_keyboard
        )

def main():
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is not set in environment.")

    app = Application.builder().token(BOT_TOKEN or "DUMMY_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_property_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
