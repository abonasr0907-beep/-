from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.config import VISITORS_FILE
from bot.database import load_json, save_json

async def visitors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    visitors = load_json(VISITORS_FILE, default=[])

    if not visitors:
        text = "📨 *طلبات الزوار:*\n\nلا توجد طلبات زوار حالياً."
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    text = f"📨 *طلبات الزوار ({len(visitors)} طلب):*\n\n"
    keyboard = []

    for idx, v in enumerate(visitors[:5]):
        vid = v.get("id", f"VIS-{idx+1}")
        vname = v.get("name", "زائر")
        vphone = v.get("phone", "غير محدد")
        vprop = v.get("property_id", "عام")
        vstatus = v.get("status", "جديد")

        stat_icon = "🟢" if vstatus == "contacted" else ("🟡" if vstatus == "following_up" else "🔴")
        text += f"{stat_icon} `{vid}` - *{vname}* ({vphone})\n   العرض: `{vprop}` | الحالة: {vstatus}\n\n"

        row = [
            InlineKeyboardButton(f"✅ تم التواصل #{vid}", callback_data=f"vis_contacted_{vid}"),
            InlineKeyboardButton(f"🔄 متابعة #{vid}", callback_data=f"vis_followup_{vid}"),
        ]
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def update_visitor_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    visitors = load_json(VISITORS_FILE, default=[])

    if data.startswith("vis_contacted_"):
        vid = data.replace("vis_contacted_", "")
        for v in visitors:
            if v.get("id") == vid:
                v["status"] = "contacted"
        save_json(VISITORS_FILE, visitors, root_key="visitors")
        await query.answer("✅ تم تحديث الحالة إلى (تم التواصل)", show_alert=True)
        await visitors_handler(update, context)
    elif data.startswith("vis_followup_"):
        vid = data.replace("vis_followup_", "")
        for v in visitors:
            if v.get("id") == vid:
                v["status"] = "following_up"
        save_json(VISITORS_FILE, visitors, root_key="visitors")
        await query.answer("🔄 تم تحديث الحالة إلى (قيد المتابعة)", show_alert=True)
        await visitors_handler(update, context)

def get_visitors_handler():
    return CallbackQueryHandler(visitors_handler, pattern="^visitors$")
