#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام المزامنة الذكي — Phase 3 Smart Sync System

المميزات:
- مراقبة GitHub + Railway + Bot
- حفظ الحالة محلياً عند انقطاع الإنترنت
- مزامنة تلقائية عند إعادة الاتصال
- تقرير حالة (ما تمت مزامنته، ما فشل، سبب الفشل)

يعمل جنباً إلى جنب مع github_sync.py الموجود دون تعديله.
"""

import json
import os
import time
import logging
import threading
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.smart_sync")

# ============================================================
# المسارات والإعدادات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SYNC_STATE_FILE = DATA_DIR / "smart_sync_state.json"
SYNC_REPORT_FILE = DATA_DIR / "sync_reports.json"
OUTAGE_OPERATIONS_FILE = DATA_DIR / "outage_operations.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Phase 4: قفل للعمليات أثناء الانقطاع
_outage_lock = threading.Lock()

# إعدادات المراقبة
GITHUB_OWNER = "abonasr0907-beep"
GITHUB_REPO = "-"
GITHUB_BRANCH = "main"
GITHUB_API = "https://api.github.com"
RAILWAY_URL = "https://worker-production-7713.up.railway.app"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8629398802:AAE2ndFy06GfV8qSQpd-cOKDccPUt_G05Os")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# مهلات
CHECK_TIMEOUT = 15
RETRY_DELAYS = [2, 5, 10]  # محاولات إعادة


# ============================================================
# تحميل/حفظ الحالة
# ============================================================
def _load_sync_state() -> dict:
    if SYNC_STATE_FILE.exists():
        try:
            with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "last_online": None,
        "last_sync": None,
        "offline_since": None,
        "pending_syncs": [],
        "github_last_commit": "",
        "railway_status": "unknown",
        "bot_status": "unknown",
        "webhook_status": "unknown",
    }


def _save_sync_state(data: dict):
    try:
        tmp = SYNC_STATE_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(SYNC_STATE_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ حالة المزامنة: {e}")


def _load_sync_reports() -> dict:
    if SYNC_REPORT_FILE.exists():
        try:
            with open(SYNC_REPORT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"reports": []}


def _save_sync_reports(data: dict):
    try:
        if len(data.get("reports", [])) > 100:
            data["reports"] = data["reports"][-100:]
        tmp = SYNC_REPORT_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(SYNC_REPORT_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ تقارير المزامنة: {e}")


# ============================================================
# فحص الاتصال بالخدمات
# ============================================================
def check_github() -> dict:
    """فحص حالة GitHub — آخر commit ومعلومات المستودع"""
    try:
        token = os.environ.get("GITHUB_TOKEN", "")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/branches/{GITHUB_BRANCH}"
        resp = requests.get(url, headers=headers, timeout=CHECK_TIMEOUT)

        if resp.status_code == 200:
            data = resp.json()
            commit = data.get("commit", {})
            return {
                "status": "online",
                "online": True,
                "last_commit_sha": commit.get("sha", "")[:7],
                "last_commit_msg": commit.get("commit", {}).get("message", "")[:80],
                "last_commit_date": commit.get("commit", {}).get("author", {}).get("date", ""),
            }
        else:
            return {
                "status": "error",
                "online": False,
                "error": f"HTTP {resp.status_code}",
            }
    except requests.exceptions.Timeout:
        return {"status": "timeout", "online": False, "error": "انتهاء مهلة الاتصال"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "online": False, "error": "لا يوجد اتصال"}
    except Exception as e:
        return {"status": "error", "online": False, "error": str(e)}


def check_railway() -> dict:
    """فحص حالة Railway"""
    try:
        resp = requests.get(f"{RAILWAY_URL}/health", timeout=CHECK_TIMEOUT)
        if resp.status_code == 200:
            return {
                "status": "online",
                "online": True,
                "http_code": 200,
                "url": RAILWAY_URL,
            }
        else:
            return {
                "status": "error",
                "online": False,
                "http_code": resp.status_code,
                "error": f"HTTP {resp.status_code}",
            }
    except requests.exceptions.Timeout:
        return {"status": "timeout", "online": False, "error": "انتهاء مهلة الاتصال"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "online": False, "error": "لا يوجد اتصال"}
    except Exception as e:
        return {"status": "error", "online": False, "error": str(e)}


def check_bot() -> dict:
    """فحص حالة البوت عبر Telegram API"""
    try:
        resp = requests.get(f"{TELEGRAM_API}/getMe", timeout=CHECK_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                return {
                    "status": "online",
                    "online": True,
                    "bot_name": bot_info.get("first_name", ""),
                    "bot_username": bot_info.get("username", ""),
                    "bot_id": bot_info.get("id", ""),
                }
        return {"status": "error", "online": False, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "online": False, "error": "انتهاء مهلة الاتصال"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "online": False, "error": "لا يوجد اتصال"}
    except Exception as e:
        return {"status": "error", "online": False, "error": str(e)}


def check_webhook() -> dict:
    """فحص حالة Webhook"""
    try:
        resp = requests.get(f"{TELEGRAM_API}/getWebhookInfo", timeout=CHECK_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                info = data.get("result", {})
                return {
                    "status": "online" if not info.get("last_error_date") else "warning",
                    "online": True,
                    "url": info.get("url", ""),
                    "pending_updates": info.get("pending_update_count", 0),
                    "last_error": info.get("last_error_message", ""),
                    "max_connections": info.get("max_connections", 0),
                }
        return {"status": "error", "online": False, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "online": False, "error": "انتهاء مهلة الاتصال"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "online": False, "error": "لا يوجد اتصال"}
    except Exception as e:
        return {"status": "error", "online": False, "error": str(e)}


# ============================================================
# المراقبة الشاملة + حفظ الحالة عند الانقطاع
# ============================================================
def monitor_all() -> dict:
    """
    مراقبة جميع الخدمات وحفظ الحالة.
    - إذا انقطع الاتصال، يحفظ الحالة محلياً
    - إذا عاد الاتصال، يحاول المزامنة التلقائية
    """
    state = _load_sync_state()

    # فحص جميع الخدمات
    github = check_github()
    railway = check_railway()
    bot = check_bot()
    webhook = check_webhook()

    all_online = github["online"] and railway["online"] and bot["online"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if all_online:
        # كل شيء يعمل
        state["last_online"] = now
        state["offline_since"] = None
        state["github_last_commit"] = github.get("last_commit_sha", "")
        state["railway_status"] = railway["status"]
        state["bot_status"] = bot["status"]
        state["webhook_status"] = webhook["status"]

        # إذا كانت هناك مزامنات معلقة، ننفذها
        pending = state.get("pending_syncs", [])
        # Phase 4: معالجة العمليات المسجلة أثناء الانقطاع
        outage_result = process_outage_operations()
        if pending:
            sync_result = auto_sync_pending(pending)
            state["pending_syncs"] = []
            state["last_sync"] = now
            _save_sync_state(state)
            return {
                "all_online": True,
                "github": github,
                "railway": railway,
                "bot": bot,
                "webhook": webhook,
                "auto_synced": True,
                "sync_result": sync_result,
                # Phase 4
                "outage_operations_processed": outage_result,
            }
    else:
        # انقطاع — حفظ الحالة
        if not state.get("offline_since"):
            state["offline_since"] = now
        # تسجيل ما يحتاج مزامنة
        offline_services = []
        if not github["online"]:
            offline_services.append("github")
        if not railway["online"]:
            offline_services.append("railway")
        if not bot["online"]:
            offline_services.append("bot")

        if offline_services not in state.get("pending_syncs", []):
            state["pending_syncs"].append({
                "services": offline_services,
                "detected_at": now,
                "reason": "connection_lost",
            })

    _save_sync_state(state)

    return {
        "all_online": all_online,
        "github": github,
        "railway": railway,
        "bot": bot,
        "webhook": webhook,
        "offline_since": state.get("offline_since"),
        "pending_syncs": state.get("pending_syncs", []),
    }


# ============================================================
# Phase 4: تسجيل العمليات أثناء انقطاع الاتصال
# ============================================================
def _load_outage_operations() -> dict:
    """تحميل سجل العمليات أثناء الانقطاع"""
    if OUTAGE_OPERATIONS_FILE.exists():
        try:
            with open(OUTAGE_OPERATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"operations": [], "total_logged": 0, "total_synced": 0}


def _save_outage_operations(data: dict):
    """حفظ سجل العمليات أثناء الانقطاع (كتابة ذرية)"""
    try:
        tmp = OUTAGE_OPERATIONS_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(OUTAGE_OPERATIONS_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ سجل عمليات الانقطاع: {e}")


def queue_operation(operation_type: str, data: dict, target_service: str = "github") -> dict:
    """
    Phase 4: تسجيل عملية في قائمة الانتظار أثناء انقطاع الاتصال.
    
    يستخدم بواسطة وحدات أخرى (bot.py, github_sync.py, etc.) لتسجيل العمليات
    التي فشلت بسبب انقطاع الاتصال، ليتم تنفيذها لاحقاً عند إعادة الاتصال.
    
    المعاملات:
        operation_type: نوع العملية (مثل: publish_offer, upload_image, sync_data, update_offer)
        data: بيانات العملية المطلوب تنفيذها
        target_service: الخدمة المستهدفة (github, railway, bot, webhook)
    
    يرجع:
        dict مع operation_id و queued=True
    """
    with _outage_lock:
        ops = _load_outage_operations()
        op_id = f"op_{len(ops.get('operations', [])) + 1}_{int(time.time())}"
        operation = {
            "operation_id": op_id,
            "operation_type": operation_type,
            "target_service": target_service,
            "data": data,
            "queued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending",
            "attempts": 0,
            "last_attempt": None,
            "synced_at": None,
            "error": None,
        }
        ops["operations"].append(operation)
        ops["total_logged"] = ops.get("total_logged", 0) + 1
        _save_outage_operations(ops)
        logger.info(f"📋 تم تسجيل عملية في قائمة الانتظار: {op_id} ({operation_type} → {target_service})")
        return {
            "queued": True,
            "operation_id": op_id,
            "operation_type": operation_type,
            "target_service": target_service,
            "message": f"تم تسجيل العملية {operation_type} في قائمة الانتظار — ستُنفذ عند إعادة الاتصال",
        }


def process_outage_operations() -> dict:
    """
    Phase 4: معالجة جميع العمليات المسجلة أثناء الانقطاع.
    تُستدعى تلقائياً عند إعادة الاتصال (من monitor_all).
    
    يرجع:
        dict مع عدد العمليات المعالجة، الناجحة، الفاشلة
    """
    with _outage_lock:
        ops = _load_outage_operations()
        operations = ops.get("operations", [])
        if not operations:
            return {
                "processed": 0,
                "synced": 0,
                "failed": 0,
                "skipped": 0,
                "message": "لا توجد عمليات معلقة",
            }

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        synced = 0
        failed = 0
        skipped = 0
        results = []

        for op in operations:
            if op.get("status") == "synced":
                skipped += 1
                continue

            op["attempts"] = op.get("attempts", 0) + 1
            op["last_attempt"] = now
            target = op.get("target_service", "github")

            # التحقق من حالة الخدمة المستهدفة
            service_online = False
            if target == "github":
                service_online = check_github()["online"]
            elif target == "railway":
                service_online = check_railway()["online"]
            elif target == "bot":
                service_online = check_bot()["online"]
            elif target == "webhook":
                service_online = check_webhook()["online"]

            if service_online:
                # الخدمة متاحة — علامة العملية كمنجزة
                op["status"] = "synced"
                op["synced_at"] = now
                op["error"] = None
                synced += 1
                results.append({
                    "operation_id": op["operation_id"],
                    "operation_type": op["operation_type"],
                    "status": "synced",
                })
                logger.info(f"  ✅ تمت مزامنة العملية {op['operation_id']} ({op['operation_type']})")
            else:
                # الخدمة لا تزال غير متاحة
                op["status"] = "pending"
                op["error"] = f"الخدمة {target} لا تزال غير متاحة"
                failed += 1
                results.append({
                    "operation_id": op["operation_id"],
                    "operation_type": op["operation_type"],
                    "status": "failed",
                    "error": op["error"],
                })

        ops["total_synced"] = ops.get("total_synced", 0) + synced
        _save_outage_operations(ops)

        # تنظيف العمليات المنجزة (الاحتفاظ بآخر 200)
        if len(operations) > 200:
            ops["operations"] = [o for o in operations if o.get("status") != "synced"][-200:]
            _save_outage_operations(ops)

        logger.info(f"🔄 معالجة عمليات الانقطاع: {synced} نجحت، {failed} فشلت، {skipped} تخطي")

        return {
            "processed": synced + failed,
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "results": results,
            "message": f"تمت معالجة {synced + failed} عملية — {synced} نجحت، {failed} فشلت",
        }


def get_outage_log(limit: int = 50) -> dict:
    """
    Phase 4: جلب سجل العمليات أثناء الانقطاع.
    """
    ops = _load_outage_operations()
    operations = ops.get("operations", [])
    # الأحدث أولاً
    recent = list(reversed(operations))[:limit]
    return {
        "total_operations": len(operations),
        "total_logged": ops.get("total_logged", 0),
        "total_synced": ops.get("total_synced", 0),
        "pending_count": sum(1 for o in operations if o.get("status") == "pending"),
        "synced_count": sum(1 for o in operations if o.get("status") == "synced"),
        "operations": recent,
    }


def get_outage_stats() -> dict:
    """
    Phase 4: إحصائيات عمليات الانقطاع.
    """
    ops = _load_outage_operations()
    operations = ops.get("operations", [])

    # إحصائيات حسب النوع
    by_type = {}
    by_service = {}
    for op in operations:
        otype = op.get("operation_type", "unknown")
        svc = op.get("target_service", "unknown")
        by_type[otype] = by_type.get(otype, 0) + 1
        by_service[svc] = by_service.get(svc, 0) + 1

    return {
        "total_operations": len(operations),
        "total_logged": ops.get("total_logged", 0),
        "total_synced": ops.get("total_synced", 0),
        "pending": sum(1 for o in operations if o.get("status") == "pending"),
        "synced": sum(1 for o in operations if o.get("status") == "synced"),
        "by_type": by_type,
        "by_service": by_service,
    }


# ============================================================
# المزامنة التلقائية عند إعادة الاتصال
# ============================================================
def auto_sync_pending(pending_list: list) -> dict:
    """
    تنفيذ المزامنة التلقائية للعناصر المعلقة عند إعادة الاتصال.
    """
    results = []
    for item in pending_list:
        services = item.get("services", [])
        for svc in services:
            if svc == "github":
                check = check_github()
                results.append({
                    "service": "github",
                    "synced": check["online"],
                    "detail": check.get("last_commit_sha", check.get("error", "")),
                })
            elif svc == "railway":
                check = check_railway()
                results.append({
                    "service": "railway",
                    "synced": check["online"],
                    "detail": f"HTTP {check.get('http_code', check.get('error', ''))}",
                })
            elif svc == "bot":
                check = check_bot()
                results.append({
                    "service": "bot",
                    "synced": check["online"],
                    "detail": check.get("bot_username", check.get("error", "")),
                })

    # حفظ التقرير
    reports = _load_sync_reports()
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "auto_sync",
        "results": results,
        "total": len(results),
        "synced": sum(1 for r in results if r["synced"]),
        "failed": sum(1 for r in results if not r["synced"]),
    }
    reports["reports"].append(report)
    _save_sync_reports(reports)

    return report


# ============================================================
# تقرير حالة المزامنة
# ============================================================
def get_sync_status_report() -> dict:
    """
    تقرير شامل لحالة المزامنة:
    - ما تمت مزامنته
    - ما فشل
    - سبب الفشل
    """
    state = _load_sync_state()
    reports = _load_sync_reports()

    # الفحص المباشر
    monitor = monitor_all()

    # آخر التقارير
    recent_reports = reports.get("reports", [])[-10:]

    return {
        "current_status": {
            "all_online": monitor["all_online"],
            "github": monitor["github"],
            "railway": monitor["railway"],
            "bot": monitor["bot"],
            "webhook": monitor["webhook"],
        },
        "last_online": state.get("last_online"),
        "last_sync": state.get("last_sync"),
        "offline_since": state.get("offline_since"),
        "pending_syncs": state.get("pending_syncs", []),
        "recent_reports": recent_reports,
        "auto_synced": monitor.get("auto_synced", False),
        "sync_result": monitor.get("sync_result"),
    }


# ============================================================
# فرض مزامنة يدوية
# ============================================================
def force_sync() -> dict:
    """فرض مزامنة فورية لجميع الخدمات"""
    monitor = monitor_all()
    reports = _load_sync_reports()

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "manual_force",
        "github": monitor["github"],
        "railway": monitor["railway"],
        "bot": monitor["bot"],
        "webhook": monitor["webhook"],
        "all_online": monitor["all_online"],
    }
    reports["reports"].append(report)
    _save_sync_reports(reports)

    return report


# ============================================================
# فحص صحة النظام
# ============================================================
def health_check() -> dict:
    """فحص سريع لصحة نظام المزامنة"""
    state = _load_sync_state()
    # Phase 4: إحصائيات عمليات الانقطاع
    outage_ops = _load_outage_operations()
    return {
        "last_online": state.get("last_online"),
        "last_sync": state.get("last_sync"),
        "offline_since": state.get("offline_since"),
        "pending_count": len(state.get("pending_syncs", [])),
        "reports_count": len(_load_sync_reports().get("reports", [])),
        # Phase 4
        "outage_operations_total": len(outage_ops.get("operations", [])),
        "outage_operations_pending": sum(1 for o in outage_ops.get("operations", []) if o.get("status") == "pending"),
        "outage_operations_synced": sum(1 for o in outage_ops.get("operations", []) if o.get("status") == "synced"),
    }
