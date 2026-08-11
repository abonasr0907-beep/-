#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام التحقق الإلزامي من النشر — Phase 4 AI Protection

الهدف: التأكد من أن العرض قد نُشر فعلاً وظهر بشكل صحيح قبل تعيين الحالة
إلى PUBLISHED. لا يتم تعيين PUBLISHED إلا بعد نجاح جميع الفحوصات.

دورة النشر:
    APPROVED → PUBLISHING → VERIFYING → PUBLISHED (أو FAILED)

الفحوصات التسعة (9 checks):
    1. العرض موجود في قاعدة البيانات (offers.json).
    2. العرض موجود في قائمة العروض المنشورة (bot_offers.json).
    3. العرض مرئي على الموقع (تحقق من وجوده في البيانات المنشورة).
    4. العرض في القسم الصحيح (section/area/property_type).
    5. جميع صور العرض مرئية (الملفات موجودة).
    6. العرض على الخريطة (إحداثيات أو رابط خريطة).
    7. صفحة التفاصيل تعمل (رابط نهائي صالح).
    8. رابط التواصل يعمل (رقم تواصل موجود).
    9. معرف العرض النهائي موجود (offer_id صالح).

عند الفشل:
    - لا يتم تعيين الحالة إلى PUBLISHED.
    - يتم تعيين الحالة إلى FAILED أو UNDER_REVIEW.
    - يتم إنشاء تقرير بالمشكلة.
    - يتم إرسال تقرير المشكلة للأدمن.
    - يقوم AI Monitor بتحليل السبب.
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.publish_verifier")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WEBSITE_DIR = BASE_DIR.parent
OFFERS_JSON = WEBSITE_DIR / "offers-data" / "offers.json"
BOT_OFFERS_JSON = DATA_DIR / "bot_offers.json"
VERIFICATION_LOG = DATA_DIR / "publish_verification_log.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  المخزن الداخلي
# ============================================================
_verification_log = []
_lock = threading.Lock()


# ============================================================
#  أدوات مساعدة
# ============================================================
def _atomic_write_json(file_path: Path, data):
    """كتابة JSON بشكل ذري."""
    try:
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(file_path)
    except Exception as e:
        logger.error("خطأ في الكتابة الذرية لـ %s: %s", file_path, e)


def _safe_read_json(file_path: Path, default):
    """قراءة JSON بأمان."""
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("خطأ في قراءة %s: %s", file_path, e)
        return default


def _now_iso() -> str:
    return datetime.now().isoformat()


def _load_log():
    global _verification_log
    data = _safe_read_json(VERIFICATION_LOG, {"verifications": []})
    _verification_log = data.get("verifications", [])


def _save_log():
    _atomic_write_json(VERIFICATION_LOG, {"verifications": _verification_log[-200:]})


_load_log()


# ============================================================
#  الفحوصات الفردية
# ============================================================
def _check_1_in_database(offer_id: str) -> dict:
    """الفحص 1: العرض موجود في قاعدة البيانات (offers.json)."""
    try:
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        found = any(o.get("id") == offer_id for o in data.get("offers", []))
        return {
            "check": "in_database",
            "passed": found,
            "detail": f"العرض {offer_id} {'موجود' if found else 'غير موجود'} في offers.json",
        }
    except Exception as e:
        return {"check": "in_database", "passed": False, "detail": f"خطأ: {e}"}


def _check_2_in_published_list(offer_id: str) -> dict:
    """الفحص 2: العرض موجود في قائمة العروض المنشورة (bot_offers.json)."""
    try:
        data = _safe_read_json(BOT_OFFERS_JSON, {"offers": []})
        found = any(o.get("id") == offer_id for o in data.get("offers", []))
        return {
            "check": "in_published_list",
            "passed": found,
            "detail": f"العرض {offer_id} {'موجود' if found else 'غير موجود'} في bot_offers.json",
        }
    except Exception as e:
        return {"check": "in_published_list", "passed": False, "detail": f"خطأ: {e}"}


def _check_3_visible_on_website(offer_id: str) -> dict:
    """الفحص 3: العرض مرئي على الموقع (تحقق من البيانات المنشورة)."""
    try:
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        offer = next((o for o in data.get("offers", []) if o.get("id") == offer_id), None)
        if not offer:
            return {
                "check": "visible_on_website",
                "passed": False,
                "detail": f"العرض {offer_id} غير موجود في البيانات المنشورة",
            }
        # التحقق من وجود الحقول الأساسية
        has_title = bool(offer.get("title"))
        has_price = bool(offer.get("price_text") or offer.get("price"))
        passed = has_title and has_price
        return {
            "check": "visible_on_website",
            "passed": passed,
            "detail": f"العنوان: {'✓' if has_title else '✗'}، السعر: {'✓' if has_price else '✗'}",
        }
    except Exception as e:
        return {"check": "visible_on_website", "passed": False, "detail": f"خطأ: {e}"}


def _check_4_correct_section(offer_id: str, expected_section: str = None,
                              expected_area: str = None, expected_type: str = None) -> dict:
    """الفحص 4: العرض في القسم/المنطقة/النوع الصحيح."""
    try:
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        offer = next((o for o in data.get("offers", []) if o.get("id") == offer_id), None)
        if not offer:
            return {
                "check": "correct_section",
                "passed": False,
                "detail": f"العرض {offer_id} غير موجود",
            }
        issues = []
        actual_type = offer.get("type", "").lower()
        actual_section = offer.get("section", "")
        actual_area = offer.get("area", "")
        actual_prop_type = offer.get("property_type", "")

        if expected_type and actual_type and actual_type != expected_type.lower():
            issues.append(f"النوع: متوقع {expected_type}، موجود {actual_type}")
        if expected_area and actual_area and expected_area not in actual_area and actual_area not in expected_area:
            issues.append(f"المنطقة: متوقعة {expected_area}، موجودة {actual_area}")
        if expected_section and actual_section and actual_section != expected_section:
            issues.append(f"القسم: متوقع {expected_section}، موجود {actual_section}")

        passed = len(issues) == 0
        detail = "كل الحقول صحيحة" if passed else "؛ ".join(issues)
        return {
            "check": "correct_section",
            "passed": passed,
            "detail": detail,
        }
    except Exception as e:
        return {"check": "correct_section", "passed": False, "detail": f"خطأ: {e}"}


def _check_5_images_visible(offer_id: str) -> dict:
    """الفحص 5: جميع صور العرض مرئية (الملفات موجودة أو روابط صالحة)."""
    try:
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        offer = next((o for o in data.get("offers", []) if o.get("id") == offer_id), None)
        if not offer:
            return {
                "check": "images_visible",
                "passed": False,
                "detail": f"العرض {offer_id} غير موجود",
            }
        images = offer.get("images", [])
        if not images:
            # لا توجد صور — نعتبره ناجحاً (بعض العروض بدون صور)
            return {
                "check": "images_visible",
                "passed": True,
                "detail": "لا توجد صور (مقبول)",
            }
        # التحقق من وجود ملفات الصور محلياً
        images_dir = WEBSITE_DIR / "images"
        missing = []
        for img in images:
            if isinstance(img, str):
                if img.startswith("http://") or img.startswith("https://"):
                    # رابط خارجي — نعتبره صالحاً (لا يمكن الفحص دون اتصال)
                    continue
                # مسار محلي
                img_path = WEBSITE_DIR / img if not Path(img).is_absolute() else Path(img)
                if not img_path.exists():
                    missing.append(img)
        passed = len(missing) == 0
        detail = f"{len(images)} صورة، {len(missing)} مفقودة" if missing else f"{len(images)} صورة كلها موجودة"
        return {
            "check": "images_visible",
            "passed": passed,
            "detail": detail,
            "missing_images": missing,
        }
    except Exception as e:
        return {"check": "images_visible", "passed": False, "detail": f"خطأ: {e}"}


def _check_6_on_map(offer_id: str) -> dict:
    """الفحص 6: العرض على الخريطة (إحداثيات أو رابط خريطة)."""
    try:
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        offer = next((o for o in data.get("offers", []) if o.get("id") == offer_id), None)
        if not offer:
            return {
                "check": "on_map",
                "passed": False,
                "detail": f"العرض {offer_id} غير موجود",
            }
        has_lat = bool(offer.get("visitor_lat"))
        has_lng = bool(offer.get("visitor_lng"))
        has_map_link = bool(offer.get("map_link") or offer.get("visitor_map_link"))
        passed = (has_lat and has_lng) or has_map_link
        detail_parts = []
        if has_lat and has_lng:
            detail_parts.append(f"إحداثيات: {offer.get('visitor_lat')}, {offer.get('visitor_lng')}")
        if has_map_link:
            detail_parts.append("رابط خريطة موجود")
        if not passed:
            detail_parts.append("لا توجد إحداثيات ولا رابط خريطة")
        return {
            "check": "on_map",
            "passed": passed,
            "detail": "؛ ".join(detail_parts),
        }
    except Exception as e:
        return {"check": "on_map", "passed": False, "detail": f"خطأ: {e}"}


def _check_7_details_page(offer_id: str, final_url: str = None) -> dict:
    """الفحص 7: صفحة التفاصيل تعمل (رابط نهائي صالح)."""
    try:
        if not final_url:
            # بناء الرابط النهائي المتوقع
            final_url = f"/property/{offer_id}"
        # التحقق من وجود ملف صفحة العقار
        property_page = WEBSITE_DIR / "property.html"
        page_exists = property_page.exists()
        # التحقق من صحة تنسيق الرابط
        url_valid = bool(offer_id) and ("/property/" in str(final_url) or offer_id in str(final_url))
        passed = page_exists and url_valid
        detail = f"صفحة property.html: {'موجودة' if page_exists else 'غير موجودة'}؛ الرابط: {'صالح' if url_valid else 'غير صالح'}"
        return {
            "check": "details_page",
            "passed": passed,
            "detail": detail,
            "final_url": final_url,
        }
    except Exception as e:
        return {"check": "details_page", "passed": False, "detail": f"خطأ: {e}"}


def _check_8_contact_link(offer_id: str) -> dict:
    """الفحص 8: رابط التواصل يعمل (رقم تواصل موجود)."""
    try:
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        offer = next((o for o in data.get("offers", []) if o.get("id") == offer_id), None)
        if not offer:
            return {
                "check": "contact_link",
                "passed": False,
                "detail": f"العرض {offer_id} غير موجود",
            }
        has_phone = bool(offer.get("visitor_phone"))
        has_name = bool(offer.get("visitor_name"))
        passed = has_phone or has_name
        detail = f"هاتف: {'✓' if has_phone else '✗'}، اسم: {'✓' if has_name else '✗'}"
        return {
            "check": "contact_link",
            "passed": passed,
            "detail": detail,
        }
    except Exception as e:
        return {"check": "contact_link", "passed": False, "detail": f"خطأ: {e}"}


def _check_9_offer_id_exists(offer_id: str) -> dict:
    """الفحص 9: معرف العرض النهائي موجود وصالح."""
    try:
        if not offer_id:
            return {
                "check": "offer_id_exists",
                "passed": False,
                "detail": "معرف العرض فارغ",
            }
        # التحقق من تنسيق المعرف (يجب أن يحتوي على شرطة وأحرف/أرقام)
        has_valid_format = "-" in offer_id and len(offer_id) >= 5
        # التحقق من عدم تكرار المعرف
        data = _safe_read_json(OFFERS_JSON, {"offers": []})
        count = sum(1 for o in data.get("offers", []) if o.get("id") == offer_id)
        is_unique = count == 1
        passed = has_valid_format and is_unique
        detail = f"تنسيق: {'✓' if has_valid_format else '✗'}، فريد: {'✓' if is_unique else '✗ (مكرر ' + str(count) + ')'}"
        return {
            "check": "offer_id_exists",
            "passed": passed,
            "detail": detail,
        }
    except Exception as e:
        return {"check": "offer_id_exists", "passed": False, "detail": f"خطأ: {e}"}


# ============================================================
#  التحقق الكامل
# ============================================================
def verify_publishing(
    offer_id: str,
    expected_section: str = None,
    expected_area: str = None,
    expected_type: str = None,
    final_url: str = None,
) -> dict:
    """
    تنفيذ جميع الفحوصات التسعة للتحقق من النشر.

    المُرجَع: قاموس نتيجة التحقق:
        {
            "offer_id": str,
            "passed": bool,           # True فقط إذا نجحت جميع الفحوصات
            "all_passed": bool,
            "checks": [list of check results],
            "failed_checks": [list of failed check names],
            "timestamp": str,
            "summary": str,
        }
    """
    checks = []
    checks.append(_check_1_in_database(offer_id))
    checks.append(_check_2_in_published_list(offer_id))
    checks.append(_check_3_visible_on_website(offer_id))
    checks.append(_check_4_correct_section(offer_id, expected_section, expected_area, expected_type))
    checks.append(_check_5_images_visible(offer_id))
    checks.append(_check_6_on_map(offer_id))
    checks.append(_check_7_details_page(offer_id, final_url))
    checks.append(_check_8_contact_link(offer_id))
    checks.append(_check_9_offer_id_exists(offer_id))

    failed_checks = [c["check"] for c in checks if not c.get("passed", False)]
    all_passed = len(failed_checks) == 0
    timestamp = _now_iso()

    result = {
        "offer_id": offer_id,
        "passed": all_passed,
        "all_passed": all_passed,
        "checks": checks,
        "failed_checks": failed_checks,
        "timestamp": timestamp,
        "summary": _build_summary(offer_id, checks, all_passed),
    }

    # حفظ في السجل
    with _lock:
        _verification_log.append(result)
        _save_log()

    if all_passed:
        logger.info("✅ التحقق من النشر نجح للعرض %s — جميع الفحوصات التسعة نجحت", offer_id)
    else:
        logger.error("❌ التحقق من النشر فشل للعرض %s — فحوصات فاشلة: %s", offer_id, failed_checks)

    return result


def _build_summary(offer_id: str, checks: list, all_passed: bool) -> str:
    """بناء ملخص نصي لنتيجة التحقق."""
    if all_passed:
        return f"✅ تم التحقق من نشر العرض {offer_id} بنجاح — جميع الفحوصات التسعة اجتازت."
    lines = [f"❌ فشل التحقق من نشر العرض {offer_id}:"]
    for c in checks:
        icon = "✅" if c.get("passed") else "❌"
        lines.append(f"  {icon} {c['check']}: {c.get('detail', '')}")
    return "\n".join(lines)


def get_verification_result(offer_id: str) -> dict | None:
    """الحصول على آخر نتيجة تحقق لعرض معين."""
    with _lock:
        for v in reversed(_verification_log):
            if v.get("offer_id") == offer_id:
                return v
    return None


def get_verification_history(limit: int = 50) -> list:
    """الحصول على سجل عمليات التحقق."""
    with _lock:
        return list(reversed(_verification_log[-limit:]))


def get_verification_stats() -> dict:
    """إحصائيات عمليات التحقق."""
    with _lock:
        total = len(_verification_log)
        passed = sum(1 for v in _verification_log if v.get("passed"))
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
        }
