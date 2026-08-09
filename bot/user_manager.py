#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة المستخدمين المتعددين
الأدوار: admin (مدير) و editor (محرر)
الحالات: active (نشط) و suspended (موقوف)

المميزات:
- تخزين Telegram User ID / الاسم / الإذن / الحالة / التاريخ
- أوامر: /add_user, /myid, /users, /remove_user
- سجل تدقيق (audit log) لكل العمليات الحساسة
- توافق مع النظام القديم (config.json admin_ids)
- البوت ليس عاماً — كل مستخدم يجب أن يكون مصرّحاً له
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.user_manager")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
AUDIT_FILE = DATA_DIR / "audit_log.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  الثوابت
# ============================================================
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
STATUS_ACTIVE = "active"
STATUS_SUSPENDED = "suspended"

# ============================================================
#  المخزن الداخلي
# ============================================================
_users = {}          # user_id (str) -> user dict
_audit_log = []      # list of audit entries
_lock = threading.Lock()
_initialized = False


# ============================================================
#  أدوات مساعدة
# ============================================================
def _atomic_write_json(file_path: Path, data):
    """كتابة JSON بشكل ذري"""
    try:
        tmp = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(file_path)
    except Exception as e:
        logger.error(f"خطأ في الكتابة الذرية لـ {file_path}: {e}")


def _safe_read_json(file_path: Path, default):
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
    """تهيئة النظام: تحميل المستخدمين وسجل التدقيق من القرص"""
    global _users, _audit_log, _initialized
    with _lock:
        if _initialized:
            return
        _users = _safe_read_json(USERS_FILE, {})
        audit_data = _safe_read_json(AUDIT_FILE, {"entries": []})
        _audit_log = audit_data.get("entries", [])
        _initialized = True
        logger.info(f"👥 تم تحميل {len(_users)} مستخدم و {len(_audit_log)} سجل تدقيق")


def init_from_config(config):
    """
    استيراد المدراء الموجودين من config.json (admin_ids).
    يحافظ على التوافق مع النظام القديم.
    """
    init()
    admin_ids = config.get("admin_ids", [])
    with _lock:
        for aid in admin_ids:
            uid = str(aid)
            if uid not in _users:
                _users[uid] = {
                    "user_id": uid,
                    "name": f"Admin {aid}",
                    "role": ROLE_ADMIN,
                    "status": STATUS_ACTIVE,
                    "added_by": "system (config.json)",
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_active": None,
                }
                logger.info(f"  ➕ تم استيراد مدير من config: {aid}")
        _atomic_write_json(USERS_FILE, _users)


def _save_users():
    """حفظ المستخدمين على القرص (داخلي)"""
    _atomic_write_json(USERS_FILE, _users)


def _save_audit():
    """حفظ سجل التدقيق على القرص (داخلي)"""
    # الاحتفاظ بآخر 500 سجل فقط
    if len(_audit_log) > 500:
        _audit_log[:] = _audit_log[-500:]
    _atomic_write_json(AUDIT_FILE, {"entries": _audit_log})


# ============================================================
#  إدارة المستخدمين
# ============================================================
def add_user(user_id, name, role=ROLE_EDITOR, added_by="system", status=STATUS_ACTIVE):
    """
    إضافة مستخدم جديد.
    role: 'admin' أو 'editor'
    """
    init()
    uid = str(user_id)
    with _lock:
        if uid in _users:
            # تحديث المستخدم الموجود
            _users[uid]["name"] = name
            _users[uid]["role"] = role
            _users[uid]["status"] = status
        else:
            _users[uid] = {
                "user_id": uid,
                "name": name,
                "role": role,
                "status": status,
                "added_by": str(added_by),
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_active": None,
            }
        _save_users()
    log_audit("add_user", added_by, f"أضاف مستخدم {uid} ({name}) بدور {role}")
    logger.info(f"➕ تم إضافة مستخدم: {uid} ({name}) — دور: {role}")
    return True


def remove_user(user_id, removed_by="system"):
    """حذف مستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        if uid not in _users:
            return False
        user_name = _users[uid].get("name", "غير معروف")
        del _users[uid]
        _save_users()
    log_audit("remove_user", removed_by, f"حذف مستخدم {uid} ({user_name})")
    logger.info(f"➖ تم حذف مستخدم: {uid}")
    return True


def suspend_user(user_id, suspended_by="system"):
    """إيقاف مستخدم مؤقتاً"""
    init()
    uid = str(user_id)
    with _lock:
        if uid not in _users:
            return False
        _users[uid]["status"] = STATUS_SUSPENDED
        _save_users()
    log_audit("suspend_user", suspended_by, f"أوقف مستخدم {uid}")
    return True


def activate_user(user_id, activated_by="system"):
    """تنشيط مستخدم موقوف"""
    init()
    uid = str(user_id)
    with _lock:
        if uid not in _users:
            return False
        _users[uid]["status"] = STATUS_ACTIVE
        _save_users()
    log_audit("activate_user", activated_by, f"نشّط مستخدم {uid}")
    return True


def get_user(user_id) -> dict:
    """جلب بيانات مستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        return _users.get(uid, None)


def get_all_users() -> list:
    """جلب جميع المستخدمين"""
    init()
    with _lock:
        return list(_users.values())


def get_active_users() -> list:
    """جلب المستخدمين النشطين فقط"""
    init()
    with _lock:
        return [u for u in _users.values() if u.get("status") == STATUS_ACTIVE]


# ============================================================
#  التحقق من الصلاحيات
# ============================================================
def get_user_role(user_id) -> str:
    """جلب دور المستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        user = _users.get(uid)
        if not user:
            return None
        if user.get("status") == STATUS_SUSPENDED:
            return None
        return user.get("role", ROLE_EDITOR)


def is_admin(user_id) -> bool:
    """التحقق إن كان المستخدم مديراً نشطاً"""
    return get_user_role(user_id) == ROLE_ADMIN


def is_editor(user_id) -> bool:
    """التحقق إن كان المستخدم محرراً أو مديراً (نشط)"""
    role = get_user_role(user_id)
    return role in (ROLE_EDITOR, ROLE_ADMIN)


def is_authorized(user_id) -> bool:
    """التحقق من الترخيص العام (admin أو editor)"""
    return is_editor(user_id)


def can_manage_users(user_id) -> bool:
    """التحقق إن كان المستخدم يمكنه إدارة المستخدمين (admin فقط)"""
    return is_admin(user_id)


def update_last_active(user_id):
    """تحديث آخر نشاط للمستخدم"""
    init()
    uid = str(user_id)
    with _lock:
        if uid in _users:
            _users[uid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _save_users()


# ============================================================
#  سجل التدقيق (Audit Log)
# ============================================================
def log_audit(action, performed_by, detail):
    """تسجيل عملية في سجل التدقيق"""
    init()
    with _lock:
        entry = {
            "action": action,
            "performed_by": str(performed_by),
            "detail": str(detail)[:500],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _audit_log.append(entry)
        _save_audit()


def get_recent_audit(limit=10) -> list:
    """جلب آخر سجلات التدقيق"""
    init()
    with _lock:
        return _audit_log[-limit:][::-1]


def get_audit_count() -> int:
    """عدد سجلات التدقيق"""
    init()
    with _lock:
        return len(_audit_log)


# ============================================================
#  إحصائيات
# ============================================================
def get_stats() -> dict:
    """إحصائيات المستخدمين للوحة التحكم"""
    init()
    with _lock:
        total = len(_users)
        admins = sum(1 for u in _users.values() if u.get("role") == ROLE_ADMIN)
        editors = sum(1 for u in _users.values() if u.get("role") == ROLE_EDITOR)
        active = sum(1 for u in _users.values() if u.get("status") == STATUS_ACTIVE)
        suspended = sum(1 for u in _users.values() if u.get("status") == STATUS_SUSPENDED)
        return {
            "total": total,
            "admins": admins,
            "editors": editors,
            "active": active,
            "suspended": suspended,
            "audit_count": len(_audit_log),
        }
