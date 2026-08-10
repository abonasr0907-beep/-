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

    # تحديد الإصلاحات المقترحة
    all_issues = []
    all_issues.extend(pre_deploy.get("issues", []))
    all_issues.extend(railway.get("findings", []))
    all_issues.extend(problems.get("problems", []))

    suggestions = suggest_fixes({"issues": all_issues})

    # الحالة العامة
    total_critical = (pre_deploy.get("critical_count", 0) + 
                      railway.get("critical_count", 0) + 
                      problems.get("critical_count", 0))
    total_warnings = (pre_deploy.get("warning_count", 0) + 
                      railway.get("warning_count", 0) + 
                      problems.get("warning_count", 0))

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
        "suggestions": suggestions,
        "pending_approvals": len(pending_approvals),
        "auto_fixable": len([s for s in suggestions if not s.get("needs_approval")]),
    }


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
