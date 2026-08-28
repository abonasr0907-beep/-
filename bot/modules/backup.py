import os
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.config import BACKUPS_DIR, PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE

def create_backup():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subfolder = os.path.join(BACKUPS_DIR, f"backup_{timestamp}")
    os.makedirs(backup_subfolder, exist_ok=True)

    for src in [PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE]:
        if os.path.exists(src):
            shutil.copy(src, backup_subfolder)

    # Keep only last 7 backups
    all_backups = sorted([os.path.join(BACKUPS_DIR, d) for d in os.listdir(BACKUPS_DIR)])
    if len(all_backups) > 7:
        for old_b in all_backups[:-7]:
            shutil.rmtree(old_b, ignore_errors=True)

    return backup_subfolder

async def backup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    path = create_backup()
    text = (
        "💾 *النسخ الاحتياطي لقاعدة البيانات*\n\n"
        f"✅ تم إنشاء نسخة احتياطية جديدة بنجاح!\n"
        f"📂 المسار: `{path}`\n"
        "🛡️ يتم الاحتفاظ بأحدث 7 نسخ احتياطية تلقائياً."
    )

    keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_backup_handler():
    return CallbackQueryHandler(backup_handler, pattern="^backup$")
