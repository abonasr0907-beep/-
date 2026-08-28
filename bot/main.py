import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from bot.config import BOT_TOKEN, WEBHOOK_URL, PORT, PHOTOS_DIR
from bot.database import init_db, load_properties, save_properties
from bot.modules.add_property import get_add_property_handler
from utils.helpers import format_number

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ Global Telegram Application ============
telegram_app = None

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ غير متوقع أثناء معالجة الطلب."
            )
        except Exception:
            pass

# ============ Bot Commands & Menu ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة عرض جديد", callback_data="add_property")],
        [InlineKeyboardButton("📋 قائمة العروض", callback_data="list_properties")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "🏡 *نظام إدارة العقارات - آفاق الإنجاز*\n\n"
        "مرحباً بك في لوحة تحكم البوت (خاص بالمدراء)."
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def list_properties_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    properties = load_properties()
    if not properties:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]]
        await query.edit_message_text(
            "📭 لا توجد عروض حالياً.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = "📋 *قائمة العروض:*\n\n"
    for p in properties[-10:]:
        text += f"• `{p.get('id', 'N/A')}` - {p.get('location', 'غير محدد')} ({format_number(p.get('area', 0))}م²) - {format_number(p.get('price', 0))} ريال [{p.get('status', 'active')}]\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ============ FastAPI Lifecycle & Webhook ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    init_db()

    if BOT_TOKEN:
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        telegram_app.add_error_handler(global_error_handler)

        # Register modules
        telegram_app.add_handler(get_add_property_handler())
        telegram_app.add_handler(CommandHandler("start", start))
        telegram_app.add_handler(CallbackQueryHandler(list_properties_handler, pattern="^list_properties$"))
        telegram_app.add_handler(CallbackQueryHandler(start, pattern="^back_to_menu$"))

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

class PropertyMapRequest(BaseModel):
    area: Optional[str] = "all"
    type: Optional[str] = "all"
    min_price: Optional[int] = None
    max_price: Optional[int] = None

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
