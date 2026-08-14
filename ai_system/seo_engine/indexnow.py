#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indexnow.py — إرسال تنبيه فوري لمحركات البحث (IndexNow) للمرحلة الثالثة §2.6
===============================================================================
يوفّر:
  - توليد مفتاح IndexNow وحفظه في جذر الموقع
  - إرسال POST لمحركات البحث عند نشر/تحديث صفحة
  - تسجيل كل إرسال في سجل (log)

يدعم: Bing, Yandex, Seznam, naver (IndexNow API).
لا يتطلب مكتبات خارجية — يستخدم urllib فقط.

قواعد:
  - idempotent: إرسال نفس الرابط عدة مرات آمن
  - آمن: لا يُغيّر Tokens أو Webhook
  - يسجّل كل إرسال في bot/data/indexnow_log.json
"""

import json
import os
import re
import logging
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from urllib import request, error

logger = logging.getLogger("afaq.seo_engine.indexnow")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
KEY_PATH = BASE_DIR / "afaq_indexnow_key.txt"
KEY_URL_PATH = BASE_DIR / "afaq_indexnow_key.txt"  # نفس المفتاح في جذر الموقع
LOG_PATH = BASE_DIR / "bot" / "data" / "indexnow_log.json"

# محركات البحث المدعومة (IndexNow endpoints)
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/IndexNow",
    "https://www.bing.com/indexnow",
]

SITE_HOST = "abonasr0907-beep.github.io"
LEGACY_SITE_URL = "https://abonasr0907-beep.github.io/-/"


def get_or_create_key():
    """
    الحصول على مفتاح IndexNow أو إنشائه (idempotent).
    المفتاح يُحفظ في جذر الموقع كملف نصي عادي.
    """
    if KEY_PATH.exists():
        try:
            key = KEY_PATH.read_text(encoding="utf-8").strip()
            if key and len(key) >= 8 and len(key) <= 128:
                return key
        except Exception:
            pass

    # إنشاء مفتاح جديد (UUID-like بدون مكتبات)
    key = secrets.token_hex(16)  # 32 حرف
    try:
        KEY_PATH.write_text(key + "\n", encoding="utf-8")
        logger.info(f"تم إنشاء مفتاح IndexNow: {key}")
    except Exception as e:
        logger.error(f"تعذّر حفظ مفتاح IndexNow: {e}")
        return None

    return key


def submit_urls(urls, key=None):
    """
    إرسال قائمة روابط إلى IndexNow.
    urls: list of full URLs.
    key: مفتاح IndexNow (يُنشأ تلقائيًا إذا لم يُمرّر).
    idempotent: يمكن استدعاؤها عدة مرات بأمان.

    يُرجع: dict with 'submitted', 'succeeded', 'failed', 'results'
    """
    if not urls:
        return {"submitted": 0, "succeeded": 0, "failed": 0, "results": []}

    if not urls:
        return {"submitted": 0, "succeeded": 0, "failed": 0, "results": []}

    if key is None:
        key = get_or_create_key()
    if not key:
        return {"submitted": len(urls), "succeeded": 0, "failed": len(urls), "results": [{"error": "no key"}]}

    key_location = f"{LEGACY_SITE_URL}afaq_indexnow_key.txt"

    # بناء payload
    payload = {
        "host": SITE_HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }

    json_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    results = []
    succeeded = 0
    failed = 0

    for endpoint in INDEXNOW_ENDPOINTS:
        try:
            req = request.Request(
                endpoint,
                data=json_payload,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "AfaqAlInjaz-IndexNow/1.0",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=10) as resp:
                status = resp.getcode()
                results.append({
                    "endpoint": endpoint,
                    "status": status,
                    "ok": True,
                })
                succeeded += 1
                logger.info(f"IndexNow {endpoint}: HTTP {status} — تم إرسال {len(urls)} رابط")
                break  # نجح مع endpoint واحد، لا داعي للمحاولة مع الباقي
        except error.HTTPError as e:
            # 200, 202, 204 كلها تعني نجاح
            if e.code in (200, 202, 204):
                results.append({
                    "endpoint": endpoint,
                    "status": e.code,
                    "ok": True,
                })
                succeeded += 1
                logger.info(f"IndexNow {endpoint}: HTTP {e.code} — تم إرسال {len(urls)} رابط")
                break
            else:
                results.append({
                    "endpoint": endpoint,
                    "status": e.code,
                    "ok": False,
                    "error": str(e),
                })
                failed += 1
                logger.warning(f"IndexNow {endpoint}: HTTP {e.code}")
        except Exception as e:
            results.append({
                "endpoint": endpoint,
                "status": 0,
                "ok": False,
                "error": str(e),
            })
            failed += 1
            logger.warning(f"IndexNow {endpoint}: خطأ — {e}")

    # تسجيل في السجل
    _log_submission(urls, succeeded > 0, results)

    return {
        "submitted": len(urls),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


def submit_single_url(url, key=None):
    """
    إرسال رابط واحد إلى IndexNow.
    idempotent.
    """
    return submit_urls([url], key)


def submit_offer(offer, key=None):
    """
    إرسال رابط عرض منشور إلى IndexNow.
    idempotent.
    """
    offer_id = offer.get("id", "")
    if not offer_id:
        return {"submitted": 0, "succeeded": 0, "failed": 0, "results": []}

    slug = _slugify(offer.get("title", offer_id))
    url = f"{LEGACY_SITE_URL}offer/{offer_id}/{slug}"
    return submit_single_url(url, key)


def _log_submission(urls, success, results):
    """تسجيل إرسال IndexNow في السجل (add-only)."""
    try:
        log = []
        if LOG_PATH.exists():
            log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(log, list):
                log = []
    except Exception:
        log = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "urls": urls,
        "success": success,
        "results": results,
        "count": len(urls),
    }
    log.append(entry)

    # الحفاظ على آخر 200 إدخال فقط
    if len(log) > 200:
        log = log[-200:]

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"تعذّر حفظ سجل IndexNow: {e}")


def _slugify(text):
    """تحويل نص إلى slug آمن."""
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^\w\u0600-\u06FF-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower()


def get_log_summary():
    """تلخيص سجل إرسالات IndexNow."""
    try:
        if not LOG_PATH.exists():
            return {"total_submissions": 0, "total_urls": 0, "last_success": None}
        log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(log, list):
            return {"total_submissions": 0, "total_urls": 0, "last_success": None}
        total_urls = sum(e.get("count", 0) for e in log)
        successful = [e for e in log if e.get("success")]
        last_success = successful[-1]["timestamp"] if successful else None
        return {
            "total_submissions": len(log),
            "total_urls": total_urls,
            "successful": len(successful),
            "last_success": last_success,
        }
    except Exception:
        return {"total_submissions": 0, "total_urls": 0, "last_success": None}


# ============================================================
# اختبار ذاتي
# ============================================================
def _self_test():
    print("=== indexnow self-test ===")

    # إنشاء مفتاح
    key = get_or_create_key()
    assert key and len(key) >= 8, "Key creation failed"
    print(f"  Key created/loaded: {key[:8]}... — OK")

    # Idempotent: استدعاء ثاني يُرجع نفس المفتاح
    key2 = get_or_create_key()
    assert key == key2, "Key not idempotent"
    print("  Key idempotent — OK")

    # ملف المفتاح موجود
    assert KEY_PATH.exists(), "Key file missing"
    print("  Key file exists — OK")

    # بناء رابط عرض
    offer = {"id": "FRM-001", "title": "مزرعة في الرحمانية", "status": "published"}
    slug = _slugify(offer["title"])
    url = f"{LEGACY_SITE_URL}offer/FRM-001/{slug}"
    assert "offer/FRM-001/" in url, "URL build wrong"
    print(f"  Offer URL: {url} — OK")

    # محاولة إرسال (قد تفشل بسبب الشبكة لكن الدالة يجب ألا تتعثر)
    result = submit_single_url(url, key)
    assert "submitted" in result, "Submit result missing"
    assert "results" in result, "Submit result missing results"
    print(f"  Submit result: {result['submitted']} submitted, {result['succeeded']} succeeded — OK (network may fail in sandbox)")

    # سجل
    summary = get_log_summary()
    assert "total_submissions" in summary, "Log summary missing"
    print(f"  Log summary: {summary} — OK")

    print("=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    _self_test()
