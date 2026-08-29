from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes
from bot.database import load_properties, get_property, update_property, delete_property
from utils.helpers import format_number, generate_property_link

PER_PAGE = 5

def format_ad_text(p):
    type_labels = {"land": "أرض سكنية", "resthouse": "استراحة", "farm": "مزرعة"}
    ptype = type_labels.get(p.get("type"), p.get("type"))
    parea = format_number(p.get("area", 0))
    pprice = format_number(p.get("price", 0))
    ploc = p.get("location", "غير محدد")
    pstreets = p.get("streets", "غير محدد")
    plink = p.get("property_link") or generate_property_link(p.get("id"))

    features = p.get("features", {})
    feat_lines = [f"• {k}: {v}" for k, v in features.items()]
    feat_str = "\n".join(feat_lines) if feat_lines else "• جميع الخدمات متوفرة"

    return (
        f"🌟 *عرض عقاري مميز ({p.get('id')})*\n\n"
        f"🏢 *النوع:* {ptype}\n"
        f"📍 *الموقع:* {ploc}\n"
        f"📐 *المساحة:* {parea} م²\n"
        f"🛣️ *الشوارع:* {pstreets}\n"
        f"💰 *السعر:* {pprice} ريال\n\n"
        f"✨ *المميزات:*\n{feat_str}\n\n"
        f"🔗 *رابط العرض في الموقع:*\n{plink}\n\n"
        f"📞 *للتواصل والإستفسار:* 0544699933 | 0545888931"
    )

async def start_list_properties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    page = context.user_data.get("list_page", 0)
    filter_type = context.user_data.get("list_filter_type", "all")

    filtered_props = properties
    if filter_type != "all":
        filtered_props = [p for p in properties if p.get("type") == filter_type or p.get("status") == filter_type]

    # VIP Pinning: VIP properties first
    filtered_props = sorted(filtered_props, key=lambda x: (not x.get("is_vip", False), x.get("id", "")), reverse=False)

    if not filtered_props:
        text = "📭 *لا توجد عروض مطابقة حالياً.*"
        keyboard = [
            [
                InlineKeyboardButton("الكل", callback_data="filter_all"),
                InlineKeyboardButton("🏡 أراضي", callback_data="filter_land"),
                InlineKeyboardButton("🏠 استراحات", callback_data="filter_resthouse"),
                InlineKeyboardButton("🚜 مزارع", callback_data="filter_farm"),
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
        status_icon = "🔴 مباع" if p.get("status") == "sold" else ("📦 أرشفة" if p.get("status") == "archived" else "🟢 نشط")
        vip_badge = " ⭐ عرض مميز" if p.get("is_vip") else ""
        plink = p.get("property_link") or generate_property_link(pid)

        text += f"{status_icon}{vip_badge} `{pid}` - {ptype} | {ploc} | {parea}م² | {pprice} ريال\n"

        row1 = [
            InlineKeyboardButton("🔗 عرض بالموقع", url=plink),
            InlineKeyboardButton("✏️ تعديل", callback_data=f"editprop_{pid}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"delprop_{pid}")
        ]
        row2 = [
            InlineKeyboardButton("📦 أرشفة", callback_data=f"archprop_{pid}"),
            InlineKeyboardButton("📤 مشاركة", callback_data=f"shareprop_{pid}"),
            InlineKeyboardButton(f"{'🔴 مباع' if p.get('status') == 'active' else '🟢 نشط'}", callback_data=f"toggleprop_{pid}")
        ]
        row3 = [
            InlineKeyboardButton("📝 نص الإعلان", callback_data=f"adprop_{pid}")
        ]
        keyboard.extend([row1, row2, row3])

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
            await start_list_properties(update, context)
    elif data.startswith("filter_"):
        ftype = data.replace("filter_", "")
        context.user_data["list_filter_type"] = ftype
        context.user_data["list_page"] = 0
        await start_list_properties(update, context)
    elif data.startswith("archprop_"):
        pid = data.replace("archprop_", "")
        update_property(pid, {"status": "archived"})
        await query.answer(f"📦 تم أرشفة العرض {pid}", show_alert=True)
        await start_list_properties(update, context)
    elif data.startswith("toggleprop_"):
        pid = data.replace("toggleprop_", "")
        p = get_property(pid)
        if p:
            new_status = "sold" if p.get("status") == "active" else "active"
            update_property(pid, {"status": new_status})
            await query.answer(f"تم تغيير حالة {pid} إلى {new_status}", show_alert=True)
            await start_list_properties(update, context)
    elif data.startswith("shareprop_"):
        pid = data.replace("shareprop_", "")
        p = get_property(pid)
        if p:
            ad_text = format_ad_text(p)
            photos = p.get("photos", [])
            if photos:
                try:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photos[0], caption=ad_text, parse_mode="Markdown")
                    return
                except Exception:
                    pass
            await context.bot.send_message(chat_id=update.effective_chat.id, text=ad_text, parse_mode="Markdown")
    elif data.startswith("adprop_"):
        pid = data.replace("adprop_", "")
        p = get_property(pid)
        if p:
            ad_text = format_ad_text(p)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📝 *نص الإعلان الجاهز للنسخ لعرض `{pid}`:*\n\n`{ad_text}`",
                parse_mode="Markdown"
            )

def get_list_properties_handler():
    return CallbackQueryHandler(start_list_properties, pattern="^(list_props|list_properties)$")
