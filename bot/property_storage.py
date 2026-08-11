#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام التخزين الدائم للعقارات — Phase 4 AI Protection & Property Storage

الهدف: عدم فقدان أي عرض عقاري نهائياً، وعدم حذف الصور بعد الموافقة/النشر،
وربط الصور بشكل دائم بمعرف العقار (Property ID).

المميزات:
- تخزين دائم لكل عقار مع: Property ID ثابت، بيانات الزائر، رقم التواصل،
  بيانات العقار، الصور، القسم، نوع العقار، المساحة، الموقع، تاريخ الإضافة،
  تاريخ الموافقة، تاريخ النشر.
- ربط الصور بشكل دائم بمعرف العقار (نسخها إلى مخزن دائم وليس روابط مؤقتة).
- منع فقدان الصور عند إعادة النشر (republish).
- تتبع حالة العقار خلال دورة الحياة: NEW → UNDER_REVIEW → APPROVED →
  PUBLISHING → VERIFYING → PUBLISHED (أو FAILED / ARCHIVED).
- كتابة ذرية (atomic write) لمنع تلف الملفات.
- أمان خيوط (thread-safe) باستخدام threading.Lock.
- سجل حركة كامل (movement log) لكل تغيير في الحالة.

الملفات:
- bot/data/property_storage.json — التخزين الدائم للعقارات.
- bot/data/properties/ — المخزن الدائم للصور المرتبطة بالعقارات.
"""

import json
import os
import shutil
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.property_storage")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STORAGE_FILE = DATA_DIR / "property_storage.json"
PROPERTIES_DIR = DATA_DIR / "properties"      # المخزن الدائم للصور

DATA_DIR.mkdir(parents=True, exist_ok=True)
PROPERTIES_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  حالات العقار (تتطابق مع bot.py)
# ============================================================
STATUS_NEW = "new"
STATUS_UNDER_REVIEW = "under_review"
STATUS_APPROVED = "approved"
STATUS_PUBLISHING = "publishing"
STATUS_VERIFYING = "verifying"
STATUS_PUBLISHED = "published"
STATUS_FAILED = "failed"
STATUS_ARCHIVED = "archived"
STATUS_REJECTED = "rejected"

VALID_STATUSES = {
    STATUS_NEW, STATUS_UNDER_REVIEW, STATUS_APPROVED,
    STATUS_PUBLISHING, STATUS_VERIFYING, STATUS_PUBLISHED,
    STATUS_FAILED, STATUS_ARCHIVED, STATUS_REJECTED,
}

# ============================================================
#  المخزن الداخلي
# ============================================================
_properties = {}          # property_id (str) -> property dict
_lock = threading.Lock()
_initialized = False


# ============================================================
#  أدوات مساعدة للكتابة الذرية
# ============================================================
def _atomic_write_json(file_path: Path, data: dict):
    """كتابة JSON بشكل ذري: اكتب في ملف مؤقت ثم استبدل."""
    try:
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(file_path)
    except Exception as e:
        logger.error("خطأ في الكتابة الذرية لـ %s: %s", file_path, e)


def _safe_read_json(file_path: Path, default: dict) -> dict:
    """قراءة JSON بأمان مع قيمة افتراضية عند الفشل."""
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("خطأ في قراءة %s: %s — استخدام القيمة الافتراضية", file_path, e)
        return default


def _now_iso() -> str:
    """الوقت الحالي بصيغة ISO 8601."""
    return datetime.now().isoformat()


# ============================================================
#  التهيئة
# ============================================================
def init():
    """تحميل بيانات العقارات من القرص."""
    global _properties, _initialized
    with _lock:
        if _initialized:
            return
        data = _safe_read_json(STORAGE_FILE, {})
        _properties = data.get("properties", {})
        _initialized = True
        logger.info("تم تحميل %d عقار من التخزين الدائم", len(_properties))


def _ensure_init():
    """التأكد من تهيئة النظام."""
    if not _initialized:
        init()


def _save():
    """حفظ كل العقارات إلى القرص (يجب استدعاؤها داخل القفل)."""
    _atomic_write_json(STORAGE_FILE, {"properties": _properties})


# ============================================================
#  الدوال الأساسية
# ============================================================
def store_property(
    property_id: str,
    visitor_data: dict | None = None,
    contact_number: str | None = None,
    property_data: dict | None = None,
    images: list | None = None,
    section: str | None = None,
    property_type: str | None = None,
    area: str | None = None,
    location: str | None = None,
    add_date: str | None = None,
    approval_date: str | None = None,
    publish_date: str | None = None,
    status: str = STATUS_NEW,
    offer_id: str | None = None,
    final_url: str | None = None,
    request_id: str | None = None,
) -> dict:
    """
    تخزين عقار بشكل دائم. إذا كان معرف العقار موجوداً مسبقاً يتم التحديث
    (ولكن لا يتم حذف الصور الموجودة مسبقاً — تُضاف الجديدة فقط).

    المعاملات:
        property_id: معرف العقار الثابت (لا يتغير).
        visitor_data: بيانات الزائر (الاسم، إلخ).
        contact_number: رقم التواصل.
        property_data: بيانات العقار الكاملة (العنوان، السعر، الوصف...).
        images: قائمة مسارات الصور (سيتم نسخها للمخزن الدائم).
        section: القسم.
        property_type: نوع العقار.
        area: المساحة/المنطقة.
        location: الموقع.
        add_date: تاريخ الإضافة.
        approval_date: تاريخ الموافقة.
        publish_date: تاريخ النشر.
        status: الحالة الأولية.
        offer_id: معرف العرض (AFQ-YYYY-NNNN) إن وُجد.
        final_url: الرابط النهائي للعقار.
        request_id: معرف طلب الزائر الأصلي.

    المُرجَع: قاموس العقار المُخزَّن.
    """
    _ensure_init()
    with _lock:
        now = _now_iso()
        existing = _properties.get(property_id, {})
        is_new = property_id not in _properties

        # دمج الصور: لا نحذف الصور القديمة، نضيف الجديدة فقط
        existing_images = existing.get("images", [])
        existing_permanent_images = existing.get("permanent_images", [])

        # نسخ الصور الجديدة إلى المخزن الدائم
        permanent_images = list(existing_permanent_images)
        if images:
            permanent_images = _link_images_permanently_locked(
                property_id, images, permanent_images
            )

        # بناء قاموس العقار
        prop = {
            "property_id": property_id,
            "request_id": request_id or existing.get("request_id"),
            "offer_id": offer_id or existing.get("offer_id"),
            "visitor_data": visitor_data or existing.get("visitor_data", {}),
            "contact_number": contact_number or existing.get("contact_number"),
            "property_data": property_data or existing.get("property_data", {}),
            "images": list(set(existing_images + (images or []))),
            "permanent_images": permanent_images,
            "section": section or existing.get("section"),
            "property_type": property_type or existing.get("property_type"),
            "area": area or existing.get("area"),
            "location": location or existing.get("location"),
            "status": status if status in VALID_STATUSES else existing.get("status", STATUS_NEW),
            "final_url": final_url or existing.get("final_url"),
            "add_date": add_date or existing.get("add_date", now),
            "approval_date": approval_date or existing.get("approval_date"),
            "publish_date": publish_date or existing.get("publish_date"),
            "created_at": existing.get("created_at", now),
            "updated_at": now,
        }

        # سجل الحركة
        movement_log = existing.get("movement_log", [])
        if is_new:
            movement_log.append({
                "timestamp": now,
                "action": "created",
                "status": prop["status"],
                "detail": "إنشاء عقار جديد في التخزين الدائم",
            })
        else:
            movement_log.append({
                "timestamp": now,
                "action": "updated",
                "status": prop["status"],
                "detail": "تحديث بيانات العقار",
            })

        # سجل تواريخ تغيير الحالة
        status_history = existing.get("status_history", [])
        prev_status = existing.get("status")
        if prev_status != prop["status"]:
            status_history.append({
                "timestamp": now,
                "from_status": prev_status,
                "to_status": prop["status"],
            })

        prop["movement_log"] = movement_log
        prop["status_history"] = status_history

        _properties[property_id] = prop
        _save()
        logger.info("تم تخزين العقار %s (جديد=%s, حالة=%s)", property_id, is_new, prop["status"])
        return prop


def _link_images_permanently_locked(property_id: str, images: list, existing_permanent: list) -> list:
    """
    نسخ الصور إلى المخزن الدائم المرتبط بمعرف العقار.
    يجب استدعاؤها داخل القفل. لا تحذف الصور الموجودة مسبقاً.

    المُرجَع: قائمة مسارات الصور الدائمة.
    """
    prop_dir = PROPERTIES_DIR / property_id
    prop_dir.mkdir(parents=True, exist_ok=True)

    permanent = list(existing_permanent)
    for idx, img_src in enumerate(images):
        if not img_src:
            continue
        # إذا كانت الصورة بالفعل في المخزن الدائم، تخطّيها
        if str(img_src) in permanent:
            continue
        try:
            src = Path(img_src)
            if not src.is_absolute():
                # محاولة الحل بالنسبة لمجلد المشروع
                src = BASE_DIR.parent / src
            if src.exists() and src.is_file():
                # اسم الملف الدائم: index_الاسم_الأصلي
                dest_name = f"img_{len(permanent):03d}_{src.name}"
                dest = prop_dir / dest_name
                shutil.copy2(str(src), str(dest))
                permanent.append(str(dest))
                logger.debug("تم نسخ صورة دائمة للعقار %s: %s", property_id, dest)
            else:
                # الملف غير موجود — نحتفظ بالمسار كما هو (للربط)
                logger.warning("الصورة غير موجودة: %s — الاحتفاظ بالمسار", img_src)
                permanent.append(str(img_src))
        except Exception as e:
            logger.error("فشل نسخ الصورة %s للعقار %s: %s", img_src, property_id, e)
            # لا نحذف شيئاً، نحتفظ بالمسار الأصلي
            permanent.append(str(img_src))

    return permanent


def link_images_to_property(property_id: str, images: list) -> list:
    """
    ربط الصور بشكل دائم بمعرف العقار (واجهة عامة).
    لا يحذف الصور الموجودة مسبقاً. يُرجع قائمة الصور الدائمة.

    هذا يمنع فقدان الصور عند إعادة النشر: حتى لو حُذفت الصور المؤقتة،
    تظل الصور الدائمة محفوظة في bot/data/properties/{property_id}/.
    """
    _ensure_init()
    with _lock:
        existing = _properties.get(property_id, {})
        existing_permanent = existing.get("permanent_images", [])
        permanent = _link_images_permanently_locked(property_id, images, existing_permanent)
        existing["permanent_images"] = permanent
        existing["updated_at"] = _now_iso()
        existing["images"] = list(set(existing.get("images", []) + images))
        existing["movement_log"] = existing.get("movement_log", [])
        existing["movement_log"].append({
            "timestamp": _now_iso(),
            "action": "images_linked",
            "detail": f"ربط {len(images)} صورة بشكل دائم",
        })
        _properties[property_id] = existing
        _save()
        logger.info("تم ربط %d صورة بالعقار %s", len(images), property_id)
        return permanent


def get_property(property_id: str) -> dict | None:
    """الحصول على عقار بمعرفه. المُرجَع: قاموس العقار أو None."""
    _ensure_init()
    with _lock:
        return _properties.get(property_id)


def list_properties(status: str | None = None, section: str | None = None) -> list:
    """
    قائمة العقارات، مع إمكانية الفلترة بالحالة أو القسم.
    المُرجَع: قائمة قواميس العقارات.
    """
    _ensure_init()
    with _lock:
        props = list(_properties.values())
    if status:
        props = [p for p in props if p.get("status") == status]
    if section:
        props = [p for p in props if p.get("section") == section]
    # ترتيب من الأحدث للأقدم
    props.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return props


def update_property_status(
    property_id: str,
    new_status: str,
    detail: str | None = None,
    extra: dict | None = None,
) -> dict | None:
    """
    تحديث حالة عقار مع تسجيل في سجل الحركة وسجل تواريخ الحالة.

    المعاملات:
        property_id: معرف العقار.
        new_status: الحالة الجديدة (يجب أن تكون ضمن VALID_STATUSES).
        detail: تفاصيل إضافية للتسجيل في سجل الحركة.
        extra: حقول إضافية لتحديثها (مثل final_url, offer_id, publish_date).

    المُرجَع: قاموس العقار المُحدَّث أو None إذا لم يُوجَد.
    """
    _ensure_init()
    if new_status not in VALID_STATUSES:
        logger.error("حالة غير صالحة: %s", new_status)
        return None
    with _lock:
        prop = _properties.get(property_id)
        if not prop:
            logger.warning("العقار غير موجود: %s", property_id)
            return None
        now = _now_iso()
        old_status = prop.get("status")

        # تحديث الحالة
        prop["status"] = new_status
        prop["updated_at"] = now

        # تحديث الحقول الإضافية
        if extra:
            for k, v in extra.items():
                if v is not None:
                    prop[k] = v

        # سجل الحركة
        prop.setdefault("movement_log", []).append({
            "timestamp": now,
            "action": "status_change",
            "from_status": old_status,
            "to_status": new_status,
            "detail": detail or f"تغيير الحالة من {old_status} إلى {new_status}",
        })

        # سجل تواريخ تغيير الحالة
        if old_status != new_status:
            prop.setdefault("status_history", []).append({
                "timestamp": now,
                "from_status": old_status,
                "to_status": new_status,
            })

        _properties[property_id] = prop
        _save()
        logger.info("تحديث حالة العقار %s: %s → %s", property_id, old_status, new_status)
        return prop


def get_property_images(property_id: str) -> list:
    """الحصول على قائمة الصور الدائمة للعقار. المُرجَع: قائمة المسارات."""
    _ensure_init()
    with _lock:
        prop = _properties.get(property_id, {})
        return prop.get("permanent_images", [])


def get_properties_count(status: str | None = None) -> int:
    """عدد العقارات، مع إمكانية الفلترة بالحالة."""
    _ensure_init()
    with _lock:
        if status:
            return sum(1 for p in _properties.values() if p.get("status") == status)
        return len(_properties)


def get_movement_log(property_id: str) -> list:
    """الحصول على سجل الحركة الكامل لعقار. المُرجَع: قائمة أحداث."""
    _ensure_init()
    with _lock:
        prop = _properties.get(property_id, {})
        return prop.get("movement_log", [])


def archive_property(property_id: str, reason: str | None = None) -> dict | None:
    """أرشفة عقار (لا حذف — فقط تغيير الحالة إلى archived)."""
    return update_property_status(property_id, STATUS_ARCHIVED, detail=reason or "أرشفة العقار")


def verify_storage_integrity() -> dict:
    """
    فحص سلامة التخزين الدائم: التأكد من وجود الملف، وجود الصور الدائمة،
    عدم وجود معرفات مكررة.

    المُرجَع: تقرير سلامة {ok, total, missing_images, issues}.
    """
    _ensure_init()
    with _lock:
        total = len(_properties)
        missing_images = []
        issues = []
        for pid, prop in _properties.items():
            perm_imgs = prop.get("permanent_images", [])
            for img in perm_imgs:
                p = Path(img)
                if not p.is_absolute():
                    p = BASE_DIR.parent / p
                if not p.exists():
                    missing_images.append({"property_id": pid, "image": img})
        if missing_images:
            issues.append(f"{len(missing_images)} صورة دائمة مفقودة")
        # التحقق من عدم تكرار معرفات
        ids = [p.get("property_id") for p in _properties.values()]
        if len(ids) != len(set(ids)):
            issues.append("معرفات عقارات مكررة")
        return {
            "ok": len(issues) == 0,
            "total": total,
            "missing_images": missing_images,
            "issues": issues,
            "checked_at": _now_iso(),
        }


def get_storage_stats() -> dict:
    """إحصائيات التخزين الدائم."""
    _ensure_init()
    with _lock:
        stats = {
            "total": len(_properties),
            "by_status": {},
            "by_section": {},
            "with_images": 0,
            "total_images": 0,
            "published_count": 0,
        }
        for prop in _properties.values():
            st = prop.get("status", "unknown")
            stats["by_status"][st] = stats["by_status"].get(st, 0) + 1
            sec = prop.get("section")
            if sec:
                stats["by_section"][sec] = stats["by_section"].get(sec, 0) + 1
            imgs = prop.get("permanent_images", [])
            if imgs:
                stats["with_images"] += 1
                stats["total_images"] += len(imgs)
            if prop.get("status") == STATUS_PUBLISHED:
                stats["published_count"] += 1
        return stats


# ============================================================
#  التهيئة التلقائية عند الاستيراد
# ============================================================
init()
