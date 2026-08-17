#!/usr/bin/env python3
"""
لوحة التحكم الخلفية - Admin API Engine & Ultimate Security Shield (M22-CORE)
مسارات آمنة محاطة بـ try/except لحماية البوت من التوقف.
تعتمد توثيق SHA256، نظام OTP من خطوتين للمالك، جلسات 12 ساعة، Rate Limit موحد،
وحظر التخمين بعد 5 محاولات فاشلة مع تنبيه خفي للمالك، وإبطال الجلسات عند تغيير الرمز.
"""

import os
import sys
import json
import time
import hashlib
import uuid
import random
import csv
import io
import urllib.request
import logging
from pathlib import Path
from datetime import datetime
from aiohttp import web

logger = logging.getLogger("api_admin")

# المسارات والملفات
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bot"))

OFFERS_PATH = REPO_ROOT / "offers-data" / "offers.json"
MANAGERS_PATH = REPO_ROOT / "data" / "managers.json"
VISITOR_REQUESTS_PATH = REPO_ROOT / "bot" / "data" / "visitor_requests.json"
ADS_PATH = REPO_ROOT / "data" / "ads.json"
SCHEDULE_PATH = REPO_ROOT / "data" / "schedule.json"
TEMPLATES_PATH = REPO_ROOT / "data" / "templates.json"
AUDIT_LOG_PATH = REPO_ROOT / "data" / "audit_log.json"

# الثوابت الأمنية
OWNER_TELEGRAM_ID = "7746757675"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DEFAULT_PASSCODE = "afaq2026admin"
ADMIN_PASSCODE = os.environ.get("ADMIN_PASSCODE", DEFAULT_PASSCODE)
TOKEN_DURATION = 12 * 3600  # 12 hours in seconds
OTP_EXPIRY_SECONDS = 300   # 5 minutes

# الذاكرة الحية للجلسات والـ OTP والـ Rate Limiting
SESSIONS = {}        # token -> {"user": "admin", "created_at": ts, "expires_at": ts, "ip": ip}
PENDING_OTPS = {}    # challenge_id -> {"code": "123456", "created_at": ts, "ip": ip}
FAILED_ATTEMPTS = {} # ip -> {"count": int, "lock_until": ts}
IP_REQUESTS = {}     # ip -> list of timestamps
RATE_LIMIT_WINDOW = 60 # seconds
RATE_LIMIT_MAX = 30    # requests per window


# ============================================================
#  المساعدات والوظائف الأمنية
# ============================================================

def send_owner_telegram_msg(text: str) -> bool:
    """إرسال إشعار تلغرام للمالك حصراً"""
    bot_token = os.environ.get("BOT_TOKEN", "") or BOT_TOKEN
    if not bot_token:
        logger.warning("BOT_TOKEN not configured for Telegram notifications")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": OWNER_TELEGRAM_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Error sending Telegram msg to Owner: {e}")
        return False

def hash_passcode(passcode: str) -> str:
    """تشفير الرمز باستخدام SHA256"""
    return hashlib.sha256(str(passcode).strip().encode("utf-8")).hexdigest()

def verify_passcode(provided: str) -> bool:
    """التحقق من صحة الرمز الممرر"""
    if not provided:
        return False
    expected_hash = hash_passcode(ADMIN_PASSCODE)
    provided_hash = hash_passcode(provided)
    return provided_hash == expected_hash

def check_rate_limit(ip: str) -> bool:
    """معدل الطلبات الموحد لـ Rate Limiting"""
    now = time.time()
    reqs = IP_REQUESTS.get(ip, [])
    reqs = [t for t in reqs if now - t < RATE_LIMIT_WINDOW]
    IP_REQUESTS[ip] = reqs
    if len(reqs) >= RATE_LIMIT_MAX:
        return False
    reqs.append(now)
    return True

def is_locked_out(ip: str) -> bool:
    """فحص القفل المؤقت 30 دقيقة عند التخمين المتكرر"""
    now = time.time()
    attempt_info = FAILED_ATTEMPTS.get(ip, {})
    lock_until = attempt_info.get("lock_until", 0)
    if now < lock_until:
        return True
    return False

def record_failed_attempt(ip: str):
    """تسجيل محاولة فاشلة وإقفال الـ IP لـ 30 دقيقة بعد 5 محاولات + تنبيه خفي"""
    now = time.time()
    info = FAILED_ATTEMPTS.get(ip, {"count": 0, "lock_until": 0})
    info["count"] += 1
    if info["count"] >= 5:
        info["lock_until"] = now + (30 * 60)  # 30 minute lockout
        info["count"] = 0
        send_owner_telegram_msg(
            f"🚨 *الدرع الأقصى: تنبيه أمني خفي!*\n\n"
            f"تم حظر العنوان `{ip}` لمدة 30 دقيقة بعد 5 محاولات دخول أو OTP فاشلة متتالية."
        )
    FAILED_ATTEMPTS[ip] = info

def clear_failed_attempts(ip: str):
    """إعادة ضبط المحاولات الفاشلة عند الدخول الناجح"""
    FAILED_ATTEMPTS.pop(ip, None)

def invalidate_all_sessions(reason: str = "security_action"):
    """إبطال جميع التوكنات وتوجيه الخروج من كل الأجهزة عند تغيير الرمز أو طلب الخروج الشامل"""
    SESSIONS.clear()
    log_audit("invalidate_all_sessions", {"reason": reason})

def log_audit(action: str, details: dict, user: str = "admin"):
    """تسجيل عملية في سجل التدقيق data/audit_log.json"""
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        if AUDIT_LOG_PATH.exists():
            try:
                with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                    entries = json.load(f).get("entries", [])
            except Exception:
                entries = []
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "user": user,
            "details": details
        }
        entries.append(entry)
        if len(entries) > 1000:
            entries = entries[-1000:]
        with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump({"entries": entries}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error logging audit: {e}")

def validate_token(request: web.Request) -> bool:
    """التحقق من صلاحية التوكن في الترويسة"""
    auth = request.headers.get("Authorization", "")
    token = auth[7:].strip() if auth.startswith("Bearer ") else request.headers.get("X-Admin-Token", "").strip()

    if not token or token not in SESSIONS:
        return False
    session = SESSIONS[token]
    if time.time() > session.get("expires_at", 0):
        SESSIONS.pop(token, None)
        return False
    return True

def require_auth(handler):
    """مغلف التحقق من التوكن محاط بـ try/except"""
    async def wrapper(request):
        try:
            client_ip = request.remote or "127.0.0.1"
            if not check_rate_limit(client_ip):
                return web.json_response({"ok": False, "error": "rate_limit_exceeded"}, status=429)
            if not validate_token(request):
                return web.json_response({"ok": False, "error": "unauthorized"}, status=401)
            return await handler(request)
        except Exception as e:
            logger.error(f"Handler error in {handler.__name__}: {e}")
            return web.json_response({"ok": False, "error": f"internal_error: {str(e)}"}, status=500)
    return wrapper


# ============================================================
#  مسارات المصادقة من خطوتين (Password + OTP) وتغيير الرمز
# ============================================================

async def handle_login(request: web.Request):
    """
    POST /api/admin/login
    الخطوة 1: التحقق من الرمز وإرسال رمز OTP لمحادثة المالك فقط
    """
    try:
        client_ip = request.remote or "127.0.0.1"
        if is_locked_out(client_ip):
            return web.json_response({"ok": False, "error": "locked_out_30m"}, status=429)

        if not check_rate_limit(client_ip):
            return web.json_response({"ok": False, "error": "rate_limit_exceeded"}, status=429)

        data = {}
        try:
            data = await request.json()
        except Exception:
            data = dict(await request.post())

        passcode = data.get("passcode") or data.get("password") or ""
        if verify_passcode(passcode):
            otp_code = f"{random.randint(100000, 999999)}"
            challenge_id = str(uuid.uuid4())
            now = time.time()

            PENDING_OTPS[challenge_id] = {
                "code": otp_code,
                "created_at": now,
                "ip": client_ip
            }

            msg_text = (
                f"🔐 *الدرع الأقصى: رمز الدخول OTP*\n\n"
                f"رمز التحقق للوحة التحكم هو:\n"
                f"`{otp_code}`\n\n"
                f"⏰ صلاحية الرمز 5 دقائق."
            )
            send_owner_telegram_msg(msg_text)

            log_audit("admin_login_passcode_ok_otp_sent", {"ip": client_ip, "challenge_id": challenge_id})
            return web.json_response({
                "ok": True,
                "otp_required": True,
                "challenge_id": challenge_id,
                "message": "otp_sent_to_owner_telegram"
            })
        else:
            record_failed_attempt(client_ip)
            log_audit("admin_login_failed_passcode", {"ip": client_ip})
            return web.json_response({"ok": False, "error": "invalid_credentials"}, status=401)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_verify_otp(request: web.Request):
    """
    POST /api/admin/verify-otp
    الخطوة 2: التحقق من رمز OTP وإصدار توكن 12 ساعة عند الصحة فقط
    """
    try:
        client_ip = request.remote or "127.0.0.1"
        if is_locked_out(client_ip):
            return web.json_response({"ok": False, "error": "locked_out_30m"}, status=429)

        if not check_rate_limit(client_ip):
            return web.json_response({"ok": False, "error": "rate_limit_exceeded"}, status=429)

        data = {}
        try:
            data = await request.json()
        except Exception:
            data = dict(await request.post())

        challenge_id = str(data.get("challenge_id", "")).strip()
        user_otp = str(data.get("otp_code", "")).strip()

        pending = PENDING_OTPS.get(challenge_id)
        if not pending:
            record_failed_attempt(client_ip)
            return web.json_response({"ok": False, "error": "invalid_or_expired_challenge"}, status=400)

        now = time.time()
        if now - pending["created_at"] > OTP_EXPIRY_SECONDS:
            PENDING_OTPS.pop(challenge_id, None)
            record_failed_attempt(client_ip)
            return web.json_response({"ok": False, "error": "otp_expired"}, status=400)

        if pending["code"] == user_otp:
            PENDING_OTPS.pop(challenge_id, None)
            clear_failed_attempts(client_ip)

            token = str(uuid.uuid4())
            expires_at = now + TOKEN_DURATION
            SESSIONS[token] = {
                "user": "admin",
                "created_at": now,
                "expires_at": expires_at,
                "ip": client_ip
            }
            log_audit("admin_login_otp_verified_success", {"ip": client_ip})
            return web.json_response({
                "ok": True,
                "token": token,
                "expires_at": expires_at,
                "duration_hours": 12
            })
        else:
            record_failed_attempt(client_ip)
            log_audit("admin_login_otp_failed", {"ip": client_ip})
            return web.json_response({"ok": False, "error": "invalid_otp_code"}, status=401)

    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_change_passcode(request: web.Request):
    """
    POST /api/admin/change-passcode
    تغيير رمز الدخول وإبطال جميع التوكنات فوراً
    """
    global ADMIN_PASSCODE
    try:
        body = await request.json()
        new_passcode = str(body.get("new_passcode", "")).strip()
        if not new_passcode or len(new_passcode) < 6:
            return web.json_response({"ok": False, "error": "new_passcode_too_short"}, status=400)

        ADMIN_PASSCODE = new_passcode
        invalidate_all_sessions("passcode_changed")
        log_audit("change_passcode", {"message": "Passcode updated and all tokens revoked"})
        return web.json_response({"ok": True, "message": "passcode_changed_all_tokens_revoked"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_logout(request: web.Request):
    """POST /api/admin/logout & خروج من كل الأجهزة"""
    try:
        auth = request.headers.get("Authorization", "")
        token = auth[7:].strip() if auth.startswith("Bearer ") else request.headers.get("X-Admin-Token", "").strip()
        all_devices = False
        try:
            body = await request.json()
            all_devices = body.get("all_devices", False)
        except Exception:
            pass

        if all_devices:
            invalidate_all_sessions("logout_all_devices")
            return web.json_response({"ok": True, "message": "logged_out_all_devices"})
        elif token and token in SESSIONS:
            SESSIONS.pop(token, None)
            log_audit("logout_single_device", {})

        return web.json_response({"ok": True, "message": "logged_out"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


# ============================================================
#  إدارة العروض Offers CRUD + Verified
# ============================================================

@require_auth
async def handle_get_offers(request: web.Request):
    """GET /api/admin/offers"""
    try:
        from config import read_offers_live
        data = read_offers_live()
        return web.json_response({"ok": True, "count": len(data.get("offers", [])), "offers": data.get("offers", [])})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_save_offer(request: web.Request):
    """POST /api/admin/offers"""
    try:
        from config import read_offers_live, save_offers_live
        offer_data = await request.json()
        offer_id = offer_data.get("id")
        if not offer_id:
            offer_id = f"AFQ-{datetime.now().strftime('%Y')}-{int(time.time()) % 10000:04d}"
            offer_data["id"] = offer_id

        # Clean undefined strings & unify area
        for k, v in list(offer_data.items()):
            if str(v).strip().lower() == "undefined":
                offer_data[k] = ""
        if "space" in offer_data and not offer_data.get("area"):
            offer_data["area"] = offer_data["space"]

        live_data = read_offers_live()
        offers = live_data.get("offers", [])
        found = False
        for idx, o in enumerate(offers):
            if o.get("id") == offer_id:
                offers[idx] = offer_data
                found = True
                break
        if not found:
            offers.append(offer_data)

        live_data["offers"] = offers
        save_offers_live(live_data)
        log_audit("save_offer", {"offer_id": offer_id, "is_new": not found})
        return web.json_response({"ok": True, "id": offer_id, "offer": offer_data})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_toggle_verified(request: web.Request):
    """PUT /api/admin/offers/{id}/verified"""
    try:
        from config import read_offers_live, save_offers_live
        offer_id = request.match_info.get("id", "")
        body = await request.json()
        verified_state = bool(body.get("verified", True))

        live_data = read_offers_live()
        offers = live_data.get("offers", [])
        updated = False
        for o in offers:
            if o.get("id") == offer_id:
                o["verified"] = verified_state
                updated = True
                break

        if updated:
            save_offers_live(live_data)
            log_audit("toggle_verified", {"offer_id": offer_id, "verified": verified_state})
            return web.json_response({"ok": True, "id": offer_id, "verified": verified_state})
        return web.json_response({"ok": False, "error": "offer_not_found"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_delete_offer(request: web.Request):
    """DELETE /api/admin/offers/{id}"""
    try:
        from config import read_offers_live, save_offers_live
        offer_id = request.match_info.get("id", "")
        live_data = read_offers_live()
        offers = live_data.get("offers", [])
        initial_len = len(offers)
        offers = [o for o in offers if o.get("id") != offer_id]
        if len(offers) < initial_len:
            live_data["offers"] = offers
            save_offers_live(live_data)
            log_audit("delete_offer", {"offer_id": offer_id})
            return web.json_response({"ok": True, "deleted_id": offer_id})
        return web.json_response({"ok": False, "error": "offer_not_found"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


# ============================================================
#  طلبات الزوار المعلقة pending_visitor
# ============================================================

@require_auth
async def handle_get_pending(request: web.Request):
    """GET /api/admin/pending"""
    try:
        data = {"requests": []}
        if VISITOR_REQUESTS_PATH.exists():
            with open(VISITOR_REQUESTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        return web.json_response({"ok": True, "requests": data.get("requests", [])})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_approve_pending(request: web.Request):
    """POST /api/admin/pending/approve"""
    try:
        from config import read_offers_live, save_offers_live
        body = await request.json()
        req_id = body.get("id")
        if not req_id:
            return web.json_response({"ok": False, "error": "request_id_required"}, status=400)

        vdata = {"requests": []}
        if VISITOR_REQUESTS_PATH.exists():
            with open(VISITOR_REQUESTS_PATH, "r", encoding="utf-8") as f:
                vdata = json.load(f)

        found_req = None
        for r in vdata.get("requests", []):
            if r.get("id") == req_id:
                r["status"] = "approved"
                found_req = r
                break

        if found_req:
            with open(VISITOR_REQUESTS_PATH, "w", encoding="utf-8") as f:
                json.dump(vdata, f, ensure_ascii=False, indent=2)

            new_offer = {
                "id": f"AFQ-VIS-{int(time.time()) % 10000:04d}",
                "title": f"{found_req.get('propertyType', 'عقار')} - {found_req.get('location', 'الخرج')}",
                "category": found_req.get("propertyType", "أراضي"),
                "price": found_req.get("price", "على السوم"),
                "area": found_req.get("area", ""),
                "description": found_req.get("description", ""),
                "status": "published",
                "verified": True,
                "images": found_req.get("images", []),
                "map_link": found_req.get("mapsLink", "")
            }
            live = read_offers_live()
            live.setdefault("offers", []).append(new_offer)
            save_offers_live(live)

            log_audit("approve_pending_visitor", {"req_id": req_id, "new_offer_id": new_offer["id"]})
            return web.json_response({"ok": True, "req_id": req_id, "offer_id": new_offer["id"]})

        return web.json_response({"ok": False, "error": "request_not_found"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_reject_pending(request: web.Request):
    """POST /api/admin/pending/reject"""
    try:
        body = await request.json()
        req_id = body.get("id")
        reason = body.get("reason", "مرفوض من لوحة التحكم")

        vdata = {"requests": []}
        if VISITOR_REQUESTS_PATH.exists():
            with open(VISITOR_REQUESTS_PATH, "r", encoding="utf-8") as f:
                vdata = json.load(f)

        updated = False
        for r in vdata.get("requests", []):
            if r.get("id") == req_id:
                r["status"] = "rejected"
                r["reject_reason"] = reason
                updated = True
                break

        if updated:
            with open(VISITOR_REQUESTS_PATH, "w", encoding="utf-8") as f:
                json.dump(vdata, f, ensure_ascii=False, indent=2)
            log_audit("reject_pending_visitor", {"req_id": req_id, "reason": reason})
            return web.json_response({"ok": True, "req_id": req_id})
        return web.json_response({"ok": False, "error": "request_not_found"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


# ============================================================
#  إدارة المدراء والإعلانات والجدولة والقوالب
# ============================================================

@require_auth
async def handle_managers(request: web.Request):
    """GET / POST / DELETE /api/admin/managers"""
    try:
        from config import save_managers_live
        if request.method == "GET":
            data = {"managers": []}
            if MANAGERS_PATH.exists():
                with open(MANAGERS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            return web.json_response({"ok": True, "managers": data.get("managers", [])})

        elif request.method == "POST":
            mgr = await request.json()
            save_managers_live([mgr])
            log_audit("save_manager", {"mgr_id": mgr.get("id") or mgr.get("telegram_id")})
            return web.json_response({"ok": True, "manager": mgr})

        elif request.method == "DELETE":
            mgr_id = request.query.get("id") or (await request.json()).get("id")
            if str(mgr_id) == OWNER_TELEGRAM_ID:
                return web.json_response({"ok": False, "error": "cannot_delete_owner"}, status=403)

            data = {"managers": []}
            if MANAGERS_PATH.exists():
                with open(MANAGERS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            mgrs = [m for m in data.get("managers", []) if str(m.get("id") or m.get("telegram_id")) != str(mgr_id)]
            save_managers_live(mgrs)
            log_audit("delete_manager", {"mgr_id": mgr_id})
            return web.json_response({"ok": True, "deleted_id": mgr_id})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_ads(request: web.Request):
    """GET / POST /api/admin/ads"""
    try:
        if request.method == "GET":
            data = {"ads": []}
            if ADS_PATH.exists():
                with open(ADS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            return web.json_response({"ok": True, "ads": data.get("ads", [])})
        else:
            ads_payload = await request.json()
            ADS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(ADS_PATH, "w", encoding="utf-8") as f:
                json.dump(ads_payload, f, ensure_ascii=False, indent=2)
            log_audit("update_ads", {"count": len(ads_payload.get("ads", []))})
            return web.json_response({"ok": True, "ads": ads_payload})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_schedule(request: web.Request):
    """GET / POST /api/admin/schedule"""
    try:
        if request.method == "GET":
            data = {"jobs": []}
            if SCHEDULE_PATH.exists():
                with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            return web.json_response({"ok": True, "jobs": data.get("jobs", [])})
        else:
            sched_payload = await request.json()
            SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
                json.dump(sched_payload, f, ensure_ascii=False, indent=2)
            log_audit("update_schedule", {})
            return web.json_response({"ok": True, "schedule": sched_payload})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_templates(request: web.Request):
    """GET / POST /api/admin/templates ({اسم}{سعر}{منطقة}{رابط})"""
    try:
        if request.method == "GET":
            data = {
                "templates": [
                    {
                        "id": "default_offer",
                        "name": "قالب تسويق عرض",
                        "content": "✨ *{اسم}*\n📍 المنطقة: {منطقة}\n💰 السعر: {سعر}\n🔗 للتفاصيل: {رابط}"
                    }
                ]
            }
            if TEMPLATES_PATH.exists():
                with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            return web.json_response({"ok": True, "templates": data.get("templates", [])})
        else:
            tpl_payload = await request.json()
            TEMPLATES_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(TEMPLATES_PATH, "w", encoding="utf-8") as f:
                json.dump(tpl_payload, f, ensure_ascii=False, indent=2)
            log_audit("update_templates", {})
            return web.json_response({"ok": True, "templates": tpl_payload})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_stats(request: web.Request):
    """GET /api/admin/stats"""
    try:
        from config import read_offers_live
        offers_cnt = len(read_offers_live().get("offers", []))

        managers_cnt = 0
        if MANAGERS_PATH.exists():
            with open(MANAGERS_PATH, "r", encoding="utf-8") as f:
                managers_cnt = len(json.load(f).get("managers", []))

        pending_cnt = 0
        if VISITOR_REQUESTS_PATH.exists():
            with open(VISITOR_REQUESTS_PATH, "r", encoding="utf-8") as f:
                pending_cnt = sum(1 for r in json.load(f).get("requests", []) if r.get("status") == "pending")

        return web.json_response({
            "ok": True,
            "offers_count": offers_cnt,
            "managers_count": managers_cnt,
            "pending_requests_count": pending_cnt,
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_refresh(request: web.Request):
    """POST /api/admin/refresh"""
    try:
        from config import read_offers_live, generate_offers_index
        data = read_offers_live()
        generate_offers_index(data)
        log_audit("system_refresh", {})
        return web.json_response({"ok": True, "message": "index_refreshed", "offers_count": len(data.get("offers", []))})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@require_auth
async def handle_export_csv(request: web.Request):
    """GET /api/admin/export/csv"""
    try:
        from config import read_offers_live
        offers = read_offers_live().get("offers", [])

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Title", "Category", "Price", "Area", "Status", "Verified", "Map Link"])

        for o in offers:
            writer.writerow([
                o.get("id", ""),
                o.get("title", ""),
                o.get("category", ""),
                o.get("price", ""),
                o.get("area", ""),
                o.get("status", ""),
                o.get("verified", False),
                o.get("map_link", "")
            ])

        csv_content = output.getvalue()
        return web.Response(
            body=csv_content.encode("utf-8-sig"),
            content_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=afaq_offers_export.csv"}
        )
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


# ============================================================
#  إعادة التوجيه / التسجيل في التطبيق
# ============================================================

def setup_admin_routes(app: web.Application):
    """تسجيل مسارات لوحة التحكم في التطبيق الرئيسي"""
    try:
        app.router.add_post("/api/admin/login", handle_login)
        app.router.add_post("/api/admin/verify-otp", handle_verify_otp)
        app.router.add_post("/api/admin/change-passcode", handle_change_passcode)
        app.router.add_post("/api/admin/logout", handle_logout)
        app.router.add_get("/api/admin/offers", handle_get_offers)
        app.router.add_post("/api/admin/offers", handle_save_offer)
        app.router.add_put("/api/admin/offers/{id}/verified", handle_toggle_verified)
        app.router.add_delete("/api/admin/offers/{id}", handle_delete_offer)

        app.router.add_get("/api/admin/pending", handle_get_pending)
        app.router.add_post("/api/admin/pending/approve", handle_approve_pending)
        app.router.add_post("/api/admin/pending/reject", handle_reject_pending)

        app.router.add_get("/api/admin/managers", handle_managers)
        app.router.add_post("/api/admin/managers", handle_managers)
        app.router.add_delete("/api/admin/managers", handle_managers)

        app.router.add_get("/api/admin/ads", handle_ads)
        app.router.add_post("/api/admin/ads", handle_ads)

        app.router.add_get("/api/admin/schedule", handle_schedule)
        app.router.add_post("/api/admin/schedule", handle_schedule)

        app.router.add_get("/api/admin/templates", handle_templates)
        app.router.add_post("/api/admin/templates", handle_templates)

        app.router.add_get("/api/admin/stats", handle_stats)
        app.router.add_post("/api/admin/refresh", handle_refresh)
        app.router.add_get("/api/admin/export/csv", handle_export_csv)

        logger.info("✅ Admin API routes successfully setup.")
    except Exception as e:
        logger.error(f"Error setting up admin routes: {e}")
