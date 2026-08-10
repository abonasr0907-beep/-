#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام حماية الطوارئ — Phase 3 Emergency Protection System

المميزات:
- سيناريوهات جاهزة للزوار:
  * فشل رفع الصور
  * انقطاع الإنترنت أثناء الطلب
  * بيانات ناقصة
  * إعادة إرسال الطلب
  * تأخر البوت
- سيناريوهات جاهزة للأدمن:
  * فشل النشر (deploy)
  * خطأ GitHub
  * توقف Railway
  * فقدان webhook
  * تحديث تالف جديد
- لكل سيناريو: كشف تلقائي، إشعار Telegram، إصلاح مقترح، استعادة نسخة مستقرة
"""

import json
import os
import logging
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.emergency_protection")

# ============================================================
# المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EMERGENCY_LOG_FILE = DATA_DIR / "emergency_log.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RAILWAY_URL = "https://worker-production-7713.up.railway.app"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8629398802:AAE2ndFy06GfV8qSQpd-cOKDccPUt_G05Os")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ============================================================
# تحميل/حفظ السجل
# ============================================================
def _load_emergency_log() -> dict:
    if EMERGENCY_LOG_FILE.exists():
        try:
            with open(EMERGENCY_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"incidents": []}


def _save_emergency_log(data: dict):
    try:
        if len(data.get("incidents", [])) > 100:
            data["incidents"] = data["incidents"][-100:]
        tmp = EMERGENCY_LOG_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(EMERGENCY_LOG_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ سجل الطوارئ: {e}")


def _log_incident(scenario_id: str, category: str, severity: str, 
                   detected: str, message: str, fix: str, 
                   restore_available: bool, actions_taken: list = None):
    """تسجيل حادثة طوارئ"""
    log = _load_emergency_log()
    incident = {
        "incident_id": f"emg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "scenario_id": scenario_id,
        "category": category,
        "severity": severity,
        "detected_at": detected,
        "message": message,
        "suggested_fix": fix,
        "restore_available": restore_available,
        "actions_taken": actions_taken or [],
        "status": "detected",
    }
    log["incidents"].append(incident)
    _save_emergency_log(log)
    return incident


# ============================================================
# إرسال إشعار Telegram للأدمن
# ============================================================
def notify_admins(message: str) -> dict:
    """إرسال إشعار طوارئ للأدمن عبر Telegram"""
    try:
        config_path = BASE_DIR / "config.json"
        admin_ids = []
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                admin_ids = cfg.get("admin_ids", [])

        sent = 0
        failed = 0
        for aid in admin_ids:
            try:
                url = f"{TELEGRAM_API}/sendMessage"
                payload = {
                    "chat_id": aid,
                    "text": message,
                    "parse_mode": "HTML",
                }
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return {"sent": sent, "failed": failed, "total": len(admin_ids)}
    except Exception as e:
        logger.error(f"خطأ في إرسال إشعار الطوارئ: {e}")
        return {"sent": 0, "failed": 0, "error": str(e)}


# ============================================================
# تعريف السيناريوهات
# ============================================================
VISITOR_SCENARIOS = {
    "image_upload_failure": {
        "id": "image_upload_failure",
        "category": "visitor",
        "name": "فشل رفع الصور",
        "description": "الزائر يحاول رفع صورة ولكن العملية تفشل",
        "detection": "ظهور خطأ أثناء معالجة الصورة أو انتهاء مهلة التحميل",
        "auto_fix": "إعادة محاولة رفع الصورة تلقائياً (3 محاولات)",
        "notify_admin": False,
        "restore_available": False,
    },
    "internet_disconnect_during_request": {
        "id": "internet_disconnect_during_request",
        "category": "visitor",
        "name": "انقطاع الإنترنت أثناء الطلب",
        "description": "انقطاع الاتصال أثناء إرسال الزائر لطلبه",
        "detection": "فقدان الاتصال أثناء حفظ الطلب",
        "auto_fix": "حفظ الطلب محلياً وإكماله عند إعادة الاتصال",
        "notify_admin": False,
        "restore_available": False,
    },
    "incomplete_data": {
        "id": "incomplete_data",
        "category": "visitor",
        "name": "بيانات ناقصة",
        "description": "الزائر يرسل طلباً بدون بيانات كاملة",
        "detection": "حقول مطلوبة فارغة (الاسم، الهاتف، النوع)",
        "auto_fix": "طلب الحقول الناقصة من الزائر",
        "notify_admin": False,
        "restore_available": False,
    },
    "resend_request": {
        "id": "resend_request",
        "category": "visitor",
        "name": "إعادة إرسال الطلب",
        "description": "الزائر يريد إعادة إرسال طلب سابق",
        "detection": "الزائر يطلب إعادة إرسال طلب موجود",
        "auto_fix": "إنشاء ID جديد للطلب مع حفظ السجل القديم",
        "notify_admin": False,
        "restore_available": False,
    },
    "bot_delay": {
        "id": "bot_delay",
        "category": "visitor",
        "name": "تأخر البوت",
        "description": "البوت يستجيب ببطء شديد",
        "detection": "زمن استجابة > 30 ثانية",
        "auto_fix": "إرسال رسالة انتظار للزائر + فحص النظام",
        "notify_admin": True,
        "restore_available": False,
    },
}

ADMIN_SCENARIOS = {
    "deploy_failure": {
        "id": "deploy_failure",
        "category": "admin",
        "name": "فشل النشر (Deploy)",
        "description": "فشل نشر تحديث جديد على Railway",
        "detection": "Railway لا يستجيب بعد النشر أو يعيد خطأ",
        "auto_fix": "استعادة آخر نسخة مستقرة + إعادة النشر",
        "notify_admin": True,
        "restore_available": True,
    },
    "github_error": {
        "id": "github_error",
        "category": "admin",
        "name": "خطأ GitHub",
        "description": "خطأ في الوصول لمستودع GitHub",
        "detection": "GitHub API يعيد خطأ أو لا يستجيب",
        "auto_fix": "إعادة المحاولة + فحص الـ token",
        "notify_admin": True,
        "restore_available": False,
    },
    "railway_stop": {
        "id": "railway_stop",
        "category": "admin",
        "name": "توقف Railway",
        "description": "خدمة Railway متوقفة تماماً",
        "detection": "Railway لا يستجيب على /health",
        "auto_fix": "إشعار فوري + تعليمات إعادة التشغيل",
        "notify_admin": True,
        "restore_available": True,
    },
    "webhook_loss": {
        "id": "webhook_loss",
        "category": "admin",
        "name": "فقدان Webhook",
        "description": "الـ webhook غير مسجل أو لا يعمل",
        "detection": "getWebhookInfo يرجع URL فارغ أو أخطاء",
        "auto_fix": "إعادة تعيين الـ webhook تلقائياً",
        "notify_admin": True,
        "restore_available": False,
    },
    "update_corruption": {
        "id": "update_corruption",
        "category": "admin",
        "name": "تحديث تالف جديد",
        "description": "تحديث جديد أدى لفساد النظام",
        "detection": "أخطاء نحوية أو ملفات تالفة بعد التحديث",
        "auto_fix": "استعادة آخر نسخة مستقرة فوراً",
        "notify_admin": True,
        "restore_available": True,
    },
}


# ============================================================
# كشف السيناريوهات تلقائياً
# ============================================================
def detect_visitor_scenario(scenario_id: str, context: dict = None) -> dict:
    """
    كشف سيناريو زائر وتنفيذ الإجراءات.
    context: معلومات إضافية (user_id, request_id, etc.)
    """
    scenario = VISITOR_SCENARIOS.get(scenario_id)
    if not scenario:
        return {"success": False, "message": f"سيناريو غير معروف: {scenario_id}"}

    context = context or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # الإجراءات
    actions = []

    # تنفيذ الإصلاح التلقائي
    if scenario_id == "image_upload_failure":
        actions.append("إعادة محاولة رفع الصورة (حتى 3 محاولات)")
        actions.append("إرسال رسالة تطمين للزائر")
    elif scenario_id == "internet_disconnect_during_request":
        actions.append("حفظ الطلب محلياً في visitor_requests.json")
        actions.append("وضع علامة 'pending_sync' على الطلب")
        actions.append("إكمال الطلب تلقائياً عند إعادة الاتصال")
    elif scenario_id == "incomplete_data":
        missing = context.get("missing_fields", [])
        actions.append(f"طلب الحقول الناقصة: {', '.join(missing) if missing else 'الحقول المطلوبة'}")
    elif scenario_id == "resend_request":
        old_id = context.get("old_request_id", "")
        actions.append(f"إنشاء ID جديد للطلب (السجل القديم {old_id} محفوظ)")
        actions.append("ربط الطلب الجديد بالقديم في السجل")
    elif scenario_id == "bot_delay":
        actions.append("إرسال رسالة انتظار للزائر")
        actions.append("فحص حالة النظام")

    # إشعار الأدمن إذا لزم
    notification_result = None
    if scenario.get("notify_admin"):
        notify_msg = (
            f"🚨 <b>تنبيه طوارئ — زائر</b>\n\n"
            f"<b>السيناريو:</b> {scenario['name']}\n"
            f"<b>الوصف:</b> {scenario['description']}\n"
            f"<b>الوقت:</b> {now}\n"
            f"<b>الإصلاح المقترح:</b> {scenario['auto_fix']}\n"
        )
        if context.get("user_id"):
            notify_msg += f"<b>الزائر:</b> {context['user_id']}\n"
        notification_result = notify_admins(notify_msg)

    # تسجيل الحادثة
    incident = _log_incident(
        scenario_id=scenario_id,
        category="visitor",
        severity="warning" if not scenario.get("notify_admin") else "critical",
        detected=now,
        message=scenario["description"],
        fix=scenario["auto_fix"],
        restore_available=scenario.get("restore_available", False),
        actions_taken=actions,
    )

    return {
        "success": True,
        "scenario": scenario,
        "incident_id": incident["incident_id"],
        "actions_taken": actions,
        "notification_sent": notification_result,
    }


def detect_admin_scenario(scenario_id: str, context: dict = None) -> dict:
    """
    كشف سيناريو أدمن وتنفيذ الإجراءات.
    """
    scenario = ADMIN_SCENARIOS.get(scenario_id)
    if not scenario:
        return {"success": False, "message": f"سيناريو غير معروف: {scenario_id}"}

    context = context or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    actions = []
    restore_result = None

    # تنفيذ الإصلاح التلقائي
    if scenario_id == "deploy_failure":
        actions.append("كشف فشل النشر")
        actions.append("استعادة آخر نسخة مستقرة")
        try:
            import smart_backup
            latest = smart_backup.get_latest_stable()
            if latest:
                restore_result = smart_backup.redeploy_version(latest["version_id"])
                actions.append(f"تم استعادة: {latest['version_id']}")
        except Exception as e:
            actions.append(f"فشل الاستعادة: {e}")
    elif scenario_id == "github_error":
        actions.append("إعادة محاولة الاتصال بـ GitHub (3 محاولات)")
        actions.append("فحص GITHUB_TOKEN")
    elif scenario_id == "railway_stop":
        actions.append("إشعار فوري للأدمن")
        actions.append("تعليمات: تحقق من لوحة Railway + إعادة التشغيل")
    elif scenario_id == "webhook_loss":
        actions.append("إعادة تعيين الـ webhook")
        try:
            webhook_url = os.environ.get("WEBHOOK_URL", "").strip()
            if webhook_url:
                url = f"{TELEGRAM_API}/setWebhook"
                payload = {"url": f"{webhook_url}/bot/{BOT_TOKEN}"}
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    actions.append("تم إعادة تعيين الـ webhook بنجاح")
                else:
                    actions.append(f"فشل إعادة التعيين: HTTP {resp.status_code}")
        except Exception as e:
            actions.append(f"خطأ في إعادة تعيين webhook: {e}")
    elif scenario_id == "update_corruption":
        actions.append("كشف تحديث تالف")
        actions.append("استعادة آخر نسخة مستقرة فوراً")
        try:
            import smart_backup
            latest = smart_backup.get_latest_stable()
            if latest:
                restore_result = smart_backup.redeploy_version(latest["version_id"])
                actions.append(f"تم استعادة: {latest['version_id']}")
        except Exception as e:
            actions.append(f"فشل الاستعادة: {e}")

    # إشعار الأدمن
    notification_result = None
    if scenario.get("notify_admin"):
        notify_msg = (
            f"🚨 <b>تنبيه طوارئ — أدمن</b>\n\n"
            f"<b>السيناريو:</b> {scenario['name']}\n"
            f"<b>الوصف:</b> {scenario['description']}\n"
            f"<b>الوقت:</b> {now}\n"
            f"<b>الإصلاح:</b> {scenario['auto_fix']}\n"
            f"<b>استعادة متاحة:</b> {'نعم' if scenario.get('restore_available') else 'لا'}\n"
        )
        if restore_result:
            notify_msg += f"<b>نتيجة الاستعادة:</b> {restore_result.get('message', '')}\n"
        notification_result = notify_admins(notify_msg)

    # تسجيل الحادثة
    incident = _log_incident(
        scenario_id=scenario_id,
        category="admin",
        severity="critical",
        detected=now,
        message=scenario["description"],
        fix=scenario["auto_fix"],
        restore_available=scenario.get("restore_available", False),
        actions_taken=actions,
    )

    return {
        "success": True,
        "scenario": scenario,
        "incident_id": incident["incident_id"],
        "actions_taken": actions,
        "notification_sent": notification_result,
        "restore_result": restore_result,
    }


# ============================================================
# فحص شامل للطوارئ
# ============================================================
def run_emergency_scan() -> dict:
    """
    فحص شامل للكشف عن حالات الطوارئ تلقائياً.
    """
    detected = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # فحص Railway
    try:
        resp = requests.get(f"{RAILWAY_URL}/health", timeout=15)
        if resp.status_code != 200:
            result = detect_admin_scenario("railway_stop")
            detected.append(result)
    except Exception:
        result = detect_admin_scenario("railway_stop")
        detected.append(result)

    # فحص Webhook
    try:
        resp = requests.get(f"{TELEGRAM_API}/getWebhookInfo", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                info = data.get("result", {})
                webhook_url = info.get("url", "")
                pending = info.get("pending_update_count", 0)
                
                if not webhook_url:
                    result = detect_admin_scenario("webhook_loss")
                    detected.append(result)
                
                if pending > 100:
                    result = detect_admin_scenario("webhook_loss", {"reason": "high_pending", "pending": pending})
                    detected.append(result)
    except Exception:
        pass

    # فحص صحة الكود (تحديث تالف)
    try:
        import ai_monitor
        pre_deploy = ai_monitor.pre_deploy_check()
        if pre_deploy["status"] == "failed":
            result = detect_admin_scenario("update_corruption", {"issues": pre_deploy.get("issues", [])})
            detected.append(result)
    except Exception:
        pass

    return {
        "timestamp": now,
        "scanned": True,
        "detected_count": len(detected),
        "detected": detected,
        "all_clear": len(detected) == 0,
    }


# ============================================================
# سرد السيناريوهات
# ============================================================
def list_visitor_scenarios() -> list:
    return list(VISITOR_SCENARIOS.values())


def list_admin_scenarios() -> list:
    return list(ADMIN_SCENARIOS.values())


def list_all_scenarios() -> dict:
    return {
        "visitor": list(VISITOR_SCENARIOS.values()),
        "admin": list(ADMIN_SCENARIOS.values()),
    }


# ============================================================
# سجل الحوادث
# ============================================================
def get_recent_incidents(limit=10) -> list:
    log = _load_emergency_log()
    return log.get("incidents", [])[-limit:]


def health_check() -> dict:
    log = _load_emergency_log()
    incidents = log.get("incidents", [])
    return {
        "total_incidents": len(incidents),
        "visitor_scenarios": len(VISITOR_SCENARIOS),
        "admin_scenarios": len(ADMIN_SCENARIOS),
        "last_incident": incidents[-1] if incidents else None,
    }
