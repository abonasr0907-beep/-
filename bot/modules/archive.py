from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties, save_properties, update_property, delete_property

async def archive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    # Auto-archive listings older than 48h
    auto_archive_old_properties()

    properties = load_properties()
    archived_props = [p for p in properties if p.get("status") == "archived"]

    if not archived_props:
        text = "📦 *الأرشيف:*\n\n لا توجد عروض مؤرشفة حالياً."
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    text = f"📦 *الأرشيف ({len(archived_props)} عرض):*\n\n"
    keyboard = []

    for p in archived_props[:5]:
        pid = p.get("id")
        ploc = p.get("location", "غير محدد")
        ptype = p.get("type", "عقار")
        text += f"📦 `{pid}` - {ptype} | {ploc}\n"

        row = [
            InlineKeyboardButton(f"🔄 استعادة {pid}", callback_data=f"restore_arch_{pid}"),
            InlineKeyboardButton(f"🗑️ حذف نهائي {pid}", callback_data=f"perm_del_{pid}")
        ]
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_archive_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("restore_arch_"):
        pid = data.replace("restore_arch_", "")
        update_property(pid, {"status": "active", "archived_at": None})
        await query.answer(f"🔄 تم استعادة العرض {pid} إلى القائمة النشطة.", show_alert=True)
        await archive_handler(update, context)
    elif data.startswith("perm_del_"):
        pid = data.replace("perm_del_", "")
        delete_property(pid)
        await query.answer(f"🗑️ تم حذف العرض {pid} نهائياً.", show_alert=True)
        await archive_handler(update, context)

def auto_archive_old_properties():
    properties = load_properties()
    now = datetime.now()
    modified = False

    for p in properties:
        if p.get("status") == "active" and p.get("created_at"):
            try:
                created_dt = datetime.fromisoformat(p.get("created_at"))
                if now - created_dt > timedelta(hours=48):
                    p["status"] = "archived"
                    p["archived_at"] = now.isoformat()
                    modified = True
            except Exception:
                pass

    if modified:
        save_properties(properties)

def get_archive_handler():
    return CallbackQueryHandler(archive_handler, pattern="^archive$")
