from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.config import ADMINS_FILE
from bot.database import load_json, save_json

async def admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    admins = load_json(ADMINS_FILE, default=[])

    text = f"👥 *إدارة المدراء ({len(admins)} مدراء):*\n\n"
    if not admins:
        text += "لا يوجد مدراء إضافيون مسجلون بالنظام حالياً.\n"
    else:
        for a in admins:
            text += f"• *{a.get('name', 'مدير')}* (`{a.get('username', 'N/A')}`) - صلاحيات: {a.get('role', 'كاملة')}\n"

    keyboard = [
        [InlineKeyboardButton("➕ إضافة مدير جديد", callback_data="add_new_admin")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

def get_admins_handler():
    return CallbackQueryHandler(admins_handler, pattern="^admins$")
