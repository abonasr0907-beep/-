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
import subprocess
import platform
import sys
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
    # Phase 4 files
    "bot/property_storage.py",
    "bot/publish_verifier.py",
    "bot/data/property_storage.json",
    "bot/data/publish_verification_log.json",
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
# Phase 4: دوال مساعدة لإعلامات النسخة (معرف commit, حالة النظام, الفرق)
# ============================================================
def _get_git_commit_id() -> str:
    """جلب معرف الـ commit الحالي من git"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"  تعذر جلب commit_id: {e}")
    return ""


def _get_git_commit_message(commit_id: str = "") -> str:
    """جلب رسالة الـ commit"""
    if not commit_id:
        return ""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s", commit_id],
            cwd=str(WEBSITE_DIR),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def _get_system_state() -> dict:
    """تجميع معلومات حالة النظام في وقت النسخ الاحتياطي"""
    state = {
        "python_version": sys.version.split()[0] if sys.version else "",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    # عد الملفات المهمة
    files_info = {}
    for rel_path in STABLE_FILES:
        fpath = WEBSITE_DIR / rel_path
        if fpath.exists():
            try:
                files_info[rel_path] = {
                    "exists": True,
                    "size_bytes": fpath.stat().st_size,
                }
            except Exception:
                files_info[rel_path] = {"exists": True, "size_bytes": 0}
        else:
            files_info[rel_path] = {"exists": False, "size_bytes": 0}
    state["files_info"] = files_info
    state["total_files_tracked"] = len(STABLE_FILES)
    state["existing_files"] = sum(1 for v in files_info.values() if v["exists"])
    return state


def _compute_diff_from_previous(current_hashes: dict, previous_hashes: dict) -> dict:
    """
    حساب الفرق بين النسخة الحالية والسابقة.
    يرجع: {added: [], removed: [], modified: []}
    """
    added = []
    removed = []
    modified = []

    current_files = set(current_hashes.keys())
    previous_files = set(previous_hashes.keys())

    for f in current_files - previous_files:
        if current_hashes.get(f, "") != "MISSING":
            added.append(f)

    for f in previous_files - current_files:
        removed.append(f)

    for f in current_files & previous_files:
        cur_h = current_hashes.get(f, "")
        prev_h = previous_hashes.get(f, "")
        if cur_h != prev_h and cur_h != "MISSING":
            modified.append(f)

    return {
        "added": sorted(added),
        "removed": sorted(removed),
        "modified": sorted(modified),
        "total_changes": len(added) + len(removed) + len(modified),
    }


def get_version_diff(version_id: str) -> dict:
    """
    عرض الفرق بين نسخة محددة والنسخة السابقة لها.
    يستخدم لعرض الفرق قبل الاستعادة (rollback).
    """
    try:
        index = _load_stable_index()
        versions = index.get("versions", [])

        target_idx = None
        for i, v in enumerate(versions):
            if v["version_id"] == version_id:
                target_idx = i
                break

        if target_idx is None:
            return {"success": False, "message": f"النسخة {version_id} غير موجودة"}

        target = versions[target_idx]

        # إذا كانت هذه أول نسخة لا يوجد نسخة سابقة
        if target_idx == 0:
            return {
                "success": True,
                "version_id": version_id,
                "version_number": target["version_number"],
                "has_previous": False,
                "diff": None,
                "message": f"النسخة {target['version_number']} هي أول نسخة — لا توجد نسخة سابقة للمقارنة",
            }

        previous = versions[target_idx - 1]
        diff = _compute_diff_from_previous(
            target.get("file_hashes", {}),
            previous.get("file_hashes", {}),
        )

        # أيضا مقارنة مع الحالة الحالية
        current_hashes = {}
        for rel_path in STABLE_FILES:
            fpath = WEBSITE_DIR / rel_path
            if fpath.exists():
                current_hashes[rel_path] = _compute_file_hash(fpath)
            else:
                current_hashes[rel_path] = "MISSING"

        diff_vs_current = _compute_diff_from_previous(
            current_hashes,
            target.get("file_hashes", {}),
        )

        return {
            "success": True,
            "version_id": version_id,
            "version_number": target["version_number"],
            "has_previous": True,
            "previous_version_id": previous["version_id"],
            "previous_version_number": previous["version_number"],
            "diff_from_previous": diff,
            "diff_vs_current": diff_vs_current,
            "target_changed_files": target.get("changed_files", []),
            "target_commit_id": target.get("commit_id", ""),
            "message": f"الفرق بين النسخة {target['version_number']} والسابقة {previous['version_number']}",
        }
    except Exception as e:
        logger.error(f"❌ خطأ في جلب الفرق: {e}")
        return {"success": False, "message": f"خطأ: {e}"}


def confirm_restore(version_id: str) -> dict:
    """
    تأكيد استعادة نسخة — يعرض الفرق ومعلومات النسخة قبل الاستعادة.
    تستخدم قبل redeploy_version لتأكيد المسؤول.
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

        diff_result = get_version_diff(version_id)

        return {
            "success": True,
            "version_id": version_id,
            "version_number": target["version_number"],
            "reason": target.get("reason", ""),
            "timestamp": target.get("timestamp", ""),
            "commit_id": target.get("commit_id", ""),
            "commit_message": target.get("commit_message", ""),
            "changed_files": target.get("changed_files", []),
            "diff_from_previous": diff_result.get("diff_from_previous"),
            "diff_vs_current": diff_result.get("diff_vs_current"),
            "files_copied": target.get("files_copied", 0),
            "system_state_summary": {
                "python_version": target.get("system_state", {}).get("python_version", ""),
                "platform": target.get("system_state", {}).get("platform", ""),
                "existing_files": target.get("system_state", {}).get("existing_files", 0),
            },
            "requires_confirmation": True,
            "message": f"تم تجهيز استعادة النسخة {target['version_number']} — يحتاج تأكيد المسؤول",
        }
    except Exception as e:
        return {"success": False, "message": f"خطأ: {e}"}


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
        commit_id = _get_git_commit_id()
        commit_msg = _get_git_commit_message(commit_id)
        system_state = _get_system_state()

        # حساب الفرق من النسخة السابقة
        diff_from_previous = None
        if existing_versions:
            diff_from_previous = _compute_diff_from_previous(file_hashes, prev_hashes)

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
            # Phase 4: معلومات إضافية
            "commit_id": commit_id,
            "commit_message": commit_msg,
            "system_state": system_state,
            "diff_from_previous": diff_from_previous,
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
        # Phase 4: إضافة معلومات commit وحالة النظام والفرق
        diff_info = v.get("diff_from_previous")
        result.append({
            "version_id": v["version_id"],
            "version_number": v["version_number"],
            "reason": v["reason"],
            "timestamp": v["timestamp"],
            "files_copied": v.get("files_copied", 0),
            "changed_files": v.get("changed_files", []),
            "changed_count": len(v.get("changed_files", [])),
            # Phase 4
            "commit_id": v.get("commit_id", "")[:12],
            "commit_message": v.get("commit_message", ""),
            "has_system_state": bool(v.get("system_state")),
            "diff_total_changes": diff_info.get("total_changes", 0) if diff_info else 0,
            "diff_added": len(diff_info.get("added", [])) if diff_info else 0,
            "diff_modified": len(diff_info.get("modified", [])) if diff_info else 0,
            "diff_removed": len(diff_info.get("removed", [])) if diff_info else 0,
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
def redeploy_version(version_id: str, admin_confirmed: bool = False) -> dict:
    """
    إعادة نشر نسخة مستقرة — استعادة جميع الملفات من النسخة المحددة.
    Phase 4: يتطلب تأكيد المسؤول، يعرض الفرق، ينفذ اختبار بعد الاستعادة.
    
    الدورة:
    1. اختيار نسخة مستقرة
    2. عرض الفرق (diff)
    3. تأكيد المسؤول (admin_confirmed=True)
    4. استعادة النسخة
    5. تشغيل الاختبارات (pre_deploy_check)
    6. تقرير نجاح/فشل
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

        # Phase 4: عرض الفرق قبل الاستعادة
        diff_result = get_version_diff(version_id)

        # Phase 4: يتطلب تأكيد المسؤول
        if not admin_confirmed:
            confirm_info = confirm_restore(version_id)
            return {
                "success": False,
                "requires_confirmation": True,
                "version_id": version_id,
                "version_number": target["version_number"],
                "diff_from_previous": diff_result.get("diff_from_previous"),
                "diff_vs_current": diff_result.get("diff_vs_current"),
                "changed_files": target.get("changed_files", []),
                "commit_id": target.get("commit_id", ""),
                "message": f"تتطلب إعادة نشر النسخة {target['version_number']} تأكيد المسؤول. استدع redeploy_version('{version_id}', admin_confirmed=True) للتأكيد.",
            }

        # إنشاء نسخة احتياطية للحالة الحالية قبل الاستعادة
        pre_restore = create_stable_backup(reason="pre_redeploy")

        # استعادة الملفات
        restored = 0
        failed = 0
        failed_files_list = []
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
                    failed_files_list.append(rel_path)

        logger.info(f"🔄 تم إعادة نشر النسخة {version_id} ({restored} ملف، {failed} فشل)")

        # Phase 4: تشغيل الاختبارات بعد الاستعادة
        test_result = None
        test_passed = False
        try:
            from ai_monitor import pre_deploy_check
            test_result = pre_deploy_check()
            test_passed = test_result.get("all_passed", False)
        except Exception as e:
            test_result = {"all_passed": False, "error": str(e)}
            test_passed = False

        # Phase 4: تقرير نجاح/فشل
        if test_passed and failed == 0:
            status = "success"
            message = f"تم إعادة نشر النسخة {target['version_number']} بنجاح — {restored} ملف مستعاد، الاختبارات نجحت"
        elif test_passed and failed > 0:
            status = "partial_success"
            message = f"تم استعادة النسخة {target['version_number']} — {restored} ملف، {failed} فشل. الاختبارات نجحت لكن بعض الملفات لم تُستعاد"
        else:
            status = "failed"
            message = f"فشل الاستعادة — النسخة {target['version_number']}. الاختبارات فشلت. تم إنشاء نسخة احتياطية {pre_restore.get('version', '')}"

        logger.info(f"  📋 حالة الاستعادة: {status}")

        return {
            "success": test_passed and failed == 0,
            "status": status,
            "version_id": version_id,
            "version_number": target["version_number"],
            "restored_files": restored,
            "failed_files": failed,
            "failed_files_list": failed_files_list,
            "pre_restore_backup": pre_restore.get("version", ""),
            "diff_from_previous": diff_result.get("diff_from_previous"),
            "test_result": test_result,
            "test_passed": test_passed,
            "message": message,
        }

    except Exception as e:
        logger.error(f"❌ خطأ في إعادة نشر النسخة: {e}")
        return {"success": False, "status": "error", "message": f"خطأ: {e}"}


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
    # Phase 4: معلومات إضافية
    latest_commit = ""
    if versions:
        latest_commit = versions[-1].get("commit_id", "")[:12]
    return {
        "total_versions": len(versions),
        "max_versions": MAX_STABLE_VERSIONS,
        "last_state_hash": index.get("last_state_hash", "")[:16],
        "current_state_hash": _compute_state_hash()[:16],
        "has_changes": _compute_state_hash() != index.get("last_state_hash", ""),
        "backups_dir_exists": STABLE_BACKUPS_DIR.exists(),
        # Phase 4
        "latest_version_commit": latest_commit,
        "latest_version_has_system_state": bool(versions and versions[-1].get("system_state")),
        "latest_version_has_diff": bool(versions and versions[-1].get("diff_from_previous")),
        "current_git_commit": _get_git_commit_id()[:12],
        "current_python_version": sys.version.split()[0] if sys.version else "",
    }
