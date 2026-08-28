from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties, update_property, delete_property
from utils.helpers import format_number, generate_property_link

PER_PAGE = 5

async def list_properties_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    page = context.user_data.get("list_page", 0)
    filter_type = context.user_data.get("list_filter_type", "all")

    filtered_props = properties
    if filter_type != "all":
        filtered_props = [p for p in properties if p.get("type") == filter_type or p.get("status") == filter_type]

    if not filtered_props:
        text = "📭 *لا توجد عروض مطابقة حالياً.*"
        keyboard = [
            [
                InlineKeyboardButton("الكل", callback_data="filter_all"),
                InlineKeyboardButton("نشط", callback_data="filter_active"),
                InlineKeyboardButton("مسودة", callback_data="filter_draft"),
            ],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    total_pages = (len(filtered_props) + PER_PAGE - 1) // PER_PAGE
    page = max(0, min(page, total_pages - 1))
    context.user_data["list_page"] = page

    start_idx = page * PER_PAGE
    page_props = filtered_props[start_idx:start_idx + PER_PAGE]

    text = f"📋 *قائمة العروض ({page + 1}/{total_pages}):*\n\n"
    keyboard = []

    type_labels = {"land": "🏡 أرض", "resthouse": "🏠 استراحة", "farm": "🚜 مزرعة"}

    for p in page_props:
        pid = p.get("id", "N/A")
        ptype = type_labels.get(p.get("type"), p.get("type"))
        parea = format_number(p.get("area", 0))
        pprice = format_number(p.get("price", 0))
        ploc = p.get("location", "غير محدد")
        pstat = "🟢" if p.get("status") == "active" else "🟡"

        text += f"{pstat} `{pid}` - {ptype} | {ploc} | {parea}م² | {pprice} ريال\n"

        row = [
            InlineKeyboardButton(f"✏️ {pid}", callback_data=f"editprop_{pid}"),
            InlineKeyboardButton(f"🗑️", callback_data=f"delprop_{pid}"),
            InlineKeyboardButton(f"📦", callback_data=f"archprop_{pid}"),
        ]
        keyboard.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ السابق", callback_data=f"listpage_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="listpage_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("التالي ▶️", callback_data=f"listpage_{page + 1}"))
    if nav_row:
        keyboard.append(nav_row)

    filter_row = [
        InlineKeyboardButton("الكل", callback_data="filter_all"),
        InlineKeyboardButton("🏡 أراضي", callback_data="filter_land"),
        InlineKeyboardButton("🏠 استراحات", callback_data="filter_resthouse"),
        InlineKeyboardButton("🚜 مزارع", callback_data="filter_farm"),
    ]
    keyboard.append(filter_row)
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_list_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("listpage_"):
        page_str = data.replace("listpage_", "")
        if page_str != "noop":
            context.user_data["list_page"] = int(page_str)
            await list_properties_callback(update, context)
    elif data.startswith("filter_"):
        ftype = data.replace("filter_", "")
        context.user_data["list_filter_type"] = ftype
        context.user_data["list_page"] = 0
        await list_properties_callback(update, context)
    elif data.startswith("archprop_"):
        pid = data.replace("archprop_", "")
        update_property(pid, {"status": "archived"})
        await query.answer(f"📦 تم أرشفة العرض {pid}", show_alert=True)
        await list_properties_callback(update, context)

def get_list_properties_handler():
    return CallbackQueryHandler(list_properties_callback, pattern="^(list_props|list_properties)$")
