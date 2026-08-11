#!/usr/bin/env python3
"""
Phase 4 — نظام الإبلاغ عن الأخطاء الموحد
Error Reporting System — Unified interface to smart_repair.py + ai_monitor.py

أي مشكلة أثناء التنفيذ → smart_repair.py + AI Monitor مع تقرير نجاح/فشل.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# مسارات الملفات
BASE_DIR = Path(__file__).resolve().parent
ERROR_LOG_FILE = BASE_DIR / "error_reports.json"

# استيراد آمن للوحدات
try:
    import smart_repair
    SMART_REPAIR_AVAILABLE = True
except Exception as e:
    SMART_REPAIR_AVAILABLE = False
    logger.warning(f"smart_repair غير متاح: {e}")

try:
    import ai_monitor
    AI_MONITOR_AVAILABLE = True
except Exception as e:
    AI_MONITOR_AVAILABLE = False
    logger.warning(f"ai_monitor غير متاح: {e}")


def _load_error_log():
    """تحميل سجل الأخطاء المحلي"""
    try:
        if ERROR_LOG_FILE.exists():
            with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {"reports": []}


def _save_error_log(data):
    """حفظ سجل الأخطاء المحلي"""
    try:
        if len(data.get("reports", [])) > 100:
            data["reports"] = data["reports"][-100:]
        tmp = ERROR_LOG_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(ERROR_LOG_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ سجل الأخطاء: {e}")


def report_error(
    source: str,
    error: Exception or str,
    context: dict = None,
    severity: str = "warning",
    file_affected: str = "",
    suggested_fix: str = "",
    auto_report: bool = True,
) -> dict:
    """
    الإبلاغ عن خطأ إلى smart_repair + AI Monitor + سجل محلي.

    المعاملات:
        source: مصدر الخطأ (مثال: "bot._approve_visitor_request", "visitor_api.handle_request")
        error: كائن الاستثناء أو نص الخطأ
        context: سياق إضافي (dict)
        severity: خطورة الخطأ (critical, error, warning, info)
        file_affected: الملف المتأثر
        suggested_fix: الإصلاح المقترح
        auto_report: إذا True، يرسل تلقائياً إلى smart_repair + ai_monitor

    الإرجاع:
        dict يحتوي على:
        - success: True/False
        - repair_report: تقرير smart_repair (أو None)
        - monitor_report: تقرير ai_monitor (أو None)
        - error_id: معرف الخطأ
        - message: رسالة الحالة
    """
    error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # استخراج نص الخطأ وتتبع المكدس
    if isinstance(error, Exception):
        error_message = str(error)
        error_traceback = traceback.format_exc()
        error_type = type(error).__name__
    else:
        error_message = str(error)
        error_traceback = ""
        error_type = "GenericError"

    # بناء تقرير الخطأ
    error_report = {
        "error_id": error_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "error_type": error_type,
        "message": error_message,
        "traceback": error_traceback,
        "context": context or {},
        "severity": severity,
        "file_affected": file_affected,
        "suggested_fix": suggested_fix,
        "smart_repair_reported": False,
        "ai_monitor_reported": False,
    }

    result = {
        "success": True,
        "error_id": error_id,
        "repair_report": None,
        "monitor_report": None,
        "message": "",
    }

    # 1) الإبلاغ إلى smart_repair
    if auto_report and SMART_REPAIR_AVAILABLE:
        try:
            issue = {
                "type": error_type.lower().replace("error", "_error") if "error" not in error_type.lower() else error_type.lower(),
                "file": file_affected,
                "issue": f"[{source}] {error_message}",
                "fix": suggested_fix or "مراجعة يدوية مطلوبة",
                "severity": severity,
            }
            repair_report = smart_repair.create_repair_report(issue)
            error_report["smart_repair_reported"] = True
            error_report["repair_id"] = repair_report.get("repair_id", "")
            result["repair_report"] = repair_report
            result["message"] += "smart_repair: OK. "
            logger.info(f"Phase4: خطأ مبلغ إلى smart_repair: {repair_report.get('repair_id')}")
        except Exception as e:
            result["success"] = False
            result["message"] += f"smart_repair: فشل ({e}). "
            logger.error(f"Phase4: فشل الإبلاغ إلى smart_repair: {e}")

    # 2) الإبلاغ إلى AI Monitor
    if auto_report and AI_MONITOR_AVAILABLE:
        try:
            monitor_data = ai_monitor._load_reports()
            monitor_entry = {
                "timestamp": error_report["timestamp"],
                "type": "runtime_error",
                "source": source,
                "severity": severity,
                "error_type": error_type,
                "message": error_message,
                "file": file_affected,
                "context": context or {},
                "suggested_fix": suggested_fix,
                "traceback": error_traceback[:500] if error_traceback else "",
            }
            monitor_data["reports"].append(monitor_entry)
            ai_monitor._save_reports(monitor_data)
            error_report["ai_monitor_reported"] = True
            result["monitor_report"] = monitor_entry
            result["message"] += "ai_monitor: OK."
            logger.info(f"Phase4: خطأ مبلغ إلى ai_monitor")
        except Exception as e:
            result["success"] = False
            result["message"] += f"ai_monitor: فشل ({e})."
            logger.error(f"Phase4: فشل الإبلاغ إلى ai_monitor: {e}")

    # 3) حفظ في السجل المحلي (دائماً)
    try:
        log_data = _load_error_log()
        log_data["reports"].append(error_report)
        _save_error_log(log_data)
    except Exception as e:
        logger.error(f"Phase4: فشل حفظ سجل الأخطاء المحلي: {e}")

    # طباعة ملخص
    status = "نجاح" if result["success"] else "فشل جزئي"
    logger.info(f"Phase4 Error Report [{error_id}]: {status} — {result['message']}")

    return result


def report_success(
    source: str,
    action: str,
    details: dict = None,
) -> dict:
    """
    الإبلاغ عن نجاح عملية (لتتبع العمليات الناجحة أيضاً).

    المعاملات:
        source: مصدر العملية
        action: اسم العملية
        details: تفاصيل إضافية

    الإرجاع:
        dict يحتوي على success=True و report_id
    """
    success_id = f"ok_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    success_report = {
        "report_id": success_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "action": action,
        "status": "success",
        "details": details or {},
    }

    # حفظ في السجل المحلي
    try:
        log_data = _load_error_log()
        log_data["reports"].append(success_report)
        _save_error_log(log_data)
    except Exception as e:
        logger.error(f"Phase4: فشل حفظ تقرير النجاح: {e}")

    # الإبلاغ إلى AI Monitor كحدث إيجابي
    if AI_MONITOR_AVAILABLE:
        try:
            monitor_data = ai_monitor._load_reports()
            monitor_data["reports"].append({
                "timestamp": success_report["timestamp"],
                "type": "success_event",
                "source": source,
                "action": action,
                "details": details or {},
            })
            ai_monitor._save_reports(monitor_data)
        except Exception:
            pass

    logger.info(f"Phase4 Success Report [{success_id}]: {source} → {action}")
    return {"success": True, "report_id": success_id, "report": success_report}


def get_error_stats() -> dict:
    """
    الحصول على إحصائيات الأخطاء.
    """
    log_data = _load_error_log()
    reports = log_data.get("reports", [])

    total = len(reports)
    errors = sum(1 for r in reports if r.get("status") != "success" and "error_id" in r)
    successes = sum(1 for r in reports if r.get("status") == "success")
    critical = sum(1 for r in reports if r.get("severity") == "critical")

    return {
        "total_reports": total,
        "errors": errors,
        "successes": successes,
        "critical_errors": critical,
        "smart_repair_available": SMART_REPAIR_AVAILABLE,
        "ai_monitor_available": AI_MONITOR_AVAILABLE,
    }


# ============================================================
# سياق آمن للتشغيل — التقط الأخطاء تلقائياً
# ============================================================
class safe_operation:
    """
    سياق آمن لالتقاط الأخطاء تلقائياً والإبلاغ عنها.

    الاستخدام:
        with safe_operation("bot.process_request", context={"user_id": 123}) as op:
            # كود قد يفشل
            result = do_something()
            op.set_result(result)

        # op.success → True/False
        # op.error_report → تقرير الخطأ (أو None)
    """

    def __init__(self, source: str, context: dict = None, severity: str = "error",
                 file_affected: str = "", suggested_fix: str = "", auto_report: bool = True):
        self.source = source
        self.context = context
        self.severity = severity
        self.file_affected = file_affected
        self.suggested_fix = suggested_fix
        self.auto_report = auto_report
        self.success = False
        self.error = None
        self.error_report = None
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.success = False
            self.error = exc_val
            self.error_report = report_error(
                source=self.source,
                error=exc_val,
                context=self.context,
                severity=self.severity,
                file_affected=self.file_affected,
                suggested_fix=self.suggested_fix,
                auto_report=self.auto_report,
            )
            # منع رفع الاستثناء مرة أخرى (ت调味 بصمت)
            return True
        else:
            self.success = True
            report_success(
                source=self.source,
                action=self.context.get("action", "operation") if self.context else "operation",
                details=self.context,
            )
            return False

    def set_result(self, result):
        self.result = result
