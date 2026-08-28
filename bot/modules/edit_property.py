from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, CommandHandler
)
from bot.database import get_property, update_property
from utils.helpers import format_number, generate_property_link
from utils.validators import validate_price, validate_area

SELECTING_FIELD, EDITING_VALUE = range(2)

async def start_edit_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
        prop_id = data.replace("editprop_", "").replace("edit_prop_", "")
    else:
        prop_id = ""

    if not prop_id or prop_id == "edit_prop":
        msg = "✏️ *تعديل عرض*\n\nيرجى اختيار عرض من قائمة العروض لتعديله."
        if query:
            await query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return ConversationHandler.END

    prop = get_property(prop_id)
    if not prop:
        await query.edit_message_text("❌ لم يتم العثور على العرض المطلوب.")
        return ConversationHandler.END

    context.user_data["editing_prop_id"] = prop_id

    keyboard = [
        [InlineKeyboardButton("📐 المساحة", callback_data="editfield_area"), InlineKeyboardButton("💰 السعر", callback_data="editfield_price")],
        [InlineKeyboardButton("📍 المنطقة", callback_data="editfield_location"), InlineKeyboardButton("🛣️ الشوارع", callback_data="editfield_streets")],
        [InlineKeyboardButton("🟢 تغيير الحالة (نشط/مؤرشف)", callback_data="editfield_status")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="editfield_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"✏️ *تعديل العرض `{prop_id}`*\n\n"
        f"📐 المساحة: {format_number(prop.get('area', 0))} م²\n"
        f"📍 المنطقة: {prop.get('location')}\n"
        f"🛣️ الشوارع: {prop.get('streets')}\n"
        f"💰 السعر: {format_number(prop.get('price', 0))} ريال\n"
        f"📊 الحالة: {prop.get('status')}\n\n"
        "اختر الحقل المراد تعديله:"
    )
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    return SELECTING_FIELD

async def select_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    field = query.data.replace("editfield_", "")
    if field == "cancel":
        await query.edit_message_text("❌ تم إلغاء التعديل.")
        return ConversationHandler.END

    prop_id = context.user_data.get("editing_prop_id")
    prop = get_property(prop_id)

    if field == "status":
        new_status = "archived" if prop.get("status") == "active" else "active"
        update_property(prop_id, {"status": new_status})
        await query.edit_message_text(f"✅ تم تغيير حالة العرض `{prop_id}` إلى `{new_status}`.", parse_mode="Markdown")
        return ConversationHandler.END

    context.user_data["editing_field"] = field

    prompts = {
        "area": "📐 أدخل المساحة الجديدة بالمتر المربع (مثال: 600):",
        "price": "💰 أدخل السعر الجديد بالريال (مثال: 500000):",
        "location": "📍 أدخل اسم المنطقة الجديدة (مثال: الرحمانية):",
        "streets": "🛣️ أدخل عدد الشوارع الجديد (مثال: 2):"
    }
    await query.edit_message_text(prompts.get(field, "أدخل القيمة الجديدة:"), parse_mode="Markdown")
    return EDITING_VALUE

async def save_edited_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val_text = update.message.text
    prop_id = context.user_data.get("editing_prop_id")
    field = context.user_data.get("editing_field")

    updates = {}
    if field == "area":
        val = validate_area(val_text)
        if not val:
            await update.message.reply_text("❌ مساحة غير صحيحة. حاول مرة أخرى:")
            return EDITING_VALUE
        updates["area"] = val
    elif field == "price":
        val = validate_price(val_text)
        if not val:
            await update.message.reply_text("❌ سعر غير صحيح. حاول مرة أخرى:")
            return EDITING_VALUE
        updates["price"] = val
    else:
        updates[field] = val_text.strip()

    updates["property_link"] = generate_property_link(prop_id)
    update_property(prop_id, updates)

    await update.message.reply_text(
        f"✅ تم تعديل `{field}` بنجاح للعرض `{prop_id}`.\n🔗 [عرض في الموقع]({updates['property_link']})",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("❌ تم إلغاء التعديل.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("❌ تم إلغاء التعديل.")
    return ConversationHandler.END

def get_edit_property_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_edit_property, pattern="^(editprop_|edit_prop)"),
            CommandHandler("edit_property", start_edit_property),
            MessageHandler(filters.Regex("^✏️ تعديل عرض$"), start_edit_property)
        ],
        states={
            SELECTING_FIELD: [CallbackQueryHandler(select_edit_field, pattern="^editfield_")],
            EDITING_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_value)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_edit),
            CallbackQueryHandler(cancel_edit, pattern="^editfield_cancel$")
        ],
        per_message=False,
        per_chat=True,
        per_user=True
    )
