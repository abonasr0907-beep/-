#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مولّد معرفات العروض التسلسلية
الصيغة: AFQ-{YEAR}-{SEQUENCE:04d}
مثال: AFQ-2026-0001، AFQ-2026-0002، ...

المميزات:
- معرفات فريدة لا تتكرر
- تسلسلية وقابلة للبحث
- تُستخدم في التقارير والإحصائيات
- أمان خيطي (thread-safe)
- مزامنة مع العروض الموجودة لمنع التكرار
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.offer_id")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
COUNTER_FILE = DATA_DIR / "offer_counter.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  الثوابت
# ============================================================
PREFIX = "AFQ"

# ============================================================
#  المخزن الداخلي
# ============================================================
_counter = {}       # {"year": 2026, "sequence": 0, "total": 0}
_lock = threading.Lock()
_initialized = False


# ============================================================
#  أدوات مساعدة
# ============================================================
def _atomic_write_json(file_path: Path, data: dict):
    """كتابة JSON بشكل ذري"""
    try:
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(file_path)
    except Exception as e:
        logger.error(f"خطأ في الكتابة الذرية لـ {file_path}: {e}")


def _safe_read_json(file_path: Path, default: dict) -> dict:
    """قراءة JSON بأمان"""
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


# ============================================================
#  التهيئة
# ============================================================
def init():
    """تهيئة العدّاد من القرص"""
    global _counter, _initialized
    with _lock:
        if _initialized:
            return
        _counter = _safe_read_json(COUNTER_FILE, {})
        current_year = datetime.now().year
        if not _counter:
            _counter = {"year": current_year, "sequence": 0, "total": 0}
        # التحقق من تغيير السنة
        if _counter.get("year", current_year) != current_year:
            _counter["year"] = current_year
            _counter["sequence"] = 0
            logger.info(f"📅 سنة جديدة! تم تصفير العدّاد للسنة {current_year}")
        _initialized = True
        logger.info(f"🔢 عدّاد العروض: السنة {_counter['year']}، التسلسل {_counter['sequence']}, الإجمالي {_counter.get('total', 0)}")


def _save_counter():
    """حفظ العدّاد على القرص (داخلي)"""
    _atomic_write_json(COUNTER_FILE, _counter)


# ============================================================
#  توليد المعرفات
# ============================================================
def generate_offer_id() -> str:
    """
    توليد معرف عرض تسلسلي فريد.
    الصيغة: AFQ-2026-0001
    """
    init()
    with _lock:
        current_year = datetime.now().year
        if _counter.get("year", current_year) != current_year:
            _counter["year"] = current_year
            _counter["sequence"] = 0

        _counter["sequence"] += 1
        _counter["total"] = _counter.get("total", 0) + 1
        _save_counter()

        offer_id = f"{PREFIX}-{_counter['year']}-{_counter['sequence']:04d}"
        logger.info(f"🆔 تم توليد معرف عرض جديد: {offer_id}")
        return offer_id


def get_last_id() -> str:
    """جلب آخر معرف تم توليده"""
    init()
    with _lock:
        return f"{PREFIX}-{_counter.get('year', datetime.now().year)}-{_counter.get('sequence', 0):04d}"


def get_year_count() -> int:
    """عدد العروض في السنة الحالية"""
    init()
    with _lock:
        return _counter.get("sequence", 0)


def get_total_count() -> int:
    """إجمالي عدد العروض على الإطلاق"""
    init()
    with _lock:
        return _counter.get("total", 0)


# ============================================================
#  المزامنة مع العروض الموجودة
# ============================================================
def sync_with_existing_offers(offers_list: list):
    """
    مزامنة العدّاد مع العروض الموجودة لضمان عدم التكرار.
    يفحص جميع العروض ويحدّث العدّاد ليكون أعلى من أكبر رقم موجود.

    المعاملات:
        offers_list: قائمة العروض (كل عرض له مفتاح 'id')
    """
    init()
    current_year = datetime.now().year
    max_seq = 0

    for offer in offers_list:
        oid = offer.get("id", "")
        # محاولة استخراج الرقم من المعرفات القديمة (مثل FRM-001) أو الجديدة (AFQ-2026-0001)
        try:
            if oid.startswith(f"{PREFIX}-{current_year}-"):
                seq = int(oid.split("-")[-1])
                if seq > max_seq:
                    max_seq = seq
            elif oid.startswith(f"{PREFIX}-"):
                parts = oid.split("-")
                if len(parts) >= 3:
                    year = int(parts[1])
                    seq = int(parts[2])
                    if year == current_year and seq > max_seq:
                        max_seq = seq
        except (ValueError, IndexError):
            continue

    with _lock:
        if max_seq > _counter.get("sequence", 0):
            _counter["sequence"] = max_seq
            _save_counter()
            logger.info(f"🔄 تمت مزامنة العدّاد مع العروض الموجودة: التسلسل = {max_seq}")


def parse_offer_id(offer_id: str) -> dict:
    """
    تحليل معرف عرض إلى مكوناته.
    يُعيد: {"prefix": "AFQ", "year": 2026, "sequence": 1} أو {}
    """
    try:
        parts = offer_id.split("-")
        if len(parts) >= 3 and parts[0] == PREFIX:
            return {
                "prefix": parts[0],
                "year": int(parts[1]),
                "sequence": int(parts[2]),
            }
    except (ValueError, IndexError):
        pass
    return {}
