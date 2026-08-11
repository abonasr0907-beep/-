#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام مراقبة الذكاء الاصطناعي — Phase 3 AI Monitoring System

المميزات:
- طبقة مراقبة الكود تفحص الأخطاء قبل النشر
- تحليل سجلات Railway
- اكتشاف المشاكل المتوقعة
- اقتراح إصلاحات (لا إصلاح حساس دون موافقة الأدمن)
"""

import json
import os
import re
import ast
import logging
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.ai_monitor")

# ============================================================
# المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MONITOR_REPORT_FILE = DATA_DIR / "ai_monitor_reports.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RAILWAY_URL = "https://worker-production-7713.up.railway.app"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8629398802:AAE2ndFy06GfV8qSQpd-cOKDccPUt_G05Os")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# الملفات المراد فحصها قبل النشر
PRE_DEPLOY_FILES = [
    "bot/bot.py",
    "bot/user_manager.py",
    "bot/smart_backup.py",
    "bot/smart_sync.py",
    "bot/ai_monitor.py",
    "bot/smart_repair.py",
    "bot/emergency_protection.py",
    "bot/backup.py",
    "bot/github_sync.py",
    "bot/persistence.py",
    "bot/task_queue.py",
    "bot/image_utils.py",
    "bot/offer_id.py",
    # Phase 4 AI Protection — new modules
    "bot/property_storage.py",
    "bot/publish_verifier.py",
]


# ============================================================
# تحميل/حفظ التقارير
# ============================================================
def _load_reports() -> dict:
    if MONITOR_REPORT_FILE.exists():
        try:
            with open(MONITOR_REPORT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"reports": []}


def _save_reports(data: dict):
    try:
        if len(data.get("reports", [])) > 50:
            data["reports"] = data["reports"][-50:]
        tmp = MONITOR_REPORT_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(MONITOR_REPORT_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ تقارير المراقبة: {e}")


# ============================================================
# فحص الكود قبل النشر (Pre-deployment Check)
# ============================================================
def pre_deploy_check() -> dict:
    """
    فحص جميع ملفات Python قبل النشر:
    - التحقق من الترجمة (compilation)
    - فحص الأخطاء النحوية (syntax)
    - فحص الاستيرادات (imports)
    - كشف المشاكل الشائعة
    """
    website_dir = BASE_DIR.parent
    issues = []
    checked = 0
    passed = 0

    for rel_path in PRE_DEPLOY_FILES:
        fpath = website_dir / rel_path
        if not fpath.exists():
            issues.append({
                "file": rel_path,
                "severity": "warning",
                "type": "missing_file",
                "message": f"الملف غير موجود: {rel_path}",
                "fix": "تأكد من أن الملف موجود قبل النشر",
            })
            continue

        checked += 1
        file_issues = _check_python_file(fpath, rel_path)
        
        if not file_issues:
            passed += 1
        else:
            issues.extend(file_issues)

    # تحديد الحالة العامة
    critical = [i for i in issues if i["severity"] == "critical"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    
    if critical:
        status = "failed"
        message = f"فشل الفحص — {len(critical)} مشكلة حرجة"
    elif warnings:
        status = "warning"
        message = f"تحذير — {len(warnings)} تحذير"
    else:
        status = "passed"
        message = f"نجح الفحص — {passed}/{checked} ملف سليم"

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "pre_deploy",
        "status": status,
        "message": message,
        "checked_files": checked,
        "passed_files": passed,
        "total_issues": len(issues),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "issues": issues,
    }

    # حفظ التقرير
    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)

    return report


def _check_python_file(fpath: Path, rel_path: str) -> list:
    """فحص ملف Python واحد"""
    issues = []
    
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            source = f.read()

        # فحص الترجمة (AST)
        try:
            ast.parse(source)
        except SyntaxError as e:
            issues.append({
                "file": rel_path,
                "severity": "critical",
                "type": "syntax_error",
                "line": e.lineno,
                "message": f"خطأ نحوي: {e.msg}",
                "fix": f"أصلح الخطأ النحوي في السطر {e.lineno} من {rel_path}",
            })
            return issues  # لا نكمل الفحص إذا كان هناك خطأ نحوي

        # فحص الاستيرادات
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # فحص الاستيرادات المحلية
        for imp in imports:
            if imp in ("github_sync", "persistence", "task_queue", "image_utils", 
                       "offer_id", "backup", "user_manager", "smart_backup",
                       "smart_sync", "ai_monitor", "smart_repair", "emergency_protection"):
                imp_file = BASE_DIR / f"{imp}.py"
                if not imp_file.exists():
                    issues.append({
                        "file": rel_path,
                        "severity": "warning",
                        "type": "missing_import",
                        "message": f"استيراد وحدة غير موجودة: {imp}",
                        "fix": f"تأكد من وجود {imp}.py أو أزل الاستيراد",
                    })

        # فحص الدوال غير المكتملة (pass فقط)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append({
                        "file": rel_path,
                        "severity": "warning",
                        "type": "incomplete_function",
                        "line": node.lineno,
                        "message": f"دالة غير مكتملة: {node.name}() تحتوي على pass فقط",
                        "fix": f"أكمل تنفيذ الدالة {node.name}() في السطر {node.lineno}",
                    })

        # فحص الأقواس غير المتوازنة (بسيط)
        open_count = source.count("(") + source.count("[") + source.count("{")
        close_count = source.count(")") + source.count("]") + source.count("}")
        if open_count != close_count:
            issues.append({
                "file": rel_path,
                "severity": "warning",
                "type": "unbalanced_brackets",
                "message": f"أقواس غير متوازنة: {open_count} فتح vs {close_count} إغلاق",
                "fix": "تحقق من توازن الأقواس في الملف",
            })

    except Exception as e:
        issues.append({
            "file": rel_path,
            "severity": "critical",
            "type": "read_error",
            "message": f"خطأ في قراءة الملف: {e}",
            "fix": f"تأكد من صحة ترميز الملف {rel_path}",
        })

    return issues


# ============================================================
# تحليل سجلات Railway
# ============================================================
def analyze_railway_logs() -> dict:
    """
    تحليل سجلات Railway لاكتشاف الأخطاء.
    يستخدم endpoint /health و Telegram API للحصول على معلومات.
    """
    findings = []

    # فحص Railway
    try:
        resp = requests.get(f"{RAILWAY_URL}/health", timeout=15)
        if resp.status_code != 200:
            findings.append({
                "severity": "critical",
                "service": "railway",
                "issue": f"Railway يعيد HTTP {resp.status_code}",
                "fix": "تحقق من حالة Railway — قد تحتاج لإعادة نشر",
            })
        else:
            findings.append({
                "severity": "info",
                "service": "railway",
                "issue": "Railway يعمل بشكل طبيعي",
                "fix": None,
            })
    except requests.exceptions.Timeout:
        findings.append({
            "severity": "critical",
            "service": "railway",
            "issue": "انتهاء مهلة الاتصال بـ Railway",
            "fix": "تحقق من اتصال الإنترنت وحالة Railway",
        })
    except requests.exceptions.ConnectionError:
        findings.append({
            "severity": "critical",
            "service": "railway",
            "issue": "لا يوجد اتصال بـ Railway",
            "fix": "Railway قد تكون متوقفة — تحقق من لوحة التحكم",
        })
    except Exception as e:
        findings.append({
            "severity": "warning",
            "service": "railway",
            "issue": f"خطأ غير متوقع: {e}",
            "fix": "تحقق من السجلات يدوياً",
        })

    # فحص Webhook
    try:
        resp = requests.get(f"{TELEGRAM_API}/getWebhookInfo", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                info = data.get("result", {})
                pending = info.get("pending_update_count", 0)
                last_error = info.get("last_error_message", "")
                last_error_date = info.get("last_error_date")

                if pending > 50:
                    findings.append({
                        "severity": "critical",
                        "service": "webhook",
                        "issue": f"عدد تحديثات معلقة عالي: {pending}",
                        "fix": "الـ webhook قد لا يستجيب — تحقق من Railway وأعد تعيين الـ webhook",
                    })
                elif pending > 10:
                    findings.append({
                        "severity": "warning",
                        "service": "webhook",
                        "issue": f"تحديثات معلقة: {pending}",
                        "fix": "راقب العدد — قد يكون هناك بطء في المعالجة",
                    })

                if last_error and last_error_date:
                    findings.append({
                        "severity": "warning",
                        "service": "webhook",
                        "issue": f"آخر خطأ في webhook: {last_error[:100]}",
                        "fix": "تحقق من عنوان الـ webhook وتأكد من أنه يعمل",
                    })
    except Exception as e:
        findings.append({
            "severity": "warning",
            "service": "webhook",
            "issue": f"تعذر فحص webhook: {e}",
            "fix": "تحقق من اتصال الإنترنت",
        })

    # تحليل النتائج
    critical = [f for f in findings if f["severity"] == "critical"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    
    if critical:
        status = "critical"
        message = f"مشاكل حرجة مكتشفة: {len(critical)}"
    elif warnings:
        status = "warning"
        message = f"تحذيرات: {len(warnings)}"
    else:
        status = "healthy"
        message = "جميع الخدمات تعمل بشكل طبيعي"

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "railway_logs",
        "status": status,
        "message": message,
        "findings": findings,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }

    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)

    return report


# ============================================================
# كشف المشاكل المتوقعة
# ============================================================
def detect_expected_problems() -> dict:
    """
    كشف المشاكل المتوقعة بناءً على أنماط معروفة:
    - ملفات JSON تالفة
    - ملفات مفقودة
    - أذونات غير صحيحة
    - مساحة تخزين منخفضة
    """
    problems = []
    website_dir = BASE_DIR.parent

    # فحص ملفات JSON
    json_files = [
        "bot/config.json",
        "bot/data/visitor_requests.json",
        "bot/data/bot_offers.json",
        "bot/data/bids.json",
        "bot/data/users.json",
        "bot/data/audit_log.json",
        "offers-data/offers.json",
        "offers-data/news.json",
        "offers-data/office-data.json",
    ]

    for jf in json_files:
        fpath = website_dir / jf
        if not fpath.exists():
            problems.append({
                "severity": "warning",
                "type": "missing_json",
                "file": jf,
                "issue": f"ملف JSON غير موجود: {jf}",
                "fix": f"أنشئ الملف {jf} بالمحتوى الافتراضي",
            })
        else:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                problems.append({
                    "severity": "critical",
                    "type": "corrupt_json",
                    "file": jf,
                    "issue": f"ملف JSON تالف: {e}",
                    "fix": f"أصلح أو أعد إنشاء {jf} — تأكد من صحة JSON",
                })

    # فحص مساحة التخزين
    try:
        stat = os.statvfs(str(website_dir))
        free_space = stat.f_bavail * stat.f_frsize
        total_space = stat.f_blocks * stat.f_frsize
        if total_space > 0:
            free_percent = (free_space / total_space) * 100
            if free_percent < 10:
                problems.append({
                    "severity": "critical",
                    "type": "low_disk",
                    "issue": f"مساحة تخزين منخفضة: {free_percent:.1f}% متبقية",
                    "fix": "احذف الملفات غير الضرورية أو النسخ الاحتياطية القديمة",
                })
            elif free_percent < 25:
                problems.append({
                    "severity": "warning",
                    "type": "low_disk",
                    "issue": f"مساحة تخزين منخفضة نسبياً: {free_percent:.1f}% متبقية",
                    "fix": "راقب مساحة التخزين — قد تحتاج لتنظيف قريباً",
                })
    except Exception:
        pass  # قد لا يعمل على جميع الأنظمة

    # فحص حجم bot.py (إذا كان ضخماً جداً)
    bot_py = website_dir / "bot" / "bot.py"
    if bot_py.exists():
        size_kb = bot_py.stat().st_size / 1024
        if size_kb > 300:
            problems.append({
                "severity": "warning",
                "type": "large_file",
                "file": "bot/bot.py",
                "issue": f"bot.py حجمه {size_kb:.0f}KB — قد يحتاج لتفريغ",
                "fix": "فكر في نقل بعض الدوال لوحدات منفصلة (تحسين أداء)",
            })

    critical = [p for p in problems if p["severity"] == "critical"]
    warnings = [p for p in problems if p["severity"] == "warning"]

    if critical:
        status = "critical"
        message = f"مشاكل حرجة: {len(critical)}"
    elif warnings:
        status = "warning"
        message = f"تحذيرات: {len(warnings)}"
    else:
        status = "healthy"
        message = "لا توجد مشاكل متوقعة"

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "expected_problems",
        "status": status,
        "message": message,
        "problems": problems,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }

    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)

    return report


# ============================================================
# اقتراح إصلاحات (بدون تنفيذ حساس دون موافقة)
# ============================================================
def suggest_fixes(report) -> list:
    """
    اقتراح إصلاحات بناءً على تقرير المراقبة.
    الإصلاحات الحساسة تتطلب موافقة الأدمن.
    يقبل dict (مع مفتاح issues/findings/problems) أو list مباشرة.
    """
    suggestions = []

    if isinstance(report, list):
        issues_list = report
    elif isinstance(report, dict):
        issues_list = report.get("issues", report.get("findings", report.get("problems", [])))
    else:
        issues_list = []

    for issue in issues_list:
        severity = issue.get("severity", "info")
        fix = issue.get("fix", "")
        
        if not fix:
            continue

        # تحديد ما إذا كان الإصلاح حساساً
        sensitive_keywords = ["حذف", "delete", "remove", "إعادة نشر", "redeploy", "استعادة", "restore"]
        is_sensitive = any(kw in fix.lower() for kw in sensitive_keywords) or severity == "critical"

        suggestions.append({
            "issue": issue.get("issue", issue.get("message", "")),
            "file": issue.get("file", ""),
            "severity": severity,
            "fix": fix,
            "needs_approval": is_sensitive,
            "type": issue.get("type", ""),
        })

    return suggestions


# ============================================================
# فحص شامل (Full AI Check)
# ============================================================
def full_ai_check() -> dict:
    """
    فحص شامل: قبل النشر + سجلات Railway + المشاكل المتوقعة + اقتراحات.
    """
    pre_deploy = pre_deploy_check()
    railway = analyze_railway_logs()
    problems = detect_expected_problems()
    # Phase 4: مراقبة أنظمة الحماية والتخزين
    phase4 = monitor_all_phase4()

    # تحديد الإصلاحات المقترحة
    all_issues = []
    all_issues.extend(pre_deploy.get("issues", []))
    all_issues.extend(railway.get("findings", []))
    all_issues.extend(problems.get("problems", []))
    all_issues.extend(phase4.get("problems", []))

    suggestions = suggest_fixes({"issues": all_issues})

    # الحالة العامة
    total_critical = (pre_deploy.get("critical_count", 0) + 
                      railway.get("critical_count", 0) + 
                      problems.get("critical_count", 0) +
                      phase4.get("total_critical", 0))
    total_warnings = (pre_deploy.get("warning_count", 0) + 
                      railway.get("warning_count", 0) + 
                      problems.get("warning_count", 0) +
                      phase4.get("total_warnings", 0))

    if total_critical > 0:
        overall_status = "critical"
        overall_message = f"مشاكل حرجة: {total_critical} — يلزم إصلاح قبل النشر"
    elif total_warnings > 0:
        overall_status = "warning"
        overall_message = f"تحذيرات: {total_warnings} — يمكن النشر مع متابعة"
    else:
        overall_status = "healthy"
        overall_message = "النظام سليم — جاهز للنشر"

    pending_approvals = [s for s in suggestions if s.get("needs_approval")]

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": overall_status,
        "overall_message": overall_message,
        "total_critical": total_critical,
        "total_warnings": total_warnings,
        "pre_deploy": {
            "status": pre_deploy["status"],
            "message": pre_deploy["message"],
            "checked": pre_deploy["checked_files"],
            "passed": pre_deploy["passed_files"],
        },
        "railway": {
            "status": railway["status"],
            "message": railway["message"],
        },
        "problems": {
            "status": problems["status"],
            "message": problems["message"],
        },
        "phase4": {
            "status": phase4["status"],
            "message": phase4["message"],
            "total_critical": phase4.get("total_critical", 0),
            "total_warnings": phase4.get("total_warnings", 0),
        },
        "suggestions": suggestions,
        "pending_approvals": len(pending_approvals),
        "auto_fixable": len([s for s in suggestions if not s.get("needs_approval")]),
    }


# ============================================================
# Phase 4 — مراقبة أخطاء التخزين الدائم للعقارات
# ============================================================
def monitor_property_storage() -> dict:
    """
    مراقبة أخطاء التخزين الدائم للعقارات:
    - التحقق من وجود ملف التخزين الدائم.
    - التحقق من سلامة الصور الدائمة المرتبطة بالعقارات.
    - التحقق من عدم وجود عقارات عالقة في حالة FAILED/PUBLISHING.
    """
    problems = []

    storage_file = DATA_DIR / "property_storage.json"
    if not storage_file.exists():
        problems.append({
            "severity": "warning",
            "type": "missing_property_storage",
            "file": "bot/data/property_storage.json",
            "issue": "ملف التخزين الدائم للعقارات غير موجود",
            "fix": "سيتم إنشاؤه تلقائياً عند أول تخزين — تأكد من استيراد property_storage",
        })
    else:
        try:
            with open(storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            properties = data.get("properties", {})
            missing_count = 0
            stuck_failed = 0
            stuck_publishing = 0
            for pid, prop in properties.items():
                for img in prop.get("permanent_images", []):
                    img_path = Path(img)
                    if not img_path.is_absolute():
                        img_path = BASE_DIR.parent / img_path
                    if not img_path.exists():
                        missing_count += 1
                if prop.get("status") == "failed":
                    stuck_failed += 1
                if prop.get("status") == "publishing":
                    stuck_publishing += 1
            if missing_count > 0:
                problems.append({
                    "severity": "critical",
                    "type": "missing_permanent_images",
                    "file": "bot/data/properties/",
                    "issue": f"{missing_count} صورة دائمة مفقودة من التخزين",
                    "fix": "أعد ربط الصور بالعقارات المتأثرة أو أعد تحميلها من GitHub",
                })
            if stuck_failed > 0:
                problems.append({
                    "severity": "warning",
                    "type": "failed_properties",
                    "issue": f"{stuck_failed} عقار في حالة FAILED — يحتاج مراجعة",
                    "fix": "راجع العقارات الفاشلة وأعد محاولة النشر بعد إصلاح السبب",
                })
            if stuck_publishing > 0:
                problems.append({
                    "severity": "warning",
                    "type": "stuck_publishing",
                    "issue": f"{stuck_publishing} عقار عالق في حالة PUBLISHING",
                    "fix": "تحقق من حالة النشر لهذه العقارات — قد تحتاج إعادة محاولة",
                })
        except json.JSONDecodeError as e:
            problems.append({
                "severity": "critical",
                "type": "corrupt_property_storage",
                "file": "bot/data/property_storage.json",
                "issue": f"ملف التخزين الدائم تالف: {e}",
                "fix": "أصلح JSON أو استعد من نسخة احتياطية مستقرة",
            })
        except Exception as e:
            problems.append({
                "severity": "warning",
                "type": "property_storage_error",
                "issue": f"خطأ في فحص التخزين الدائم: {e}",
                "fix": "تحقق من نظام التخزين الدائم",
            })

    critical = [p for p in problems if p["severity"] == "critical"]
    warnings = [p for p in problems if p["severity"] == "warning"]
    status = "critical" if critical else ("warning" if warnings else "healthy")
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "property_storage_monitor",
        "status": status,
        "message": f"مشاكل التخزين الدائم: {len(critical)} حرجة، {len(warnings)} تحذيرات",
        "problems": problems,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }
    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)
    return report


def storage_has_properties() -> bool:
    """التحقق من وجود عقارات في التخزين الدائم."""
    try:
        storage_file = DATA_DIR / "property_storage.json"
        if not storage_file.exists():
            return False
        with open(storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return len(data.get("properties", {})) > 0
    except Exception:
        return False


# ============================================================
# Phase 4 — مراقبة أخطاء رفع الصور
# ============================================================
def monitor_image_uploads() -> dict:
    """
    مراقبة أخطاء رفع الصور:
    - التحقق من وجود مجلدات صور الزوار.
    - التحقق من وجود صور مسودة معطوبة (حجم 0).
    - التحقق من مساحة الصور.
    """
    problems = []
    website_dir = BASE_DIR.parent

    visitor_images_dir = website_dir / "images" / "visitor"
    if visitor_images_dir.exists():
        try:
            empty_files = 0
            total_files = 0
            for req_dir in visitor_images_dir.iterdir():
                if req_dir.is_dir():
                    for img in req_dir.iterdir():
                        if img.is_file():
                            total_files += 1
                            if img.stat().st_size == 0:
                                empty_files += 1
            if empty_files > 0:
                problems.append({
                    "severity": "warning",
                    "type": "empty_image_files",
                    "file": "images/visitor/",
                    "issue": f"{empty_files} ملف صورة فارغ (حجم 0) من أصل {total_files}",
                    "fix": "احذف الملفات الفارغة أو أعد تحميل الصور",
                })
        except Exception as e:
            problems.append({
                "severity": "warning",
                "type": "image_scan_error",
                "issue": f"خطأ في فحص صور الزوار: {e}",
                "fix": "تحقق من صلاحيات الوصول لمجلد images/visitor/",
            })

    bot_images_dir = website_dir / "images" / "bot"
    if bot_images_dir.exists():
        try:
            empty_bot = 0
            total_bot = 0
            for img in bot_images_dir.iterdir():
                if img.is_file():
                    total_bot += 1
                    if img.stat().st_size == 0:
                        empty_bot += 1
            if empty_bot > 0:
                problems.append({
                    "severity": "warning",
                    "type": "empty_bot_images",
                    "file": "images/bot/",
                    "issue": f"{empty_bot} صورة مسودة فارغة من أصل {total_bot}",
                    "fix": "احذف ملفات الصور الفارغة",
                })
        except Exception:
            pass

    permanent_dir = DATA_DIR / "properties"
    if permanent_dir.exists():
        try:
            total_permanent = sum(1 for _ in permanent_dir.rglob("*") if _.is_file())
            if total_permanent == 0 and storage_has_properties():
                problems.append({
                    "severity": "warning",
                    "type": "no_permanent_images",
                    "file": "bot/data/properties/",
                    "issue": "لا توجد صور دائمة رغم وجود عقارات مخزنة",
                    "fix": "تأكد من ربط الصور بالعقارات عند النشر",
                })
        except Exception:
            pass

    critical = [p for p in problems if p["severity"] == "critical"]
    warnings = [p for p in problems if p["severity"] == "warning"]
    status = "critical" if critical else ("warning" if warnings else "healthy")
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "image_upload_monitor",
        "status": status,
        "message": f"مشاكل الصور: {len(critical)} حرجة، {len(warnings)} تحذيرات",
        "problems": problems,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }
    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)
    return report


# ============================================================
# Phase 4 — مراقبة أخطاء المزامنة
# ============================================================
def monitor_sync_errors() -> dict:
    """
    مراقبة أخطاء المزامنة:
    - التحقق من وجود عمليات مزامنة معلقة.
    - التحقق من حالة الاتصال بـ GitHub/Railway.
    - التحقق من سجل العمليات أثناء الانقطاع.
    """
    problems = []

    pending_file = DATA_DIR / "pending_syncs.json"
    if pending_file.exists():
        try:
            with open(pending_file, "r", encoding="utf-8") as f:
                pending = json.load(f)
            pending_count = len(pending) if isinstance(pending, list) else len(pending.get("syncs", []))
            if pending_count > 0:
                problems.append({
                    "severity": "warning",
                    "type": "pending_syncs",
                    "file": "bot/data/pending_syncs.json",
                    "issue": f"{pending_count} عملية مزامنة معلقة — قد يكون الاتصال مقطوعاً",
                    "fix": "تحقق من اتصال الإنترنت وأعد تشغيل المزامنة",
                })
        except Exception:
            pass

    outage_log = DATA_DIR / "outage_operations.json"
    if outage_log.exists():
        try:
            with open(outage_log, "r", encoding="utf-8") as f:
                ops = json.load(f)
            ops_count = len(ops) if isinstance(ops, list) else len(ops.get("operations", []))
            if ops_count > 50:
                problems.append({
                    "severity": "warning",
                    "type": "many_outage_ops",
                    "file": "bot/data/outage_operations.json",
                    "issue": f"{ops_count} عملية مسجلة أثناء الانقطاع — قد تحتاج للمزامنة",
                    "fix": "تأكد من مزامنة جميع العمليات المعلقة بعد استعادة الاتصال",
                })
        except Exception:
            pass

    gh_token = os.environ.get("GITHUB_TOKEN", "")
    if not gh_token:
        problems.append({
            "severity": "warning",
            "type": "missing_github_token",
            "issue": "GITHUB_TOKEN غير مضبوط — المزامنة مع GitHub لن تعمل",
            "fix": "اضبط GITHUB_TOKEN في متغيرات البيئة",
        })

    critical = [p for p in problems if p["severity"] == "critical"]
    warnings = [p for p in problems if p["severity"] == "warning"]
    status = "critical" if critical else ("warning" if warnings else "healthy")
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "sync_error_monitor",
        "status": status,
        "message": f"مشاكل المزامنة: {len(critical)} حرجة، {len(warnings)} تحذيرات",
        "problems": problems,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }
    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)
    return report


# ============================================================
# Phase 4 — مراقبة أخطاء النشر
# ============================================================
def monitor_publish_errors() -> dict:
    """
    مراقبة أخطاء النشر:
    - التحقق من نتائج التحقق من النشر (publish_verification_log.json).
    - التحقق من طلبات عالقة في PUBLISHING أو فاشلة.
    - التحقق من التطابق بين offers.json و bot_offers.json.
    """
    problems = []

    verify_log = DATA_DIR / "publish_verification_log.json"
    if verify_log.exists():
        try:
            with open(verify_log, "r", encoding="utf-8") as f:
                data = json.load(f)
            verifications = data.get("verifications", [])
            failed_verifications = [v for v in verifications if not v.get("passed")]
            if len(failed_verifications) > 0:
                recent_failed = failed_verifications[-5:]
                for v in recent_failed:
                    problems.append({
                        "severity": "critical",
                        "type": "publish_verification_failed",
                        "file": "offers-data/offers.json",
                        "issue": f"فشل التحقق من نشر العرض {v.get('offer_id', '?')}: {', '.join(v.get('failed_checks', []))}",
                        "fix": "راجع فحوصات النشر الفاشلة وأعد المحاولة بعد الإصلاح",
                    })
        except Exception:
            pass

    visitor_file = DATA_DIR / "visitor_requests.json"
    if visitor_file.exists():
        try:
            with open(visitor_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_items = list(data.get("requests", [])) + list(data.get("inquiries", []))
            publishing = [i for i in all_items if i.get("status") == "PUBLISHING"]
            failed = [i for i in all_items if i.get("status") == "rejected" and i.get("publish_status") == "Failed"]
            if len(publishing) > 0:
                problems.append({
                    "severity": "warning",
                    "type": "stuck_in_publishing",
                    "file": "bot/data/visitor_requests.json",
                    "issue": f"{len(publishing)} طلب عالق في حالة PUBLISHING",
                    "fix": "أعد محاولة النشر أو حدّث الحالة يدوياً",
                })
            if len(failed) > 0:
                problems.append({
                    "severity": "warning",
                    "type": "failed_publishes",
                    "file": "bot/data/visitor_requests.json",
                    "issue": f"{len(failed)} طلب فشل في النشر — يحتاج مراجعة",
                    "fix": "راجع سبب الفشل (fail_reason) وأعد المحاولة بعد الإصلاح",
                })
        except Exception:
            pass

    offers_file = BASE_DIR.parent / "offers-data" / "offers.json"
    bot_offers_file = DATA_DIR / "bot_offers.json"
    try:
        with open(offers_file, "r", encoding="utf-8") as f:
            site_offers = json.load(f).get("offers", [])
        with open(bot_offers_file, "r", encoding="utf-8") as f:
            bot_offers = json.load(f).get("offers", [])
        site_ids = {o.get("id") for o in site_offers}
        bot_ids = {o.get("id") for o in bot_offers}
        only_in_site = site_ids - bot_ids
        if len(only_in_site) > 5:
            problems.append({
                "severity": "warning",
                "type": "offer_mismatch",
                "file": "bot/data/bot_offers.json",
                "issue": f"{len(only_in_site)} عرض في offers.json غير موجودة في bot_offers.json",
                "fix": "مزامنة bot_offers.json مع offers.json",
            })
    except Exception:
        pass

    critical = [p for p in problems if p["severity"] == "critical"]
    warnings = [p for p in problems if p["severity"] == "warning"]
    status = "critical" if critical else ("warning" if warnings else "healthy")
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "publish_error_monitor",
        "status": status,
        "message": f"مشاكل النشر: {len(critical)} حرجة، {len(warnings)} تحذيرات",
        "problems": problems,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }
    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)
    return report


# ============================================================
# Phase 4 — مراقبة شاملة لأنظمة Phase 4
# ============================================================
def monitor_all_phase4() -> dict:
    """
    مراقبة شاملة لجميع أنظمة Phase 4:
    - أخطاء التخزين الدائم للعقارات.
    - أخطاء رفع الصور.
    - أخطاء المزامنة.
    - أخطاء النشر.
    """
    storage = monitor_property_storage()
    images = monitor_image_uploads()
    sync = monitor_sync_errors()
    publish = monitor_publish_errors()

    all_problems = []
    all_problems.extend(storage.get("problems", []))
    all_problems.extend(images.get("problems", []))
    all_problems.extend(sync.get("problems", []))
    all_problems.extend(publish.get("problems", []))

    total_critical = (storage.get("critical_count", 0) + images.get("critical_count", 0) +
                      sync.get("critical_count", 0) + publish.get("critical_count", 0))
    total_warnings = (storage.get("warning_count", 0) + images.get("warning_count", 0) +
                      sync.get("warning_count", 0) + publish.get("warning_count", 0))

    if total_critical > 0:
        status = "critical"
        message = f"مشاكل حرجة: {total_critical} — يتطلب إصلاح"
    elif total_warnings > 0:
        status = "warning"
        message = f"تحذيرات: {total_warnings} — ينبغي المتابعة"
    else:
        status = "healthy"
        message = "جميع أنظمة Phase 4 تعمل بشكل سليم"

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "phase4_full_monitor",
        "status": status,
        "message": message,
        "total_critical": total_critical,
        "total_warnings": total_warnings,
        "property_storage": {"status": storage["status"], "count": storage.get("critical_count", 0) + storage.get("warning_count", 0)},
        "image_uploads": {"status": images["status"], "count": images.get("critical_count", 0) + images.get("warning_count", 0)},
        "sync": {"status": sync["status"], "count": sync.get("critical_count", 0) + sync.get("warning_count", 0)},
        "publish": {"status": publish["status"], "count": publish.get("critical_count", 0) + publish.get("warning_count", 0)},
        "problems": all_problems,
        "suggestions": suggest_fixes({"issues": all_problems}),
    }
    reports = _load_reports()
    reports["reports"].append(report)
    _save_reports(reports)
    return report


# ============================================================
# آخر التقاير
# ============================================================
def get_recent_reports(limit=5) -> list:
    reports = _load_reports()
    return reports.get("reports", [])[-limit:]


def health_check() -> dict:
    return {
        "reports_count": len(_load_reports().get("reports", [])),
        "monitor_file": str(MONITOR_REPORT_FILE),
    }
