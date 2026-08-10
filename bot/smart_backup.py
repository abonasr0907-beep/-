#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام النسخ الاحتياطي الذكي — Phase 3 Smart Backup System

المميزات:
- إنشاء نسخة احتياطية مستقرة تلقائياً عند التحديث الناجح
- الاحتفاظ بآخر 5 نسخ مستقرة فقط
- عدم إنشاء نسخة احتياطية إذا لم يحدث تغيير حقيقي (مقارنة بالـ hash)
- عرض 5 نسخ مع التاريخ/رقم الإصدار/الملفات المتغيرة/الفرق
- اختيار أي نسخة وإعادة نشرها (redeploy)

يعمل جنباً إلى جنب مع backup.py الموجود دون تعديله.
"""

import json
import hashlib
import logging
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.smart_backup")

# ============================================================
# المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STABLE_BACKUPS_DIR = DATA_DIR / "stable_backups"
WEBSITE_DIR = BASE_DIR.parent

# الملفات المهمة للنسخ المستقر (نفس قائمة backup.py + bot.py)
STABLE_FILES = [
    "bot/bot.py",
    "bot/user_manager.py",
    "bot/config.json",
    "bot/backup.py",
    "bot/github_sync.py",
    "bot/persistence.py",
    "bot/task_queue.py",
    "bot/image_utils.py",
    "bot/offer_id.py",
    "bot/smart_backup.py",
    "bot/smart_sync.py",
    "bot/ai_monitor.py",
    "bot/smart_repair.py",
    "bot/emergency_protection.py",
    "offers-data/offers.json",
    "bot/data/bot_offers.json",
    "bot/data/visitor_requests.json",
    "bot/data/bids.json",
    "bot/data/users.json",
    "bot/data/audit_log.json",
    "offers-data/office-data.json",
    "offers-data/news.json",
]

MAX_STABLE_VERSIONS = 5
STABLE_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

# ملف سجل النسخ المستقرة
STABLE_INDEX_FILE = STABLE_BACKUPS_DIR / "stable_index.json"


# ============================================================
# دوال مساعدة
# ============================================================
def _compute_file_hash(file_path: Path) -> str:
    """حساب SHA-256 لملف"""
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def _compute_state_hash() -> str:
    """حساب hash شامل لحالة جميع الملفات المهمة"""
    h = hashlib.sha256()
    for rel_path in STABLE_FILES:
        fpath = WEBSITE_DIR / rel_path
        if fpath.exists():
            fh = _compute_file_hash(fpath)
            h.update(f"{rel_path}:{fh}\n".encode("utf-8"))
        else:
            h.update(f"{rel_path}:MISSING\n".encode("utf-8"))
    return h.hexdigest()


def _load_stable_index() -> dict:
    """تحميل فهرس النسخ المستقرة"""
    if STABLE_INDEX_FILE.exists():
        try:
            with open(STABLE_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"versions": [], "last_state_hash": ""}


def _save_stable_index(data: dict):
    """حفظ فهرس النسخ المستقرة"""
    try:
        STABLE_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STABLE_INDEX_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(STABLE_INDEX_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ فهرس النسخ المستقرة: {e}")


# ============================================================
# إنشاء نسخة احتياطية ذكية (فقط عند التغيير)
# ============================================================
def create_stable_backup(reason: str = "update", changed_files: list = None) -> dict:
    """
    إنشاء نسخة احتياطية مستقرة ذكية.
    - لا ينشئ نسخة إذا لم يحدث تغيير حقيقي (مقارنة hash)
    - يحتفظ بآخر 5 نسخ فقط

    يعيد dict:
      {"created": bool, "version": str, "reason": str, "message": str,
       "changed_files": list, "skipped": bool}
    """
    try:
        index = _load_stable_index()
        current_hash = _compute_state_hash()

        # التحقق من وجود تغيير
        if current_hash == index.get("last_state_hash", ""):
            logger.info("💾 لا توجد تغييرات حقيقية — تم تخطي إنشاء نسخة احتياطية")
            return {
                "created": False,
                "skipped": True,
                "reason": "no_change",
                "message": "لا توجد تغييرات حقيقية منذ آخر نسخة — تم تخطي النسخ الاحتياطي",
                "changed_files": [],
                "version": "",
            }

        # رقم الإصدار الجديد
        version_num = len(index.get("versions", [])) + 1
        # البحث عن أعلى رقم إصدار موجود
        existing_versions = index.get("versions", [])
        if existing_versions:
            version_num = max(v.get("version_number", 0) for v in existing_versions) + 1

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = f"v{version_num}_{timestamp}"
        backup_dir = STABLE_BACKUPS_DIR / version_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        # حساب hash لكل ملف وتحديد الملفات المتغيرة
        file_hashes = {}
        prev_hashes = {}
        if existing_versions:
            prev_hashes = existing_versions[-1].get("file_hashes", {})

        actually_changed = []
        copied = 0
        for rel_path in STABLE_FILES:
            fpath = WEBSITE_DIR / rel_path
            if fpath.exists():
                dst = backup_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(fpath), str(dst))
                copied += 1
                fh = _compute_file_hash(fpath)
                file_hashes[rel_path] = fh
                if prev_hashes.get(rel_path, "") != fh:
                    actually_changed.append(rel_path)
            else:
                file_hashes[rel_path] = "MISSING"

        # إذا تم تمرير قائمة changed_files، ندمجها
        if changed_files:
            for cf in changed_files:
                if cf not in actually_changed:
                    actually_changed.append(cf)

        # معلومات النسخة
        version_info = {
            "version_id": version_id,
            "version_number": version_num,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_sort": timestamp,
            "state_hash": current_hash,
            "files_copied": copied,
            "changed_files": actually_changed,
            "file_hashes": file_hashes,
        }

        # إضافة النسخة للفهرس
        versions = index.get("versions", [])
        versions.append(version_info)

        # الاحتفاظ بآخر 5 نسخ فقط
        if len(versions) > MAX_STABLE_VERSIONS:
            old_versions = versions[:-MAX_STABLE_VERSIONS]
            versions = versions[-MAX_STABLE_VERSIONS:]
            # حذف مجلدات النسخ القديمة
            for ov in old_versions:
                old_dir = STABLE_BACKUPS_DIR / ov["version_id"]
                if old_dir.exists():
                    shutil.rmtree(str(old_dir), ignore_errors=True)
                    logger.info(f"  🗑️ حذف نسخة قديمة: {ov['version_id']}")

        index["versions"] = versions
        index["last_state_hash"] = current_hash
        _save_stable_index(index)

        logger.info(f"💾 تم إنشاء نسخة مستقرة: {version_id} ({copied} ملف، {len(actually_changed)} متغير)")

        return {
            "created": True,
            "skipped": False,
            "version": version_id,
            "version_number": version_num,
            "reason": reason,
            "message": f"تم إنشاء نسخة احتياطية مستقرة رقم {version_num}",
            "changed_files": actually_changed,
            "files_copied": copied,
        }

    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء نسخة احتياطية مستقرة: {e}")
        return {
            "created": False,
            "skipped": False,
            "reason": "error",
            "message": f"خطأ: {e}",
            "changed_files": [],
            "version": "",
        }


# ============================================================
# سرد النسخ المستقرة (آخر 5)
# ============================================================
def list_stable_versions() -> list:
    """
    سرد آخر 5 نسخ مستقرة مع التفاصيل:
    - رقم الإصدار
    - التاريخ
    - الملفات المتغيرة
    - سبب النسخ
    """
    index = _load_stable_index()
    versions = index.get("versions", [])
    result = []
    for v in reversed(versions):  # الأحدث أولاً
        result.append({
            "version_id": v["version_id"],
            "version_number": v["version_number"],
            "reason": v["reason"],
            "timestamp": v["timestamp"],
            "files_copied": v.get("files_copied", 0),
            "changed_files": v.get("changed_files", []),
            "changed_count": len(v.get("changed_files", [])),
        })
    return result


# ============================================================
# عرض تفاصيل نسخة (مع الفرق)
# ============================================================
def get_version_details(version_id: str) -> dict:
    """
    عرض تفاصيل نسخة معينة مع الفرق عن النسخة السابقة.
    """
    index = _load_stable_index()
    versions = index.get("versions", [])

    target = None
    prev_version = None
    for i, v in enumerate(versions):
        if v["version_id"] == version_id:
            target = v
            if i > 0:
                prev_version = versions[i - 1]
            break

    if not target:
        return {"found": False, "message": f"النسخة {version_id} غير موجودة"}

    # حساب الفرق
    diffs = []
    prev_hashes = prev_version.get("file_hashes", {}) if prev_version else {}
    curr_hashes = target.get("file_hashes", {})

    all_files = set(list(prev_hashes.keys()) + list(curr_hashes.keys()))
    for fpath in sorted(all_files):
        prev_h = prev_hashes.get(fpath, "MISSING")
        curr_h = curr_hashes.get(fpath, "MISSING")
        if prev_h != curr_h:
            status = "added" if prev_h == "MISSING" else ("removed" if curr_h == "MISSING" else "modified")
            diffs.append({"file": fpath, "status": status})

    return {
        "found": True,
        "version_id": target["version_id"],
        "version_number": target["version_number"],
        "reason": target["reason"],
        "timestamp": target["timestamp"],
        "files_copied": target.get("files_copied", 0),
        "changed_files": target.get("changed_files", []),
        "diffs": diffs,
        "has_previous": prev_version is not None,
        "previous_version": prev_version["version_id"] if prev_version else None,
    }


# ============================================================
# إعادة نشر نسخة (Redeploy)
# ============================================================
def redeploy_version(version_id: str) -> dict:
    """
    إعادة نشر نسخة مستقرة — استعادة جميع الملفات من النسخة المحددة.
    ينشئ نسخة احتياطية للحالة الحالية أولاً قبل الاستعادة.
    """
    try:
        index = _load_stable_index()
        versions = index.get("versions", [])

        target = None
        for v in versions:
            if v["version_id"] == version_id:
                target = v
                break

        if not target:
            return {"success": False, "message": f"النسخة {version_id} غير موجودة"}

        backup_dir = STABLE_BACKUPS_DIR / version_id
        if not backup_dir.exists():
            return {"success": False, "message": f"مجلد النسخة {version_id} غير موجود"}

        # إنشاء نسخة احتياطية للحالة الحالية قبل الاستعادة
        pre_restore = create_stable_backup(reason="pre_redeploy")

        # استعادة الملفات
        restored = 0
        failed = 0
        for rel_path in STABLE_FILES:
            src = backup_dir / rel_path
            if src.exists():
                dst = WEBSITE_DIR / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(str(src), str(dst))
                    restored += 1
                except Exception as e:
                    logger.error(f"  ❌ فشل استعادة {rel_path}: {e}")
                    failed += 1

        logger.info(f"🔄 تم إعادة نشر النسخة {version_id} ({restored} ملف، {failed} فشل)")

        return {
            "success": True,
            "version_id": version_id,
            "version_number": target["version_number"],
            "restored_files": restored,
            "failed_files": failed,
            "pre_restore_backup": pre_restore.get("version", ""),
            "message": f"تم إعادة نشر النسخة {target['version_number']} — {restored} ملف مستعاد",
        }

    except Exception as e:
        logger.error(f"❌ خطأ في إعادة نشر النسخة: {e}")
        return {"success": False, "message": f"خطأ: {e}"}


# ============================================================
# التحقق من وجود نسخة
# ============================================================
def version_exists(version_id: str) -> bool:
    index = _load_stable_index()
    return any(v["version_id"] == version_id for v in index.get("versions", []))


def get_stable_count() -> int:
    index = _load_stable_index()
    return len(index.get("versions", []))


def get_latest_stable() -> dict:
    versions = list_stable_versions()
    return versions[0] if versions else None


# ============================================================
# فحص صحة النظام
# ============================================================
def health_check() -> dict:
    """فحص صحة نظام النسخ الاحتياطي الذكي"""
    index = _load_stable_index()
    versions = index.get("versions", [])
    return {
        "total_versions": len(versions),
        "max_versions": MAX_STABLE_VERSIONS,
        "last_state_hash": index.get("last_state_hash", "")[:16],
        "current_state_hash": _compute_state_hash()[:16],
        "has_changes": _compute_state_hash() != index.get("last_state_hash", ""),
        "backups_dir_exists": STABLE_BACKUPS_DIR.exists(),
    }
