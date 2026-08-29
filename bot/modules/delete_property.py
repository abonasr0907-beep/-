from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes
from bot.database import load_properties, get_property, delete_property

CONFIRM_DELETE = range(1)

async def start_delete_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
        prop_id = data.replace("delprop_", "").replace("delete_prop_", "")
    else:
        prop_id = ""

    if not prop_id or prop_id in ["delete_prop", "delprop"]:
        properties = load_properties()
        if not properties:
            msg = "📭 *لا توجد عروض متاحة للحذف حالياً.*"
            if query:
                await query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, parse_mode="Markdown")
            return ConversationHandler.END

        keyboard = []
        type_labels = {"land": "أرض", "resthouse": "استراحة", "farm": "مزرعة"}
        for p in properties:
            pid = p.get("id")
            ptype = type_labels.get(p.get("type"), p.get("type"))
            ploc = p.get("location", "")
            keyboard.append([InlineKeyboardButton(f"🗑️ {pid} - {ptype} | {ploc}", callback_data=f"delprop_{pid}")])
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "🗑️ *اختر العرض المراد حذفه:*"
        if query:
            await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        return ConversationHandler.END

    prop = get_property(prop_id)
    if not prop:
        await query.edit_message_text("❌ لم يتم العثور على العرض المطلوب.")
        return ConversationHandler.END

    context.user_data["deleting_prop_id"] = prop_id

    keyboard = [
        [
            InlineKeyboardButton("⚠️ نعم، حذف نهائي", callback_data="confirm_delete_yes"),
            InlineKeyboardButton("❌ إلغاء", callback_data="confirm_delete_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"⚠️ *تأكيد الحذف النهائي*\n\nهل أنت تأكد من حذف العرض `{prop_id}` نهائياً من النظام والموقع؟",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CONFIRM_DELETE

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    prop_id = context.user_data.get("deleting_prop_id")

    if data == "confirm_delete_yes":
        delete_property(prop_id)
        await query.edit_message_text(f"🗑️ تم حذف العرض `{prop_id}` نهائياً من قاعدة البيانات والموقع.", parse_mode="Markdown")
    else:
        await query.edit_message_text("❌ تم إلغاء عملية الحذف.")

    return ConversationHandler.END

async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    msg_text = "🔄 تم الإلغاء"
    if update.message:
        await update.message.reply_text(msg_text)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg_text)
    return ConversationHandler.END

def get_delete_property_handler():
    common_handlers = [
        MessageHandler(filters.Regex("إلغاء") | filters.Regex("❌ إلغاء"), cancel_delete),
        CallbackQueryHandler(cancel_delete, pattern="^(cancel|confirm_delete_no)$")
    ]

    return ConversationHandler(
        conversation_timeout=900,
        entry_points=[
            CallbackQueryHandler(start_delete_property, pattern="^(delprop_|delete_prop)"),
            CommandHandler("delete_property", start_delete_property),
            MessageHandler(filters.Regex("حذف عرض"), start_delete_property)
        ],
        states={
            CONFIRM_DELETE: [
                CallbackQueryHandler(handle_delete_confirmation, pattern="^confirm_delete_"),
                *common_handlers
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_delete),
            MessageHandler(filters.Regex("إلغاء") | filters.Regex("❌ إلغاء"), cancel_delete),
            CallbackQueryHandler(cancel_delete, pattern="^(cancel|confirm_delete_no)$")
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
