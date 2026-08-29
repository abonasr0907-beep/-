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

from bot.config import BOT_TOKEN, WEBHOOK_URL, PORT, VISITORS_FILE, COMPASS_FILE, ADMIN_IDS
from bot.database import init_db, load_properties, get_property, load_json, save_json
from bot.modules.add_property import get_add_property_handler
from bot.modules.list_properties import get_list_properties_handler, start_list_properties
from bot.modules.edit_property import get_edit_property_handler
from bot.modules.delete_property import get_delete_property_handler
from bot.modules.customers import get_customers_handler
from bot.modules.visitors import get_visitors_handler, visitors_handler, update_visitor_status
from bot.modules.reports import get_reports_handler, morning_report_command, export_csv_command
from bot.modules.follow_up import get_follow_up_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import time
from collections import defaultdict

app = FastAPI(title="Afaq Al-Injaz Bot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# In-memory CRM events storage & simple rate limiting
CRM_EVENTS = []
RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMIT_MAX = 60  # max 60 requests per minute per IP

@app.middleware("http")
async def security_and_rate_limiting_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    if request.url.path.startswith("/api/"):
        # Clean timestamps older than 60 seconds
        timestamps = [t for t in RATE_LIMIT_STORE[client_ip] if now - t < 60]
        if len(timestamps) >= RATE_LIMIT_MAX:
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded. Please try again in a minute."})
        timestamps.append(now)
        RATE_LIMIT_STORE[client_ip] = timestamps

    response = await call_next(request)
    # Add Security Headers including CSP
    response.headers["Content-Security-Policy"] = "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

telegram_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    logger.info("🚀 Starting bot...")
    init_db()
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("morning_report", morning_report_command))
    telegram_app.add_handler(CommandHandler("export_csv", export_csv_command))
    telegram_app.add_handler(get_add_property_handler())
    telegram_app.add_handler(get_list_properties_handler())
    telegram_app.add_handler(get_edit_property_handler())
    telegram_app.add_handler(get_delete_property_handler())
    telegram_app.add_handler(get_customers_handler())
    telegram_app.add_handler(get_visitors_handler())
    telegram_app.add_handler(get_reports_handler())
    telegram_app.add_handler(get_follow_up_handler())
    telegram_app.add_handler(CallbackQueryHandler(update_visitor_status, pattern="^vis_"))
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

def is_property_archived(prop):
    status = str(prop.get("status", "")).lower()
    if status in ["sold", "مباع", "archived", "مؤرشف"]:
        return True

    date_str = prop.get("date")
    if date_str:
        try:
            prop_date = datetime.fromisoformat(date_str)
            age_days = (datetime.now() - prop_date).days
            if age_days > 120:
                return True
        except Exception:
            pass
    return False

@app.get("/api/properties")
async def get_properties_api():
    all_props = load_properties()
    # Filter active only
    active_props = [p for p in all_props if not is_property_archived(p)]
    return active_props

@app.get("/api/properties/all")
async def get_all_properties_api():
    all_props = load_properties()
    for p in all_props:
        p["is_archived"] = is_property_archived(p)
    return all_props

@app.get("/api/properties/archived")
async def get_archived_properties_api():
    all_props = load_properties()
    archived_props = [p for p in all_props if is_property_archived(p)]
    return archived_props

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

@app.post("/api/events")
async def create_crm_event_api(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    event_type = body.get("type", "unknown")
    event_entry = {
        "id": f"EVT-{int(time.time() * 1000)}",
        "type": event_type,
        "details": body.get("details", {}),
        "url": body.get("url", ""),
        "timestamp": body.get("timestamp", datetime.now().isoformat())
    }
    CRM_EVENTS.append(event_entry)
    return {"status": "ok", "event_id": event_entry["id"]}

@app.get("/api/events")
async def get_crm_events_api():
    return {"total": len(CRM_EVENTS), "events": CRM_EVENTS}

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

    if telegram_app and telegram_app.bot:
        try:
            req_type = body.get("type", "طلب موقع")
            name = body.get("name", "غير محدد")
            phone = body.get("phone", body.get("mobile", "غير محدد"))
            details = body.get("details", body.get("notes", "بدون تفاصيل"))
            msg_text = (
                f"🔔 *طلب جديد من الموقع*\n\n"
                f"🏷️ *النوع:* {req_type}\n"
                f"👤 *الاسم:* {name}\n"
                f"📱 *الجوال:* {phone}\n"
                f"📝 *التفاصيل:* {details}"
            )
            for admin_id in ADMIN_IDS:
                await telegram_app.bot.send_message(
                    chat_id=admin_id,
                    text=msg_text,
                    parse_mode="Markdown",
                    disable_notification=True
                )
        except Exception as e:
            logger.error(f"Admin notification failed: {e}")

    return {"status": "ok", "id": req_id, "message": "Request saved successfully"}

def normalize(text):
    import re
    t = re.sub(r'[^\w\u0600-\u06FF\s]', '', text or '')
    t = re.sub(r'[إأآ]', 'ا', t)
    return re.sub(r'\s+', ' ', t).strip()

from bot.modules.add_property import start_add_property
from bot.modules.list_properties import start_list_properties
from bot.modules.edit_property import start_edit_property
from bot.modules.delete_property import start_delete_property
from bot.modules.compass import compass_handler
from bot.database import save_properties

async def reset_offers_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("⚠️ نعم احذف الكل", callback_data="confirm_reset_all_yes"),
            InlineKeyboardButton("❌ إلغاء", callback_data="confirm_reset_all_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "⚠️ *تأكيد إعادة تهيئة العروض*\n\nهل أنت تأكد من مسح جميع العروض من النظام وقت التشغيل؟"
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

ROUTES = {
  "اضافة عرض جديد": start_add_property,
  "قائمة العروض": start_list_properties,
  "تعديل عرض": start_edit_property,
  "حذف عرض": start_delete_property,
  "الارشيف": start_list_properties,
  "البوصلة": compass_handler,
  "اعادة تهيئة العروض": reset_offers_prompt,
}

def get_main_reply_keyboard():
    keyboard = [
        ["➕ إضافة عرض جديد", "📋 قائمة العروض"],
        ["✏️ تعديل عرض", "🗑️ حذف عرض"],
        ["📦 الأرشيف", "🧭 البوصلة"],
        ["🧹 إعادة تهيئة العروض"]
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
    norm = normalize(text)
    if norm in ROUTES:
        if norm == "الارشيف":
            context.user_data["list_filter_type"] = "archived"
        handler = ROUTES[norm]
        return await handler(update, context)
    else:
        await update.message.reply_text("🏡 مرحباً بك! اختر من القائمة أسفل الشاشة للتحكم بعروض آفاق الإنجاز.", reply_markup=get_main_reply_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "back_to_main":
        await query.edit_message_text("🏡 أهلاً بك في القائمة الرئيسية.")
        return
    elif data == "compass":
        return await compass_handler(update, context)
    elif data == "visitors":
        return await visitors_handler(update, context)
    elif data == "reports":
        from bot.modules.reports import reports_handler
        return await reports_handler(update, context)
    elif data == "report_morning":
        return await morning_report_command(update, context)
    elif data == "report_export_csv":
        return await export_csv_command(update, context)
    elif data == "confirm_reset_all_yes":
        save_properties([])
        await query.edit_message_text("🧹 تم إعادة تهيئة قائمة العروض وقت التشغيل بنجاح.")
        return
    elif data == "confirm_reset_all_no":
        await query.edit_message_text("❌ تم إلغاء عملية إعادة التهيئة.")
        return
    responses = {
        'archive': "📦 الأرشيف متوفر في فلاتر قائمة العروض.",
        'stats': "📊 الإحصائيات معروضة في الموقع.",
        'admins': "👥 إدارة المدراء مفعلة بحسابات النظام.",
        'assistant': "🤖 المساعد الذكي قيد التكيف.",
        'marketing': "🎬 قسم التسويق والمشاركات مفعل لكل عرض.",
        'settings': "⚙️ النظام يعمل بالإعدادات القياسية.",
        'cancel': "🔄 تم الإلغاء."
    }
    await query.edit_message_text(responses.get(data, "🏡 أهلاً بك في القائمة الرئيسية."))

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

if __name__ == '__main__':
    main()
