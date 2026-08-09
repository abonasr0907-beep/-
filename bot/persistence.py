#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الحفظ الدائم للجلسات والمسودات
يحلّ مشكلة فقدان حالة المستخدم عند إعادة تشغيل السيرفر / إعادة النشر

المميزات:
- حفظ جلسات المستخدمين على القرص (sessions.json)
- نظام مسودات: استئناف العرض غير المكتمل بعد الانقطاع
- كتابة ذرية (atomic write) لمنع تلف الملفات
- أمان خيطي (thread-safe) باستخدام threading.Lock
"""

import json
import os
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.persistence")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_FILE = DATA_DIR / "sessions.json"
DRAFTS_FILE = DATA_DIR / "drafts.json"

# التأكد من وجود المجلد
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  المخزن الداخلي (يُحمَّل من القرص عند التهيئة)
# ============================================================
_sessions = {}       # user_id (str) -> session dict
_drafts = {}         # user_id (str) -> draft dict
_lock = threading.Lock()
_initialized = False


# ============================================================
#  أدوات مساعدة للكتابة الذرية
# ============================================================
def _atomic_write_json(file_path: Path, data: dict):
    """كتابة JSON بشكل ذري: اكتب في ملف مؤقت ثم استبدل"""
    try:
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(file_path)
    except Exception as e:
        logger.error(f"خطأ في الكتابة الذرية لـ {file_path}: {e}")


def _safe_read_json(file_path: Path, default: dict) -> dict:
    """قراءة JSON بأمان مع قيمة افتراضية عند الفشل"""
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"خطأ في قراءة {file_path}: {e} — استخدام القيمة الافتراضية")
        return default


# ============================================================
#  التهيئة — تحميل البيانات من القرص
# ============================================================
def init():
    """تهيئة النظام: تحميل الجلسات والمسودات من القرص"""
    global _sessions, _drafts, _initialized
    with _lock:
        if _initialized:
            return
        _sessions = _safe_read_json(SESSIONS_FILE, {})
        _drafts = _safe_read_json(DRAFTS_FILE, {})
        _initialized = True
        logger.info(f"📦 تم تحميل {len(_sessions)} جلسة و {len(_drafts)} مسودة من القرص")


# ============================================================
#  دوال الجلسات
# ============================================================
def _new_session():
    """إنشاء جلسة جديدة فارغة"""
    return {
        "state": None,
        "offer": {},
        "images": [],
    }


def get_session(user_id) -> dict:
    """
    جلب جلسة مستخدم من الذاكرة الدائمة (تُحمَّل من القرص).
    تُنشئ جلسة جديدة إذا لم تكن موجودة.
    """
    init()
    uid = str(user_id)
    with _lock:
        if uid not in _sessions:
            _sessions[uid] = _new_session()
            _atomic_write_json(SESSIONS_FILE, _sessions)
        return _sessions[uid]


def save_session(user_id):
    """حفظ حالة الجلسة على القرص فوراً (بعد كل تغيير)"""
    init()
    uid = str(user_id)
    with _lock:
        if uid not in _sessions:
            return
        _atomic_write_json(SESSIONS_FILE, _sessions)
        # حفظ مسودة تلقائياً إذا كان العرض غير مكتمل
        sess = _sessions[uid]
        state = sess.get("state", "")
        if state and state.startswith("awaiting_") and sess.get("offer"):
            _auto_save_draft(uid, sess)


def reset_session(user_id):
    """إعادة تعيين جلسة مستخدم وحفظها على القرص"""
    init()
    uid = str(user_id)
    with _lock:
        _sessions[uid] = _new_session()
        _atomic_write_json(SESSIONS_FILE, _sessions)
        # حذف المسودة المرتبطة
        if uid in _drafts:
            del _drafts[uid]
            _atomic_write_json(DRAFTS_FILE, _drafts)


def update_session_state(user_id, new_state):
    """تحديث حالة الجلسة وحفظها على القرص"""
    init()
    uid = str(user_id)
    with _lock:
        if uid not in _sessions:
            _sessions[uid] = _new_session()
        _sessions[uid]["state"] = new_state
        _atomic_write_json(SESSIONS_FILE, _sessions)


# ============================================================
#  نظام المسودات
# ============================================================
def _auto_save_draft(user_id, session):
    """حفظ تلقائي للمسودة عند حفظ الجلسة (داخلي)"""
    _drafts[user_id] = {
        "session": session,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _atomic_write_json(DRAFTS_FILE, _drafts)


def save_draft(user_id, session):
    """حفظ عرض كمسودة (لاستئنافه لاحقاً)"""
    init()
    uid = str(user_id)
    with _lock:
        _drafts[uid] = {
            "session": session,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _atomic_write_json(DRAFTS_FILE, _drafts)
        logger.info(f"📝 تم حفظ مسودة للمستخدم {uid}")


def get_draft(user_id) -> dict:
    """جلب مسودة مستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        return _drafts.get(uid, None)


def has_incomplete_offer(user_id) -> bool:
    """التحقق من وجود مسودة غير مكتملة لمستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        draft = _drafts.get(uid)
        if not draft:
            return False
        sess = draft.get("session", {})
        state = sess.get("state", "")
        # المسودة تعتبر غير مكتملة إذا كانت الحالة في وضع إضافة
        return bool(state and state.startswith("awaiting_"))


def delete_draft(user_id):
    """حذف مسودة مستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        if uid in _drafts:
            del _drafts[uid]
            _atomic_write_json(DRAFTS_FILE, _drafts)


def restore_draft(user_id) -> dict:
    """
    استعادة مسودة وحمّلها في الجلسة الحالية.
    تُعيد الجلسة المستعادة أو None.
    """
    init()
    uid = str(user_id)
    with _lock:
        draft = _drafts.get(uid)
        if not draft:
            return None
        session = draft.get("session", _new_session())
        _sessions[uid] = session
        _atomic_write_json(SESSIONS_FILE, _sessions)
        # حذف المسودة بعد الاستعادة
        del _drafts[uid]
        _atomic_write_json(DRAFTS_FILE, _drafts)
        logger.info(f"🔄 تم استئناف مسودة للمستخدم {uid}")
        return session


# ============================================================
#  دوال مساعدة
# ============================================================
def get_active_sessions_count() -> int:
    """عدد الجلسات النشطة (في وضع إضافة عرض)"""
    init()
    with _lock:
        count = 0
        for sess in _sessions.values():
            state = sess.get("state", "")
            if state and state.startswith("awaiting_"):
                count += 1
        return count


def get_all_sessions() -> dict:
    """جلب جميع الجلسات (للعرض في لوحة التحكم)"""
    init()
    with _lock:
        return dict(_sessions)


def cleanup_old_drafts(max_age_hours: int = 72):
    """تنظيف المسودات القديمة (أقدم من max_age_hours ساعة)"""
    init()
    with _lock:
        now = datetime.now()
        to_remove = []
        for uid, draft in _drafts.items():
            saved_at = draft.get("saved_at", "")
            try:
                draft_time = datetime.strptime(saved_at, "%Y-%m-%d %H:%M:%S")
                if (now - draft_time).total_seconds() > max_age_hours * 3600:
                    to_remove.append(uid)
            except (ValueError, TypeError):
                continue
        for uid in to_remove:
            del _drafts[uid]
        if to_remove:
            _atomic_write_json(DRAFTS_FILE, _drafts)
            logger.info(f"🧹 تم تنظيف {len(to_remove)} مسودة قديمة")
