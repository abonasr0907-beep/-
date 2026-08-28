"""
آفاق الإنجاز - نظام إدارة العقارات
بوت تيليجرام للمدراء فقط - FastAPI + Uvicorn
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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from bot.config import BOT_TOKEN, WEBHOOK_URL, PORT
from bot.database import init_db, load_properties

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Afaq Al-Injaz Real Estate Bot")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

telegram_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    logger.info("🚀 Starting bot initialization...")
    init_db()
    logger.info("✅ Database initialized")
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("✅ Basic handlers registered")
    webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    await telegram_app.initialize()
    await telegram_app.set_webhook(webhook_url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info(f"✅ Webhook set: {webhook_url}")
    logger.info("✅ Bot started successfully")
    yield
    await telegram_app.stop()
    logger.info("🛑 Bot stopped")

app.router.lifespan_context = lifespan

@app.post(f"/{BOT_TOKEN}")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/")
async def root():
    return {"status": "running", "system": "Afaq Al-Injaz Real Estate Bot", "properties_count": len(load_properties()), "timestamp": datetime.now().isoformat()}

@app.get("/api/properties")
async def get_properties_api():
    return load_properties()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 قائمة العروض", callback_data='list_props'), InlineKeyboardButton("➕ إضافة عرض جديد", callback_data='add_prop')],
        [InlineKeyboardButton("✏️ تعديل عرض", callback_data='edit_prop'), InlineKeyboardButton("🗑️ حذف عرض", callback_data='delete_prop')],
        [InlineKeyboardButton("📨 طلبات الزوار", callback_data='visitors'), InlineKeyboardButton("📦 الأرشيف", callback_data='archive')],
        [InlineKeyboardButton("📊 إحصائيات", callback_data='stats'), InlineKeyboardButton("🧭 تحديث البوصلة", callback_data='compass')],
        [InlineKeyboardButton("👥 إدارة المدراء", callback_data='admins'), InlineKeyboardButton("🤖 المساعد الذكي", callback_data='assistant')],
        [InlineKeyboardButton("🎬 استوديو التسويق", callback_data='marketing'), InlineKeyboardButton("📈 التقرير الأسبوعي", callback_data='reports')],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings'), InlineKeyboardButton("🔄 إلغاء / بدء جديد", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏡 نظام إدارة العقارات - آفاق الإنجاز\n\nمرحباً بك في لوحة تحكم المدراء (خاص بالمدراء فقط).\nاختر من القائمة أدناه:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    responses = {
        'list_props': "📋 قائمة العروض - جاري التحميل...",
        'add_prop': "➕ إضافة عرض جديد - بدء التدفق...",
        'edit_prop': "✏️ تعديل عرض - قيد التطوير",
        'delete_prop': "🗑️ حذف عرض - قيد التطوير",
        'visitors': "📨 طلبات الزوار - قيد التطوير",
        'archive': "📦 الأرشيف - قيد التطوير",
        'stats': "📊 إحصائيات - قيد التطوير",
        'compass': "🧭 تحديث البوصلة - قيد التطوير",
        'admins': "👥 إدارة المدراء - قيد التطوير",
        'assistant': "🤖 المساعد الذكي - قيد التطوير",
        'marketing': "🎬 استوديو التسويق - قيد التطوير",
        'reports': "📈 التقرير الأسبوعي - قيد التطوير",
        'settings': "⚙️ الإعدادات - قيد التطوير",
        'cancel': "🔄 تم الإلغاء. اكتب /start للبدء من جديد."
    }
    message = responses.get(data, "⚠️ أمر غير معروف")
    await query.edit_message_text(message)

def main():
    logger.info("🚀 Starting Uvicorn server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

if __name__ == '__main__':
    main()
