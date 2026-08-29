from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.database import load_properties

async def reports_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    properties = load_properties()
    active_props = [p for p in properties if p.get('status') != 'archived']
    total_views = sum(p.get('views', 0) for p in properties)

    text = (
        "📈 *تقارير الأداء والإحصائيات*\n\n"
        f"📊 عدد العروض الكلية: {len(properties)}\n"
        f"📋 عدد العروض النشطة: {len(active_props)}\n"
        f"👁️ إجمالي المشاهدات: {total_views}\n\n"
        "يمكنك طلب التقرير الصباحي أو تصدير ملف CSV للعروض عبر الخيارات التالية:"
    )

    keyboard = [
        [InlineKeyboardButton("☀️ التقرير الصباحي", callback_data="report_morning")],
        [InlineKeyboardButton("📤 تصدير CSV للعروض والطلبات", callback_data="report_export_csv")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def morning_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.config import VISITORS_FILE
    from bot.database import load_json
    properties = load_properties()
    visitors = load_json(VISITORS_FILE, default=[])

    active_props = [p for p in properties if p.get('status') != 'archived']
    total_views = sum(p.get('views', 0) for p in properties)
    new_requests = [v for v in visitors if v.get('status') == 'new' or v.get('status') == 'pending']

    text = (
        "☀️ *التقرير الصباحي التلقائي - آفاق الإنجاز*\n\n"
        f"📋 إجمالي العروض النشطة: {len(active_props)}\n"
        f"👁️ إجمالي المشاهدات: {total_views}\n"
        f"📩 الطلبات الجديدة المعلقة: {len(new_requests)} طلب\n"
        "✨ تتمنى لكم الإدارة يوماً موفقاً ومثمراً!"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def export_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import io, csv
    from bot.config import VISITORS_FILE
    from bot.database import load_json
    properties = load_properties()
    visitors = load_json(VISITORS_FILE, default=[])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["=== PROPERTIES / العروض ==="])
    writer.writerow(["ID", "Title", "Area", "Type", "Price", "Status", "Views", "VideoURL"])
    for p in properties:
        writer.writerow([
            p.get("id", ""),
            p.get("title", ""),
            p.get("area", ""),
            p.get("type", ""),
            p.get("price_text", p.get("price", "")),
            p.get("status", "active"),
            p.get("views", 0),
            p.get("video_url", "")
        ])

    writer.writerow([])
    writer.writerow(["=== VISITOR REQUESTS / طلبات الزوار ==="])
    writer.writerow(["ID", "Name", "Phone", "Type", "Status", "Date"])
    for v in visitors:
        writer.writerow([
            v.get("id", ""),
            v.get("name", ""),
            v.get("phone", ""),
            v.get("type", ""),
            v.get("status", "pending"),
            v.get("date", "")
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    output.close()

    bio = io.BytesIO(csv_bytes)
    bio.name = "afaq_full_report.csv"
    if update.callback_query:
        await update.callback_query.message.reply_document(document=bio, caption="📊 تصدير البيانات الشامل للعروض والطلبات (CSV)")
    else:
        await update.message.reply_document(document=bio, caption="📊 تصدير البيانات الشامل للعروض والطلبات (CSV)")

def get_reports_handler():
    return CallbackQueryHandler(reports_handler, pattern="^reports$")
