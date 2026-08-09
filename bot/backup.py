#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام النسخ الاحتياطي التلقائي
ينشئ نسخة احتياطية قبل العمليات الكبيرة (نشر عرض، حذف، تحديث)

المميزات:
- نسخ احتياطي لجميع ملفات البيانات المهمة
- الاحتفاظ بآخر 20 نسخة فقط (حذف الأقدم تلقائياً)
- استعادة النسخ الاحتياطية
- سرد النسخ المتاحة
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.backup")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = DATA_DIR / "backups"
WEBSITE_DIR = BASE_DIR.parent  # الموقع العام (جذر المستودع)

# الملفات المهمة للنسخ الاحتياطي
FILES_TO_BACKUP = [
    "offers-data/offers.json",          # العروض المنشورة
    "bot/data/bot_offers.json",         # عروض البوت
    "bot/data/visitor_requests.json",   # طلبات الزوار
    "offers-data/office-data.json",     # بوصلة الأسعار
    "offers-data/news.json",            # الأخبار العقارية
    "offers-data/weekly_stats.json",    # إحصائيات أسبوعية
    "bot/data/users.json",              # المستخدمون
    "bot/data/sessions.json",           # الجلسات
    "bot/config.json",                  # إعدادات البوت
]

MAX_BACKUPS = 20  # أقصى عدد نسخ احتياطية

BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
#  إنشاء نسخة احتياطية
# ============================================================
def create_backup(reason: str = "manual") -> str:
    """
    إنشاء نسخة احتياطية.
    reason: سبب النسخ (publish, delete, update, manual, etc.)

    يُعيد مسار مجلد النسخة الاحتياطية أو None عند الفشل.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{reason}"
        backup_path = BACKUPS_DIR / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        copied = 0
        skipped = 0

        for rel_path in FILES_TO_BACKUP:
            src = WEBSITE_DIR / rel_path
            if src.exists():
                dst = backup_path / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                copied += 1
            else:
                skipped += 1

        # كتابة ملف معلومات النسخة
        info = {
            "backup_name": backup_name,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_copied": copied,
            "files_skipped": skipped,
        }
        with open(backup_path / "backup_info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 تم إنشاء نسخة احتياطية: {backup_name} ({copied} ملفات)")

        # تنظيف النسخ القديمة
        _cleanup_old_backups()

        return str(backup_path)

    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء نسخة احتياطية: {e}")
        return None


def _cleanup_old_backups():
    """حذف النسخ الاحتياطية القديمة (الاحتفاظ بـ MAX_BACKUPS فقط)"""
    try:
        backups = sorted(BACKUPS_DIR.iterdir(), key=lambda p: p.name, reverse=True)
        if len(backups) > MAX_BACKUPS:
            for old in backups[MAX_BACKUPS:]:
                shutil.rmtree(str(old), ignore_errors=True)
                logger.info(f"  🗑️ تم حذف نسخة احتياطية قديمة: {old.name}")
    except Exception as e:
        logger.warning(f"⚠️ خطأ في تنظيف النسخ القديمة: {e}")


# ============================================================
#  استعادة نسخة احتياطية
# ============================================================
def restore_backup(backup_name: str) -> bool:
    """
    استعادة نسخة احتياطية.
    backup_name: اسم مجلد النسخة (مثل backup_20260101_120000_publish)
    """
    try:
        backup_path = BACKUPS_DIR / backup_name
        if not backup_path.exists():
            logger.error(f"❌ النسخة الاحتياطية غير موجودة: {backup_name}")
            return False

        # إنشاء نسخة احتياطية للحالة الحالية قبل الاستعادة
        create_backup("pre_restore")

        restored = 0
        for rel_path in FILES_TO_BACKUP:
            src = backup_path / rel_path
            if src.exists():
                dst = WEBSITE_DIR / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                restored += 1

        logger.info(f"🔄 تم استعادة النسخة الاحتياطية: {backup_name} ({restored} ملفات)")
        return True

    except Exception as e:
        logger.error(f"❌ خطأ في استعادة النسخة الاحتياطية: {e}")
        return False


# ============================================================
#  سرد النسخ الاحتياطية
# ============================================================
def list_backups() -> list:
    """سرد جميع النسخ الاحتياطية المتاحة"""
    backups = []
    try:
        for d in sorted(BACKUPS_DIR.iterdir(), key=lambda p: p.name, reverse=True):
            if d.is_dir() and d.name.startswith("backup_"):
                info_file = d / "backup_info.json"
                info = {}
                if info_file.exists():
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            info = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        pass
                backups.append({
                    "name": d.name,
                    "reason": info.get("reason", "unknown"),
                    "timestamp": info.get("timestamp", d.name),
                    "files_copied": info.get("files_copied", 0),
                })
    except Exception as e:
        logger.error(f"خطأ في سرد النسخ الاحتياطية: {e}")
    return backups


def get_backup_count() -> int:
    """عدد النسخ الاحتياطية"""
    try:
        return len([d for d in BACKUPS_DIR.iterdir() if d.is_dir() and d.name.startswith("backup_")])
    except Exception:
        return 0


def get_latest_backup() -> dict:
    """آخر نسخة احتياطية"""
    backups = list_backups()
    return backups[0] if backups else None
