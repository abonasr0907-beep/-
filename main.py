"""
آفاق الإنجاز - نظام إدارة العقارات (نسخة مستقرة)
"""

import os
import sys
import logging
from datetime import datetime
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from bot.config import BOT_TOKEN, WEBHOOK_URL, PORT, VISITORS_FILE, COMPASS_FILE
from bot.database import init_db, load_properties, get_property, load_json, save_json
from bot.modules.add_property import get_add_property_handler
from bot.modules.list_properties import get_list_properties_handler
from bot.modules.edit_property import get_edit_property_handler
from bot.modules.delete_property import get_delete_property_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Afaq Al-Injaz Bot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

telegram_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    logger.info("🚀 Starting bot...")
    init_db()
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(get_add_property_handler())
    telegram_app.add_handler(get_list_properties_handler())
    telegram_app.add_handler(get_edit_property_handler())
    telegram_app.add_handler(get_delete_property_handler())
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_persistent_menu))
    logger.info("✅ Handlers registered")

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        allowed_updates=Update.ALL_TYPES
    )
    logger.info("✅ Webhook set")
    logger.info("✅ Bot started successfully")
    yield
    await telegram_app.stop()
    await telegram_app.shutdown()

app.router.lifespan_context = lifespan

@app.post(f"/{BOT_TOKEN}")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def root():
    return {"status": "running", "system": "Afaq Al-Injaz Bot", "properties": len(load_properties())}

@app.get("/api/properties")
async def get_properties_api():
    return load_properties()

@app.get("/api/properties/{id}")
async def get_single_property_api(id: str):
    prop = get_property(id)
    if not prop:
        return JSONResponse(status_code=404, content={"error": "Property not found", "id": id})
    return prop

@app.get("/api/compass")
async def get_compass_api():
    compass_data = load_json(COMPASS_FILE, default={})
    return compass_data

@app.post("/api/visitors")
async def create_visitor_request_api(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    visitors = load_json(VISITORS_FILE, default=[])
    req_id = f"REQ-{int(datetime.now().timestamp() * 1000)}"
    visitor_entry = {
        "id": req_id,
        "date": datetime.now().isoformat(),
        "status": "pending",
        **body
    }
    visitors.append(visitor_entry)
    save_json(VISITORS_FILE, visitors, root_key="visitors")
    return {"status": "ok", "id": req_id, "message": "Request saved successfully"}

def get_main_reply_keyboard():
    keyboard = [
        ["➕ إضافة عرض جديد", "📋 قائمة العروض"],
        ["✏️ تعديل عرض", "🗑️ حذف عرض"],
        ["📦 الأرشيف", "🧭 البوصلة"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_keyboard = [
        [InlineKeyboardButton("📋 قائمة العروض", callback_data='list_props'),
         InlineKeyboardButton("➕ إضافة عرض جديد", callback_data='add_prop')],
        [InlineKeyboardButton("✏️ تعديل عرض", callback_data='edit_prop'),
         InlineKeyboardButton("🗑️ حذف عرض", callback_data='delete_prop')],
        [InlineKeyboardButton("📨 طلبات الزوار", callback_data='visitors'),
         InlineKeyboardButton("📦 الأرشيف", callback_data='archive')],
        [InlineKeyboardButton("📊 إحصائيات", callback_data='stats'),
         InlineKeyboardButton("🧭 البوصلة", callback_data='compass')],
        [InlineKeyboardButton("👥 المدراء", callback_data='admins'),
         InlineKeyboardButton("🤖 المساعد", callback_data='assistant')],
        [InlineKeyboardButton("🎬 التسويق", callback_data='marketing'),
         InlineKeyboardButton("📈 التقارير", callback_data='reports')],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings'),
         InlineKeyboardButton("🔄 إلغاء", callback_data='cancel')]
    ]
    await update.message.reply_text(
        "🏡 نظام إدارة العقارات - آفاق الإنجاز\n\nمرحباً بك في لوحة تحكم المدراء.",
        reply_markup=get_main_reply_keyboard()
    )
    await update.message.reply_text(
        "اختر من القائمة أدناه أو من الأزرار التالية:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )

async def handle_persistent_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message and update.message.text else ""
    if text == "➕ إضافة عرض جديد":
        from bot.modules.add_property import start_add_property
        return await start_add_property(update, context)
    elif text == "📋 قائمة العروض":
        from bot.modules.list_properties import list_properties_callback
        return await list_properties_callback(update, context)
    elif text == "✏️ تعديل عرض":
        from bot.modules.edit_property import start_edit_property
        return await start_edit_property(update, context)
    elif text == "🗑️ حذف عرض":
        from bot.modules.delete_property import start_delete_property
        return await start_delete_property(update, context)
    elif text == "📦 الأرشيف":
        await update.message.reply_text("📦 الأرشيف - قريباً", reply_markup=get_main_reply_keyboard())
    elif text == "🧭 البوصلة":
        await update.message.reply_text("🧭 البوصلة - قريباً", reply_markup=get_main_reply_keyboard())
    else:
        await update.message.reply_text("🏡 يمكنك استخدام القائمة الدائمة أسفل الشاشة للتحكم.", reply_markup=get_main_reply_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    responses = {
        'visitors': "📨 الزوار - قريباً",
        'archive': "📦 الأرشيف - قريباً",
        'stats': "📊 الإحصائيات - قريباً",
        'compass': "🧭 البوصلة - قريباً",
        'admins': "👥 المدراء - قريباً",
        'assistant': "🤖 المساعد - قريباً",
        'marketing': "🎬 التسويق - قريباً",
        'reports': "📈 التقارير - قريباً",
        'settings': "⚙️ الإعدادات - قريباً",
        'cancel': "🔄 تم الإلغاء. اكتب /start للبدء من جديد."
    }
    await query.edit_message_text(responses.get(data, "⚠️ أمر غير معروف"))

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

if __name__ == '__main__':
    main()
