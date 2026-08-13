#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة المستخدمين المتعددين
الأدوار: admin (مدير) و reviewer (مراجع طلبات) و publisher (ناشر فقط) و editor (محرر)
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
#  الثوابت — الأدوار الثلاثة المطلوبة
# ============================================================
# مدير كامل (admin): كل الصلاحيات
ROLE_ADMIN = "admin"
# مراجع طلبات (reviewer): مراجعة الطلبات/العروض والموافقة/الرفض فقط
ROLE_REVIEWER = "reviewer"
# ناشر فقط (publisher): إضافة ونشر العروض فقط (لا إدارة مدراء، لا حذف)
ROLE_PUBLISHER = "publisher"
# توافق مع الإصدارات القديمة (editor = publisher فعلياً)
ROLE_EDITOR = "editor"
# ── أدوار جديدة (Phase: Bot & Listing Lifecycle) ──
# المالك (owner): كل الصلاحيات بما فيها إدارة المدراء وتغيير الإعدادات الحساسة
ROLE_OWNER = "owner"
# مدير (manager): إضافة/تعديل/نشر/رفض/أرشفة عقار، اعتماد عروض الزوار والموقع،
#   تعديل النص، إضافة نص تسويقي، عرض روابط العقارات، استقبال إشعارات الطلبات.
#   لا يمكنه تغيير Tokens/Webhook/Data/الإعدادات الحساسة.
ROLE_MANAGER = "manager"
# زائر (visitor): مستخدم عادي يقدم عروضاً (status=pending) — لا صلاحيات إدارية
ROLE_VISITOR = "visitor"

STATUS_ACTIVE = "active"
STATUS_SUSPENDED = "suspended"

# الأدوار الإدارية (لها صلاحيات على البوت). visitor ليس إدارياً.
STAFF_ROLES = (ROLE_OWNER, ROLE_ADMIN, ROLE_MANAGER, ROLE_REVIEWER, ROLE_PUBLISHER, ROLE_EDITOR)
# من يمكنه إضافة/إزالة المدراء: owner و admin فقط
MANAGER_MANAGE_ROLES = (ROLE_OWNER, ROLE_ADMIN)

# خريطة الصلاحيات حسب الدور
# manage_users: إدارة المدراء (admin فقط)
# review_requests: مراجعة الطلبات والموافقة/الرفض (admin, reviewer)
# publish_offers: إضافة ونشر العروض (admin, publisher, editor)
# delete_offers: حذف العروض (admin فقط)
# view_archive: عرض الأرشيف (admin, reviewer, publisher, editor)
# edit_settings: تعديل الإعدادات (admin فقط)
_ROLE_PERMISSIONS = {
    # المالك: كل الصلاحيات + إدارة المدراء + الإعدادات الحساسة
    ROLE_OWNER: {
        "manage_users": True,
        "manage_managers": True,
        "review_requests": True,
        "publish_offers": True,
        "delete_offers": True,
        "view_archive": True,
        "edit_settings": True,
        # صلاحيات المدير الكاملة
        "add_listing": True,
        "edit_listing": True,
        "publish_listing": True,
        "reject_listing": True,
        "archive_listing": True,
        "approve_visitor_offer": True,
        "approve_site_offer": True,
        "edit_text_before_publish": True,
        "add_marketing_text": True,
        "view_listing_links": True,
        "receive_request_notifications": True,
    },
    ROLE_ADMIN: {
        "manage_users": True,
        "manage_managers": True,
        "review_requests": True,
        "publish_offers": True,
        "delete_offers": True,
        "view_archive": True,
        "edit_settings": True,
        # صلاحيات المدير الكاملة
        "add_listing": True,
        "edit_listing": True,
        "publish_listing": True,
        "reject_listing": True,
        "archive_listing": True,
        "approve_visitor_offer": True,
        "approve_site_offer": True,
        "edit_text_before_publish": True,
        "add_marketing_text": True,
        "view_listing_links": True,
        "receive_request_notifications": True,
    },
    # مدير (manager): صلاحيات النشر والاعتماد والتعديل بدون الإعدادات الحساسة
    ROLE_MANAGER: {
        "manage_users": False,
        "manage_managers": False,
        "review_requests": True,
        "publish_offers": True,
        "delete_offers": False,
        "view_archive": True,
        "edit_settings": False,  # لا يمكن تغيير Tokens/Webhook/Data
        "add_listing": True,
        "edit_listing": True,
        "publish_listing": True,
        "reject_listing": True,
        "archive_listing": True,
        "approve_visitor_offer": True,
        "approve_site_offer": True,
        "edit_text_before_publish": True,
        "add_marketing_text": True,
        "view_listing_links": True,
        "receive_request_notifications": True,
    },
    ROLE_REVIEWER: {
        "manage_users": False,
        "manage_managers": False,
        "review_requests": True,
        "publish_offers": False,
        "delete_offers": False,
        "view_archive": True,
        "edit_settings": False,
        "add_listing": False,
        "edit_listing": False,
        "publish_listing": False,
        "reject_listing": True,
        "archive_listing": False,
        "approve_visitor_offer": True,
        "approve_site_offer": True,
        "edit_text_before_publish": True,
        "add_marketing_text": True,
        "view_listing_links": True,
        "receive_request_notifications": True,
    },
    ROLE_PUBLISHER: {
        "manage_users": False,
        "manage_managers": False,
        "review_requests": False,
        "publish_offers": True,
        "delete_offers": False,
        "view_archive": True,
        "edit_settings": False,
        "add_listing": True,
        "edit_listing": True,
        "publish_listing": True,
        "reject_listing": False,
        "archive_listing": False,
        "approve_visitor_offer": False,
        "approve_site_offer": False,
        "edit_text_before_publish": True,
        "add_marketing_text": True,
        "view_listing_links": True,
        "receive_request_notifications": False,
    },
    # توافق مع الإصدارات القديمة (editor = publisher + review)
    ROLE_EDITOR: {
        "manage_users": False,
        "manage_managers": False,
        "review_requests": True,
        "publish_offers": True,
        "delete_offers": False,
        "view_archive": True,
        "edit_settings": False,
        "add_listing": True,
        "edit_listing": True,
        "publish_listing": True,
        "reject_listing": True,
        "archive_listing": False,
        "approve_visitor_offer": True,
        "approve_site_offer": True,
        "edit_text_before_publish": True,
        "add_marketing_text": True,
        "view_listing_links": True,
        "receive_request_notifications": True,
    },
    # الزائر: لا صلاحيات إدارية على الإطلاق
    ROLE_VISITOR: {
        "manage_users": False,
        "manage_managers": False,
        "review_requests": False,
        "publish_offers": False,
        "delete_offers": False,
        "view_archive": False,
        "edit_settings": False,
        "add_listing": False,
        "edit_listing": False,
        "publish_listing": False,
        "reject_listing": False,
        "archive_listing": False,
        "approve_visitor_offer": False,
        "approve_site_offer": False,
        "edit_text_before_publish": False,
        "add_marketing_text": False,
        "view_listing_links": False,
        "receive_request_notifications": False,
    },
}

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
    """
    التحقق إن كان المستخدم مديراً نشطاً (admin أو owner — owner له كل صلاحيات admin).
    """
    return get_user_role(user_id) in (ROLE_ADMIN, ROLE_OWNER)


def is_owner(user_id) -> bool:
    """التحقق إن كان المستخدم المالك (owner)."""
    return get_user_role(user_id) == ROLE_OWNER


def is_manager(user_id) -> bool:
    """التحقق إن كان المستخدم مديراً (manager)."""
    return get_user_role(user_id) == ROLE_MANAGER


def can_manage_managers(user_id) -> bool:
    """من يستطيع إضافة/إزالة المدراء: owner و admin فقط."""
    return get_user_role(user_id) in MANAGER_MANAGE_ROLES


def is_editor(user_id) -> bool:
    """Check if user is editor/publisher/admin/owner/manager (active) -- backwards compat"""
    role = get_user_role(user_id)
    return role in (ROLE_EDITOR, ROLE_PUBLISHER, ROLE_ADMIN, ROLE_OWNER, ROLE_MANAGER)


def is_authorized(user_id) -> bool:
    """General authorization check (any active staff role: owner, admin, manager, reviewer, publisher, editor).
    visitor is NOT authorized for bot admin commands."""
    role = get_user_role(user_id)
    return role in (ROLE_OWNER, ROLE_ADMIN, ROLE_MANAGER, ROLE_REVIEWER, ROLE_PUBLISHER, ROLE_EDITOR)


def can_manage_users(user_id) -> bool:
    """Check if user can manage users (admin or owner only)"""
    return is_admin(user_id)


# ============================================================
#  Permission functions (3-role RBAC)
# ============================================================
def has_permission(user_id, permission: str) -> bool:
    """Check if user has a specific permission based on their role."""
    role = get_user_role(user_id)
    if role is None:
        return False
    perms = _ROLE_PERMISSIONS.get(role, {})
    return perms.get(permission, False)


def can_review_requests(user_id) -> bool:
    """Can review/approve/reject visitor requests and offers (admin, reviewer, editor)."""
    return has_permission(user_id, "review_requests")


def can_publish_offers(user_id) -> bool:
    """Can add and publish offers (admin, publisher, editor)."""
    return has_permission(user_id, "publish_offers")


def can_delete_offers(user_id) -> bool:
    """Can delete offers (admin only)."""
    return has_permission(user_id, "delete_offers")


def can_view_archive(user_id) -> bool:
    """Can view the archive (admin, reviewer, publisher, editor)."""
    return has_permission(user_id, "view_archive")


def can_edit_settings(user_id) -> bool:
    """Can edit settings (admin only)."""
    return has_permission(user_id, "edit_settings")

# ============================================================
#  Listing lifecycle permission helpers (Phase: Bot & Listing Lifecycle)
# ============================================================
def can_add_listing(user_id) -> bool:
    """Can add a property listing (owner, admin, manager, publisher, editor)."""
    return has_permission(user_id, "add_listing")


def can_edit_listing(user_id) -> bool:
    """Can edit a property listing (owner, admin, manager, publisher, editor)."""
    return has_permission(user_id, "edit_listing")


def can_publish_listing(user_id) -> bool:
    """Can publish a listing directly without approval (owner, admin, manager, publisher, editor)."""
    return has_permission(user_id, "publish_listing")


def can_reject_listing(user_id) -> bool:
    """Can reject a pending listing (owner, admin, manager, reviewer, editor)."""
    return has_permission(user_id, "reject_listing")


def can_archive_listing(user_id) -> bool:
    """Can archive a listing (owner, admin, manager)."""
    return has_permission(user_id, "archive_listing")


def can_approve_visitor_offer(user_id) -> bool:
    """Can approve visitor offers coming from the bot (owner, admin, manager, reviewer, editor)."""
    return has_permission(user_id, "approve_visitor_offer")


def can_approve_site_offer(user_id) -> bool:
    """Can approve offers submitted from the website (owner, admin, manager, reviewer, editor)."""
    return has_permission(user_id, "approve_site_offer")


def can_edit_text_before_publish(user_id) -> bool:
    """Can edit listing text before publishing (owner, admin, manager, reviewer, publisher, editor)."""
    return has_permission(user_id, "edit_text_before_publish")


def can_add_marketing_text(user_id) -> bool:
    """Can add marketing text before publishing."""
    return has_permission(user_id, "add_marketing_text")


def can_view_listing_links(user_id) -> bool:
    """Can view listing permanent links (all staff)."""
    return has_permission(user_id, "view_listing_links")


def should_receive_request_notifications(user_id) -> bool:
    """Should receive notifications about new pending requests (owner, admin, manager, reviewer, editor)."""
    return has_permission(user_id, "receive_request_notifications")


def get_managers() -> list:
    """Get all active managers (role=manager)."""
    init()
    with _lock:
        return [u for u in _users.values() if isinstance(u, dict) and u.get("role") == ROLE_MANAGER and u.get("status") == STATUS_ACTIVE]


def get_staff_for_notifications() -> list:
    """Get all active staff who should receive request notifications (for pending visitor/site offers)."""
    init()
    with _lock:
        result = []
        for u in _users.values():
            if not isinstance(u, dict):
                continue
            if u.get("status") != STATUS_ACTIVE:
                continue
            role = u.get("role")
            if role in (ROLE_OWNER, ROLE_ADMIN, ROLE_MANAGER, ROLE_REVIEWER, ROLE_EDITOR):
                result.append(u)
        return result



def get_user_permissions(user_id) -> dict:
    """Get all permissions for a user based on their role."""
    role = get_user_role(user_id)
    if role is None:
        return {}
    return dict(_ROLE_PERMISSIONS.get(role, {}))


def change_role(user_id, new_role, changed_by="system") -> bool:
    """Change a user's role. Validates the new role against known roles."""
    init()
    valid_roles = (ROLE_OWNER, ROLE_ADMIN, ROLE_MANAGER, ROLE_REVIEWER, ROLE_PUBLISHER, ROLE_EDITOR, ROLE_VISITOR)
    if new_role not in valid_roles:
        logger.warning(f"Invalid role: {new_role}")
        return False
    uid = str(user_id)
    with _lock:
        if uid not in _users:
            return False
        old_role = _users[uid].get("role", "unknown")
        _users[uid]["role"] = new_role
        _save_users()
    log_audit("change_role", changed_by, f"Changed role of {uid} from {old_role} to {new_role}")
    logger.info(f"Changed role of {uid}: {old_role} -> {new_role}")
    return True


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
        # Filter to only dict entries (skip legacy keys like "users" list)
        _ulist = [u for u in _users.values() if isinstance(u, dict)]
        total = len(_ulist)
        admins = sum(1 for u in _ulist if u.get("role") == ROLE_ADMIN)
        owners = sum(1 for u in _ulist if u.get("role") == ROLE_OWNER)
        managers = sum(1 for u in _ulist if u.get("role") == ROLE_MANAGER)
        reviewers = sum(1 for u in _ulist if u.get("role") == ROLE_REVIEWER)
        publishers = sum(1 for u in _ulist if u.get("role") == ROLE_PUBLISHER)
        editors = sum(1 for u in _ulist if u.get("role") == ROLE_EDITOR)
        visitors = sum(1 for u in _ulist if u.get("role") == ROLE_VISITOR)
        active = sum(1 for u in _ulist if u.get("status") == STATUS_ACTIVE)
        suspended = sum(1 for u in _ulist if u.get("status") == STATUS_SUSPENDED)
        return {
            "total": total,
            "owners": owners,
            "admins": admins,
            "managers": managers,
            "reviewers": reviewers,
            "publishers": publishers,
            "editors": editors,
            "visitors": visitors,
            "active": active,
            "suspended": suspended,
            "audit_count": len(_audit_log),
        }
