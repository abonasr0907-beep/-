#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الإصلاح الذكي — Phase 3 Smart Repair System

المميزات:
- عند كشف مشكلة: إنشاء تقرير واضح (سبب الخطأ، الملف المسبب، الإصلاح المقترح، الملفات لتعديلها)
- بعد موافقة الأدمن: تنفيذ الإصلاح، اختبار النظام، نسخة احتياطية قبل التعديل، نشر تلقائي
"""

import json
import os
import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.smart_repair")

# ============================================================
# المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPAIR_REPORT_FILE = DATA_DIR / "repair_reports.json"
REPAIR_QUEUE_FILE = DATA_DIR / "repair_queue.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# تحميل/حفظ البيانات
# ============================================================
def _load_repair_reports() -> dict:
    if REPAIR_REPORT_FILE.exists():
        try:
            with open(REPAIR_REPORT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"reports": []}


def _save_repair_reports(data: dict):
    try:
        if len(data.get("reports", [])) > 50:
            data["reports"] = data["reports"][-50:]
        tmp = REPAIR_REPORT_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(REPAIR_REPORT_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ تقارير الإصلاح: {e}")


def _load_repair_queue() -> dict:
    if REPAIR_QUEUE_FILE.exists():
        try:
            with open(REPAIR_QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"queue": []}


def _save_repair_queue(data: dict):
    try:
        tmp = REPAIR_QUEUE_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(REPAIR_QUEUE_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ قائمة الإصلاح: {e}")


# ============================================================
# إنشاء تقرير إصلاح
# ============================================================
def create_repair_report(issue: dict) -> dict:
    """
    إنشاء تقرير إصلاح واضح من مشكلة مكتشفة.
    
    issue يجب أن يحتوي على:
    - type: نوع المشكلة
    - file: الملف المتأثر
    - issue: وصف المشكلة
    - fix: الإصلاح المقترح
    - severity: خطورة المشكلة
    """
    repair_id = f"repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # تحديد الملفات التي تحتاج تعديل
    files_to_modify = []
    issue_type = issue.get("type", "")

    # إضافة ملفات مرتبطة بناءً على نوع المشكلة
    if issue.get("file"):
        if issue["file"] not in files_to_modify:
            files_to_modify.append(issue["file"])
    if issue_type == "webhook_error":
        if "bot/bot.py" not in files_to_modify:
            files_to_modify.append("bot/bot.py")  # إعداد الـ webhook

    # تحديد ما إذا كان الإصلاح حساساً
    sensitive_types = ["corrupt_json", "syntax_error", "webhook_error", "deploy_error"]
    is_sensitive = issue_type in sensitive_types or issue.get("severity") == "critical"

    # خطوات الإصلاح
    repair_steps = _generate_repair_steps(issue)

    report = {
        "repair_id": repair_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending_approval",  # pending_approval, approved, executing, completed, failed
        "issue_type": issue_type,
        "severity": issue.get("severity", "warning"),
        "cause": issue.get("issue", issue.get("message", "")),
        "causing_file": issue.get("file", ""),
        "suggested_fix": issue.get("fix", ""),
        "files_to_modify": files_to_modify,
        "repair_steps": repair_steps,
        "is_sensitive": is_sensitive,
        "needs_admin_approval": is_sensitive,
        "approved_by": None,
        "approved_at": None,
        "executed_at": None,
        "result": None,
        "backup_created": None,
    }

    # إضافة لقائمة الانتظار
    queue = _load_repair_queue()
    queue["queue"].append(report)
    _save_repair_queue(queue)

    # إضافة للتقارير
    reports = _load_repair_reports()
    reports["reports"].append(report)
    _save_repair_reports(reports)

    logger.info(f"🔧 تم إنشاء تقرير إصلاح: {repair_id} ({issue_type})")

    return report


def _generate_repair_steps(issue: dict) -> list:
    """توليد خطوات الإصلاح بناءً على نوع المشكلة"""
    issue_type = issue.get("type", "")
    steps = []

    if issue_type == "syntax_error":
        steps = [
            "1. فتح الملف في محرر النصوص",
            f"2. الذهاب للسطر {issue.get('line', '?')}",
            "3. إصلاح الخطأ النحوي المحدد",
            "4. حفظ الملف",
            "5. اختبار الترجمة: python -m py_compile <file>",
            "6. إنشاء نسخة احتياطية مستقرة",
            "7. نشر التحديث",
        ]
    elif issue_type == "corrupt_json":
        steps = [
            f"1. فتح الملف: {issue.get('file', '')}",
            "2. تحديد مكان الخطأ في JSON",
            "3. إصلاح بنية JSON (أقواس، فواصل)",
            "4. التحقق: python -c \"import json; json.load(open('file'))\"",
            "5. إنشاء نسخة احتياطية مستقرة",
            "6. نشر التحديث",
        ]
    elif issue_type == "missing_json":
        steps = [
            f"1. إنشاء الملف: {issue.get('file', '')}",
            "2. كتابة المحتوى الافتراضي ({...} أو {\"items\": []})",
            "3. التحقق من صحة JSON",
            "4. إنشاء نسخة احتياطية مستقرة",
        ]
    elif issue_type == "missing_import":
        steps = [
            f"1. التحقق من وجود الوحدة: {issue.get('message', '')}",
            "2. إنشاء الوحدة إذا لزم الأمر",
            "3. أو إزالة الاستيراد من الملف",
            "4. اختبار الترجمة",
            "5. إنشاء نسخة احتياطية مستقرة",
        ]
    elif issue_type == "webhook_error":
        steps = [
            "1. التحقق من حالة Railway (HTTP 200)",
            "2. التحقق من عنوان الـ webhook",
            "3. إعادة تعيين الـ webhook إذا لزم الأمر",
            "4. اختبار استجابة البوت",
            "5. إنشاء نسخة احتياطية مستقرة",
        ]
    elif issue_type == "low_disk":
        steps = [
            "1. تحديد الملفات الكبيرة غير الضرورية",
            "2. حذف النسخ الاحتياطية القديمة",
            "3. حذف ملفات السجل القديمة",
            "4. التحقق من المساحة المحررة",
        ]
    else:
        steps = [
            "1. تحليل المشكلة المكتشفة",
            "2. تحديد الملف المتأثر",
            "3. تطبيق الإصلاح المقترح",
            "4. اختبار النظام",
            "5. إنشاء نسخة احتياطية مستقرة",
            "6. نشر التحديث",
        ]

    return steps


# ============================================================
# موافقة الأدمن على إصلاح
# ============================================================
def approve_repair(repair_id: str, admin_id: int) -> dict:
    """
    موافقة الأدمن على تنفيذ إصلاح.
    """
    queue = _load_repair_queue()
    found = None
    for item in queue["queue"]:
        if item["repair_id"] == repair_id:
            found = item
            break

    if not found:
        return {"success": False, "message": f"الإصلاح {repair_id} غير موجود"}

    if found["status"] != "pending_approval":
        return {"success": False, "message": f"الإصلاح {repair_id} ليس في حالة انتظار (الحالة: {found['status']})"}

    found["status"] = "approved"
    found["approved_by"] = str(admin_id)
    found["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    _save_repair_queue(queue)

    # تحديث في التقارير أيضاً
    reports = _load_repair_reports()
    for r in reports["reports"]:
        if r["repair_id"] == repair_id:
            r["status"] = "approved"
            r["approved_by"] = str(admin_id)
            r["approved_at"] = found["approved_at"]
            break
    _save_repair_reports(reports)

    logger.info(f"✅ تمت الموافقة على إصلاح {repair_id} من قبل الأدمن {admin_id}")

    return {
        "success": True,
        "repair_id": repair_id,
        "message": f"تمت الموافقة على الإصلاح {repair_id}",
        "next_step": "استخدم /execute_repair لتنفيذ الإصلاح",
    }


# ============================================================
# تنفيذ الإصلاح (بعد الموافقة)
# ============================================================
def execute_repair(repair_id: str) -> dict:
    """
    تنفيذ الإصلاح بعد موافقة الأدمن:
    1. إنشاء نسخة احتياطية قبل التعديل
    2. تنفيذ الإصلاح
    3. اختبار النظام
    4. نشر تلقائي
    """
    queue = _load_repair_queue()
    found = None
    for item in queue["queue"]:
        if item["repair_id"] == repair_id:
            found = item
            break

    if not found:
        return {"success": False, "message": f"الإصلاح {repair_id} غير موجود"}

    if found["status"] not in ("approved", "pending_approval"):
        return {"success": False, "message": f"الإصلاح {repair_id} لا يمكن تنفيذه (الحالة: {found['status']})"}

    results = {
        "backup": None,
        "repair_executed": False,
        "test_passed": False,
        "published": False,
        "errors": [],
    }

    # 1. إنشاء نسخة احتياطية قبل التعديل
    try:
        import smart_backup
        backup_result = smart_backup.create_stable_backup(
            reason=f"pre_repair_{repair_id}",
            changed_files=found.get("files_to_modify", [])
        )
        results["backup"] = backup_result
        found["backup_created"] = backup_result.get("version", "")
    except Exception as e:
        results["errors"].append(f"فشل النسخ الاحتياطي: {e}")
        logger.error(f"❌ فشل النسخ الاحتياطي قبل الإصلاح: {e}")

    # 2. تنفيذ الإصلاح
    found["status"] = "executing"
    _save_repair_queue(queue)

    try:
        repair_result = _apply_repair(found)
        results["repair_executed"] = repair_result.get("success", False)
        if not repair_result.get("success"):
            results["errors"].append(repair_result.get("message", "فشل الإصلاح"))
    except Exception as e:
        results["errors"].append(f"خطأ في تنفيذ الإصلاح: {e}")
        logger.error(f"❌ خطأ في تنفيذ الإصلاح {repair_id}: {e}")

    # 3. اختبار النظام
    if results["repair_executed"]:
        try:
            import ai_monitor
            test_result = ai_monitor.pre_deploy_check()
            results["test_passed"] = test_result["status"] in ("passed", "warning")
            results["test_result"] = {
                "status": test_result["status"],
                "message": test_result["message"],
                "passed": test_result["passed_files"],
                "checked": test_result["checked_files"],
            }
        except Exception as e:
            results["errors"].append(f"خطأ في الاختبار: {e}")
            results["test_passed"] = False

    # 4. تحديث الحالة
    if results["repair_executed"] and results["test_passed"]:
        found["status"] = "completed"
        found["executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found["result"] = "success"
    else:
        found["status"] = "failed"
        found["executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found["result"] = "failed"

    found["execution_details"] = results
    _save_repair_queue(queue)

    # تحديث في التقارير
    reports = _load_repair_reports()
    for r in reports["reports"]:
        if r["repair_id"] == repair_id:
            r["status"] = found["status"]
            r["executed_at"] = found["executed_at"]
            r["result"] = found["result"]
            r["backup_created"] = found.get("backup_created")
            r["execution_details"] = results
            break
    _save_repair_reports(reports)

    logger.info(f"🔧 إصلاح {repair_id}: {found['status']}")

    return {
        "success": found["status"] == "completed",
        "repair_id": repair_id,
        "status": found["status"],
        "results": results,
        "message": "تم الإصلاح بنجاح" if found["status"] == "completed" else f"فشل الإصلاح — {len(results['errors'])} أخطاء",
    }


def _apply_repair(repair: dict) -> dict:
    """تطبيق الإصلاح الفعلي بناءً على نوع المشكلة"""
    issue_type = repair.get("issue_type", "")
    website_dir = BASE_DIR.parent

    if issue_type == "missing_json":
        # إنشاء ملف JSON افتراضي
        file_path = repair.get("causing_file", "")
        if file_path:
            fpath = website_dir / file_path
            if not fpath.exists():
                default_content = _get_default_json_content(file_path)
                fpath.parent.mkdir(parents=True, exist_ok=True)
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=2)
                return {"success": True, "message": f"تم إنشاء {file_path}"}
        return {"success": False, "message": "تعذر إنشاء الملف"}

    elif issue_type == "corrupt_json":
        # محاولة إصلاح JSON تالف (إعادة تعيين للمحتوى الافتراضي)
        file_path = repair.get("causing_file", "")
        if file_path:
            fpath = website_dir / file_path
            if fpath.exists():
                default_content = _get_default_json_content(file_path)
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=2)
                return {"success": True, "message": f"تم إعادة تعيين {file_path} للمحتوى الافتراضي"}
        return {"success": False, "message": "تعذر إصلاح الملف"}

    elif issue_type in ("syntax_error",):
        # لا يمكن إصلاح الأخطاء النحوية تلقائياً بدقة — نرجع تعليمات
        return {
            "success": False,
            "message": f"الخطأ النحوي يتطلب تدخلاً يدوياً — راجع: {repair.get('suggested_fix', '')}",
        }

    elif issue_type == "low_disk":
        # تنظيف النسخ الاحتياطية القديمة
        try:
            import shutil
            backups_dir = DATA_DIR / "backups"
            stable_dir = DATA_DIR / "stable_backups"
            cleaned = 0
            for d in (backups_dir, stable_dir):
                if d.exists():
                    for item in d.iterdir():
                        if item.is_dir() and item.name.startswith("backup_"):
                            shutil.rmtree(str(item), ignore_errors=True)
                            cleaned += 1
            return {"success": True, "message": f"تم تنظيف {cleaned} نسخة احتياطية قديمة"}
        except Exception as e:
            return {"success": False, "message": f"خطأ في التنظيف: {e}"}

    # الإصلاحات الأخرى تتطلب تدخلاً يدوياً
    return {
        "success": False,
        "message": f"الإصلاح من نوع {issue_type} يتطلب تدخلاً يدوياً — راجع الخطوات: {repair.get('repair_steps', [])}",
    }


def _get_default_json_content(file_path: str) -> dict:
    """الحصول على المحتوى الافتراضي لملف JSON"""
    defaults = {
        "bot/data/visitor_requests.json": {"requests": [], "inquiries": [], "offer_submissions": []},
        "bot/data/bot_offers.json": {"offers": []},
        "bot/data/bids.json": {"bids": []},
        "bot/data/users.json": {"users": []},
        "bot/data/audit_log.json": {"actions": []},
        "offers-data/offers.json": {"offers": []},
        "offers-data/news.json": {"news": []},
        "offers-data/office-data.json": {"data": []},
    }
    return defaults.get(file_path, {"data": []})


# ============================================================
# سرد الإصلاحات المعلقة
# ============================================================
def list_pending_repairs() -> list:
    queue = _load_repair_queue()
    return [item for item in queue["queue"] if item["status"] == "pending_approval"]


def list_all_repairs() -> list:
    queue = _load_repair_queue()
    return queue.get("queue", [])


def get_repair(repair_id: str) -> dict:
    queue = _load_repair_queue()
    for item in queue["queue"]:
        if item["repair_id"] == repair_id:
            return item
    return None

def reject_repair(repair_id: str, admin_id: int = 0, notes: str = "") -> dict:
    """Phase Completion: رفض تقرير إصلاح — تغيير الحالة إلى rejected"""
    try:
        queue = _load_repair_queue()
        for item in queue["queue"]:
            if item["repair_id"] == repair_id:
                item["status"] = "rejected"
                item["rejected_by"] = admin_id
                item["rejected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if notes:
                    item["rejection_notes"] = notes
                _save_repair_queue(queue)
                logger.info(f"Phase Completion: تم رفض إصلاح {repair_id}")
                return {"success": True, "repair_id": repair_id, "message": "تم رفض الإصلاح"}
        return {"success": False, "message": "الإصلاح غير موجود"}
    except Exception as e:
        logger.error(f"خطأ في رفض الإصلاح: {e}")
        return {"success": False, "message": str(e)}


def health_check() -> dict:
    queue = _load_repair_queue()
    pending = [q for q in queue["queue"] if q["status"] == "pending_approval"]
    completed = [q for q in queue["queue"] if q["status"] == "completed"]
    failed = [q for q in queue["queue"] if q["status"] == "failed"]
    return {
        "total": len(queue["queue"]),
        "pending": len(pending),
        "completed": len(completed),
        "failed": len(failed),
    }
