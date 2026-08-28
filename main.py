import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Optional

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from bot.config import BOT_TOKEN, WEBHOOK_URL, PORT
from bot.database import init_db, load_properties

from bot.modules.add_property import get_add_property_handler
from bot.modules.list_properties import get_list_properties_handler, handle_list_navigation
from bot.modules.edit_property import get_edit_property_handler
from bot.modules.delete_property import get_delete_property_handler
from bot.modules.visitors import get_visitors_handler, update_visitor_status
from bot.modules.archive import get_archive_handler, handle_archive_action
from bot.modules.stats import get_stats_handler
from bot.modules.compass import get_compass_handler, refresh_compass_callback
from bot.modules.tour import get_tour_handler
from bot.modules.admins import get_admins_handler
from bot.modules.assistant import get_assistant_handler
from bot.modules.marketing import get_marketing_handler
from bot.modules.notifications import get_notifications_handler
from bot.modules.follow_up import get_follow_up_handler
from bot.modules.pricing import get_pricing_handler
from bot.modules.reports import get_reports_handler
from bot.modules.security import get_security_handler
from bot.modules.backup import get_backup_handler
from bot.modules.site_sync import get_site_sync_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

telegram_app: Optional[Application] = None

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ حدث خطأ غير متوقع أثناء معالجة الطلب.")
        except Exception:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية"""
    keyboard = [
        [
            InlineKeyboardButton("📋 قائمة العروض", callback_data='list_props'),
            InlineKeyboardButton("➕ إضافة عرض جديد", callback_data='add_prop')
        ],
        [
            InlineKeyboardButton("✏️ تعديل عرض", callback_data='edit_prop'),
            InlineKeyboardButton("🗑️ حذف عرض", callback_data='delete_prop')
        ],
        [
            InlineKeyboardButton("📨 طلبات الزوار", callback_data='visitors'),
            InlineKeyboardButton("📦 الأرشيف", callback_data='archive')
        ],
        [
            InlineKeyboardButton("📊 إحصائيات", callback_data='stats'),
            InlineKeyboardButton("🧭 تحديث البوصلة", callback_data='compass')
        ],
        [
            InlineKeyboardButton("👥 إدارة المدراء", callback_data='admins'),
            InlineKeyboardButton("🤖 المساعد الذكي", callback_data='assistant')
        ],
        [
            InlineKeyboardButton("🎬 استوديو التسويق", callback_data='marketing'),
            InlineKeyboardButton("📈 التقرير الأسبوعي", callback_data='reports')
        ],
        [
            InlineKeyboardButton("⚙️ الإعدادات", callback_data='security'),
            InlineKeyboardButton("🔄 إلغاء / بدء جديد", callback_data='cancel')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "🏡 *نظام إدارة العقارات - آفاق الإنجاز*\n\n"
        "مرحباً بك في لوحة تحكم المدراء.\n"
        "اختر من القائمة أدناه:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in ['cancel', 'back_to_main']:
        await start(update, context)

def build_telegram_app() -> Application:
    init_db()
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is not set.")
        app = Application.builder().token("000000000:AAFFFFFF_DummyTokenForInit_ABCDEFG").build()
    else:
        app = Application.builder().token(BOT_TOKEN).build()

    app.add_error_handler(global_error_handler)

    # Register command and feature handlers
    app.add_handler(CommandHandler("start", start))

    # Modules handlers
    app.add_handler(get_add_property_handler())
    app.add_handler(get_edit_property_handler())
    app.add_handler(get_delete_property_handler())
    app.add_handler(get_list_properties_handler())
    app.add_handler(get_visitors_handler())
    app.add_handler(get_archive_handler())
    app.add_handler(get_stats_handler())
    app.add_handler(get_compass_handler())
    app.add_handler(get_tour_handler())
    app.add_handler(get_admins_handler())
    app.add_handler(get_assistant_handler())
    app.add_handler(get_marketing_handler())
    app.add_handler(get_notifications_handler())
    app.add_handler(get_follow_up_handler())
    app.add_handler(get_pricing_handler())
    app.add_handler(get_reports_handler())
    app.add_handler(get_security_handler())
    app.add_handler(get_backup_handler())
    app.add_handler(get_site_sync_handler())

    # Dynamic callbacks
    app.add_handler(CallbackQueryHandler(handle_list_navigation, pattern="^(listpage_|filter_|archprop_)"))
    app.add_handler(CallbackQueryHandler(update_visitor_status, pattern="^vis_"))
    app.add_handler(CallbackQueryHandler(handle_archive_action, pattern="^(restore_arch_|perm_del_)"))
    app.add_handler(CallbackQueryHandler(refresh_compass_callback, pattern="^refresh_compass$"))

    # Global callback fallback
    app.add_handler(CallbackQueryHandler(button_handler))

    return app

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    init_db()

    if BOT_TOKEN:
        telegram_app = build_telegram_app()
        await telegram_app.initialize()
        await telegram_app.start()

        if WEBHOOK_URL:
            webhook_path = f"/bot/{BOT_TOKEN}"
            full_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
            await telegram_app.bot.set_webhook(
                url=full_url,
                allowed_updates=["message", "callback_query", "inline_query"]
            )
            logger.info(f"✅ Webhook configured: {full_url}")

    yield

    if telegram_app:
        await telegram_app.stop()
        await telegram_app.shutdown()

app = FastAPI(title="Afaq Al-Injaz Real Estate Management System", lifespan=lifespan)

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
        "system": "Afaq Al-Injaz Modular Real Estate Bot",
        "properties_count": len(load_properties())
    }

@app.get("/api/properties")
async def get_properties():
    return load_properties()

def main():
    """تشغيل الخدمة عبر uvicorn ودعم الـ Webhook عبر FastAPI"""
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

if __name__ == '__main__':
    main()
