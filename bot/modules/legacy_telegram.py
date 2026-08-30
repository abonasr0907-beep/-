# bot/modules/legacy_telegram.py
"""
الوظائف الموروثة من البوت القديم (telegram-bot/bot.py)
تم دمجها في النظام الرئيسي.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
from pathlib import Path
from datetime import datetime

from bot.database import load_properties, save_properties
from bot.config import PROPERTIES_FILE

# الجلسات (تم الاحتفاظ بها للتوافق)
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

# لوحات المفاتيح الموروثة (للتوافق)
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
