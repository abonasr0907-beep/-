#!/usr/bin/env python3
"""
خادم API لاستقبال طلبات الزوار من الموقع وحفظها في visitor_requests.json على GitHub
يعمل كحل احتياطي عندما يكون خادم البوت على Railway غير متاح

المسار: POST /api/visitor-request
يقوم بـ:
1. حفظ الطلب في visitor_requests.json على GitHub (عبر Contents API)
2. إرسال إشعار تيليجرام للإدارة مع أزرار موافقة/رفض
3. إرجاع نجاح العملية
"""

import os
import sys
import json
import time
import base64
import asyncio
from datetime import datetime
from aiohttp import web, ClientSession

# ===== الإعدادات =====
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "abonasr0907-beep/-"
GITHUB_FILE_PATH = "bot/data/visitor_requests.json"
BOT_TOKEN = "8629398802:AAE2ndFy06GfV8qSQpd-cOKDccPUt_G05Os"
ADMIN_CHAT_ID = "7746757675"
TELEGRAM_API_BASE = "https://api.telegram.org/bot"
PORT = int(os.environ.get("PORT", "8090"))

# ===== دوال GitHub Contents API =====

async def github_get_file_content(session):
    """قراءة محتوى visitor_requests.json من GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content), data.get("sha", "")
        else:
            # الملف غير موجود — إنشاء بنية فارغة
            return {"requests": [], "inquiries": [], "offer_submissions": []}, None

async def github_update_file(session, content, sha, commit_msg):
    """تحديث visitor_requests.json على GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    encoded = base64.b64encode(json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii")
    payload = {
        "message": commit_msg,
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha
    async with session.put(url, headers=headers, json=payload) as resp:
        result = await resp.json()
        return resp.status == 200, result

async def github_save_request(visitor_request):
    """حفظ طلب زائر في visitor_requests.json على GitHub"""
    async with ClientSession() as session:
        # 1) قراءة المحتوى الحالي
        vdata, sha = await github_get_file_content(session)
        
        # 2) التحقق من عدم التكرار
        existing_ids = [r.get("id") for r in vdata.get("requests", [])]
        if visitor_request["id"] in existing_ids:
            print(f"[API] الطلب {visitor_request['id']} محفوظ مسبقاً — تخطي")
            return True, vdata
        
        # 3) إضافة الطلب الجديد
        vdata.setdefault("requests", []).append(visitor_request)
        
        # 4) حفظ على GitHub
        commit_msg = f"visitor request: {visitor_request['id']} — {visitor_request.get('name', '')}"
        success, result = await github_update_file(session, vdata, sha, commit_msg)
        
        if success:
            print(f"[API] ✅ تم حفظ طلب الزائر على GitHub: {visitor_request['id']}")
        else:
            print(f"[API] ❌ فشل حفظ الطلب على GitHub: {result}")
        
        return success, vdata

# ===== دوال تيليجرام =====

def build_notification_html(req):
    """بناء رسالة الإشعار بتنسيق HTML"""

    # ===== إشعار المزايدة الخاص =====
    if req.get("bidType") == "bid" or req.get("type") == "bid":
        html = f"<b>\U0001f514 طلب مزايدة جديد على عقار</b>\n\n"
        html += f"<b>\U0001f3e0 اسم العقار:</b> {req.get('offerName', req.get('propertyType', 'غير محدد'))}\n"
        html += f"<b>\U0001f517 رابط العرض:</b> {req.get('offerUrl', 'غير متوفر')}\n"
        html += f"<b>\U0001f4b0 أعلى سوم حالي:</b> {req.get('currentHighestBid', 'غير محدد')} ريال\n"
        html += f"<b>\U0001f4b8 المزايدة الجديدة:</b> {req.get('bidAmount', req.get('price', 'غير محدد'))} ريال\n\n"
        html += f"<b>\U0001f464 اسم المزايد:</b> {req.get('name', 'غير محدد')}\n"
        html += f"<b>\U0001f4f1 رقم الهاتف:</b> {req.get('phone', 'غير محدد')}\n"
        _bid_notes = req.get("bidNotes", req.get("notes", ""))
        if _bid_notes:
            html += f"<b>\U0001f4dd ملاحظات:</b> {_bid_notes}\n"
        html += f"\n<b>\U0001f4c4 رقم الطلب:</b> <code>{req.get('id', '')}</code>\n"
        html += f"<b>\U0001f550 التاريخ:</b> {req.get('submitted_at', '')}\n"
        html += f"\n<b>\U0001f4a1 مكتب آفاق الإنجاز العقاري</b>\n\U0001f310 abonasr0907-beep.github.io/-"
        return html

    # ===== إشعار الطلب العادي =====
    html = f"<b>\U0001f514 طلب عرض عقار جديد من الموقع</b>\n\n"
    html += f"<b>\U0001f464 اسم العميــل:</b> {req.get('name', 'غير محدد')}\n"
    html += f"<b>\U0001f4f1 رقم الهاتف:</b> {req.get('phone', 'غير محدد')}\n"

    # نوع العملية (بيع/إيجار)
    _op = req.get("operation_type", req.get("operationType", "sale"))
    _op_label = "\U0001f3e0 للإيجار" if _op == "rent" else "\U0001f3f7\ufe0f للبيع"
    html += f"<b>\U0001f502 عملية:</b> {_op_label}\n"

    html += f"<b>\U0001f3f7\ufe0f نوع العقار:</b> {req.get('propertyType', 'غير محدد')}\n"
    html += f"<b>\U0001f4cd الموقع:</b> {req.get('location', 'غير محدد')}\n"
    html += f"<b>\U0001f4d0 المساحة:</b> {req.get('area', 'غير محدد')} م\u00b2\n"

    # السعر حسب نوع السعر (priceType)
    _pt = req.get("priceType", "fixed")
    if _pt == "auction":
        _hb = req.get("highestBid", "")
        html += f"<b>\U0001f528 على السوم — أعلى سوم:</b> {_hb if _hb else req.get('price', 'غير محدد')} ريال\n"
    elif _pt == "negotiable":
        html += f"<b>\U0001f91d قابل للتفاوض</b>\n"
    else:
        html += f"<b>\U0001f4b0 السعر:</b> {req.get('price', 'غير محدد')} ريال\n"
    
    if req.get("description") and req["description"].strip():
        html += f"\n<b>ℹ️ الوصف:</b>\n{req['description']}\n"
    
    if req.get("latitude") and req.get("longitude"):
        maps_link = req.get("mapsLink") or f"https://www.google.com/maps?q={req['latitude']},{req['longitude']}"
        html += f"\n<b>🗺️ موقع العقار على الخريطة:</b>\n"
        html += f"<b>خط العرض (Latitude):</b> {req['latitude']}\n"
        html += f"<b>خط الطول (Longitude):</b> {req['longitude']}\n"
        html += f"<b>🔗 رابط Google Maps:</b> {maps_link}\n"
    
    img_count = req.get("imageCount", 0)
    img_note = " (تُرفقها العميل عبر WhatsApp)" if img_count > 0 else ""
    html += f"\n<b>📸 الصور:</b> {img_count} صورة{img_note}\n"
    html += f"<b>📄 رقم الطلب:</b> <code>{req.get('id', '')}</code>\n"
    html += f"<b>🕐 التاريخ:</b> {req.get('submitted_at', '')}\n"
    html += f"\n<b>💡 مكتب آفاق الإنجاز العقاري</b>\n🌐 abonasr0907-beep.github.io/-"
    return html

async def send_telegram_notification(req):
    """إرسال إشعار تيليجرام للإدارة مع أزرار موافقة/رفض (بدون أزرار للمزايدة)"""
    html = build_notification_html(req)
    req_id = req.get("id", "")
    _is_bid = req.get("bidType") == "bid" or req.get("type") == "bid"

    if _is_bid:
        # إشعار مزايدة — بدون أزرار موافقة/رفض
        url = f"{TELEGRAM_API_BASE}{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
    else:
        reply_markup = {
            "inline_keyboard": [
                [{"text": "✅ موافقة ونشر", "callback_data": f"vreq_approve_{req_id}"}],
                [{"text": "❌ رفض", "callback_data": f"vreq_reject_{req_id}"}],
            ]
        }
        url = f"{TELEGRAM_API_BASE}{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": json.dumps(reply_markup),
        }
    
    async with ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            result = await resp.json()
            if result.get("ok"):
                print(f"[API] ✅ تم إرسال إشعار تيليجرام: {req_id}")
                return True
            else:
                print(f"[API] ❌ فشل إرسال الإشعار: {result}")
                return False

async def send_telegram_images(request_id, image_data_list):
    """
    إرسال صور الطلب للمدير عبر Telegram sendMediaGroup API
    image_data_list: قائمة من (filename, bytes)
    """
    if not image_data_list:
        return True

    url = f"{TELEGRAM_API_BASE}{BOT_TOKEN}/sendMediaGroup"

    # بناء حقل media كـ JSON يحتوي على مراجع attach:// للصور
    import json as _json
    media = []
    for idx, (filename, data) in enumerate(image_data_list[:10]):
        media.append({
            "type": "photo",
            "media": f"attach://photo_{idx}",
        })

    # إضافة عنوان تشتيلي على أول صورة
    if media:
        media[0]["caption"] = f"📸 صور طلب زائر: {request_id}"

    form = aiohttp.FormData()
    form.add_field("chat_id", ADMIN_CHAT_ID)
    form.add_field("media", _json.dumps(media))

    for idx, (filename, data) in enumerate(image_data_list[:10]):
        form.add_field(
            f"photo_{idx}",
            data,
            filename=filename,
            content_type="image/jpeg",
        )

    try:
        async with ClientSession() as session:
            async with session.post(url, data=form) as resp:
                result = await resp.json()
                if result.get("ok"):
                    print(f"[API] ✅ تم إرسال {len(image_data_list[:10])} صورة للمدير: {request_id}")
                    return True
                else:
                    print(f"[API] ❌ فشل إرسال الصور: {result}")
                    return False
    except Exception as e:
        print(f"[API] ❌ خطأ في إرسال الصور: {e}")
        return False


# ===== معالج API =====

async def handle_visitor_request(request):
    """استقبال طلب زائر من الموقع"""
    try:
        data = await request.json()
    except Exception:
        try:
            data = dict(await request.post())
        except Exception as e:
            return web.json_response({"ok": False, "error": f"invalid data: {e}"}, status=400)
    
    # التحقق من الحقول الأساسية
    if not data.get("name") or not data.get("phone"):
        return web.json_response({"ok": False, "error": "name and phone are required"}, status=400)
    
    # بناء سجل الطلب
    request_id = data.get("id", f"REQ-{int(time.time())}")
    visitor_request = {
        "id": request_id,
        "name": str(data.get("name", "")),
        "phone": str(data.get("phone", "")),
        "propertyType": str(data.get("propertyType", data.get("property_type", ""))),
        "location": str(data.get("location", "")),
        "area": str(data.get("area", "")),
        "price": str(data.get("price", "")),
        "priceType": str(data.get("priceType", data.get("price_type", "fixed"))),
        "highestBid": str(data.get("highestBid", data.get("highest_bid", ""))),
        "operation_type": str(data.get("operation_type", data.get("operationType", "sale"))),
        "description": str(data.get("description", "")),
        "latitude": str(data.get("latitude", "")),
        "longitude": str(data.get("longitude", "")),
        "mapsLink": str(data.get("mapsLink", data.get("maps_link", ""))),
        "imageCount": int(data.get("imageCount", data.get("image_count", 0)) or 0),
        # حقول المزايدة (bid)
        "bidType": str(data.get("bidType", data.get("bid_type", ""))),
        "offerId": str(data.get("offerId", data.get("offer_id", ""))),
        "offerName": str(data.get("offerName", data.get("offer_name", ""))),
        "offerUrl": str(data.get("offerUrl", data.get("offer_url", ""))),
        "currentHighestBid": str(data.get("currentHighestBid", data.get("current_highest_bid", ""))),
        "bidAmount": str(data.get("bidAmount", data.get("bid_amount", ""))),
        "bidNotes": str(data.get("bidNotes", data.get("bid_notes", data.get("notes", "")))),
        "source": str(data.get("source", "website_api")),
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "pending",
    }
    
    print(f"[API] 📥 طلب جديد: {request_id} — {visitor_request['name']}")
    
    # 1) حفظ الطلب في visitor_requests.json على GitHub (قبل الإشعار)
    save_ok = False
    try:
        save_ok, vdata = await github_save_request(visitor_request)
    except Exception as e:
        print(f"[API] ❌ خطأ في حفظ الطلب: {e}")
        save_ok = False
    
    if not save_ok:
        return web.json_response({"ok": False, "error": "save failed"}, status=500)
    
    # 2) إرسال إشعار للإدارة مع أزرار موافقة/رفض
    try:
        await send_telegram_notification(visitor_request)
    except Exception as e:
        print(f"[API] ❌ خطأ في إرسال الإشعار: {e}")
        # الطلب محفوظ حتى لو فشل الإشعار
    
    return web.json_response({
        "ok": True,
        "id": request_id,
        "message": "تم استلام الطلب وحفظه بنجاح"
    })

async def handle_visitor_images(request):
    """
    استقبال صور طلب الزائر (multipart/form-data)
    المسار: POST /api/visitor-images
    الحقول: requestId (نص) + images (ملفات صور)
    يرفع الصور إلى GitHub في images/visitor/{requestId}/ ثم يحدّث الطلب
    """
    if not GITHUB_TOKEN:
        return web.json_response({"ok": False, "error": "GITHUB_TOKEN not configured"}, status=500)

    try:
        reader = await request.multipart()
        request_id = None
        image_files = []
        async for part in reader:
            if part.name == "requestId":
                request_id = (await part.text()).strip()
            elif part.name == "images":
                data = await part.read()
                filename = part.filename or f"img_{len(image_files)}.jpg"
                image_files.append((filename, data))

        if not request_id:
            return web.json_response({"ok": False, "error": "requestId is required"}, status=400)
        if not image_files:
            return web.json_response({"ok": False, "error": "no images provided"}, status=400)

        print(f"[API] 📷 رفع {len(image_files)} صورة للطلب {request_id}")

        image_paths = []
        for idx, (filename, data) in enumerate(image_files):
            safe_name = f"img_{idx}_" + "".join(ch for ch in filename if ch.isalnum() or ch in "._-")
            if not safe_name.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                safe_name += ".jpg"
            gh_path = f"images/visitor/{request_id}/{safe_name}"
            web_path = gh_path
            ok = await github_upload_image(gh_path, data, f"visitor image: {request_id} - {safe_name}")
            if ok:
                image_paths.append(web_path)

        if not image_paths:
            return web.json_response({"ok": False, "error": "failed to upload images"}, status=500)

        updated = await github_update_request_images(request_id, image_paths)
        # Task 2: إرسال الصور الفعلية للمدير عبر Telegram
        try:
            await send_telegram_images(request_id, image_files)
        except Exception as e:
            print(f"[API] ⚠️ تعذّر إرسال الصور للمدير: {e}")
        return web.json_response({"ok": True, "requestId": request_id, "images": image_paths, "count": len(image_paths), "updated": updated})
    except Exception as e:
        print(f"[API] ❌ خطأ في رفع الصور: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def github_upload_image(path, data, commit_msg):
    """رفع صورة (binary) إلى GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    encoded = base64.b64encode(data).decode("ascii")
    payload = {"message": commit_msg, "content": encoded}
    async with ClientSession() as session:
        async with session.put(url, headers=headers, json=payload) as resp:
            return resp.status in (200, 201)


async def github_update_request_images(request_id, image_paths):
    """تحديث طلب زائر في visitor_requests.json بإضافة مسارات الصور"""
    async with ClientSession() as session:
        vdata, sha = await github_get_file_content(session)
        updated = False
        for r in vdata.get("requests", []):
            if r.get("id") == request_id:
                r["images"] = image_paths
                r["imageCount"] = len(image_paths)
                updated = True
                break
        if updated:
            success, _ = await github_update_file(session, vdata, sha, f"add images to visitor request {request_id}")
            return success
        return False


async def handle_health(request):
    """فحص صحة الخادم"""
    return web.json_response({"ok": True, "status": "running", "service": "visitor-api"})

async def handle_root(request):
    """الصفحة الرئيسية"""
    return web.json_response({
        "ok": True,
        "service": "Afaq Visitor Request API",
        "endpoints": ["/api/visitor-request", "/health"]
    })

# ===== تشغيل الخادم =====

def create_app():
    """إنشاء تطبيق aiohttp"""
    app = web.Application()
    app.router.add_post("/api/visitor-request", handle_visitor_request)
    app.router.add_post("/api/visitor-images", handle_visitor_images)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_root)
    return app

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN غير متوفر! لن يتم حفظ الطلبات.")
    print(f"🚀 تشغيل خادم API على المنفذ {PORT}")
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)
