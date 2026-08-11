#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مزامنة GitHub — رفع العروض والصور تلقائياً إلى المستودع
عند رفع أي ملف، تُعاد نشر GitHub Pages تلقائياً فتظهر الوسائط على الموقع العام.

يعتمد على متغير البيئة GITHUB_TOKEN (يُضبط في خدمة الاستضافة).
إن لم تكن موجودة، يعمل البوت بشكل محلي فقط (للتطوير).

التحسينات:
- إعادة المحاولة (retry) عند فشل الرفع (3 محاولات)
- مهلات أطول (timeouts) للتعامل مع الاتصال الضعيف
- سجل المزامنة (sync_log) للعرض في لوحة التحكم
- معالجة أخطاء أفضل
"""

import os
import base64
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_bot.github_sync")

# إعدادات المستودع
GITHUB_OWNER = "abonasr0907-beep"
GITHUB_REPO = "-"
GITHUB_BRANCH = "main"
GITHUB_API = "https://api.github.com"

# إعدادات إعادة المحاولة
MAX_RETRIES = 3
RETRY_DELAY = 2  # ثوانٍ
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 60

# مسار سجل المزامنة
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SYNC_LOG_FILE = DATA_DIR / "sync_log.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
#  سجل المزامنة
# ============================================================
def _load_sync_log():
    if SYNC_LOG_FILE.exists():
        try:
            with open(SYNC_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"syncs": []}


def _save_sync_log(data):
    try:
        if len(data["syncs"]) > 200:
            data["syncs"] = data["syncs"][-200:]
        tmp = SYNC_LOG_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(SYNC_LOG_FILE)
    except Exception as e:
        logger.error(f"خطأ في حفظ سجل المزامنة: {e}")


def log_sync(operation, status, detail=""):
    """تسجيل عملية مزامنة في السجل"""
    try:
        data = _load_sync_log()
        entry = {
            "operation": operation,
            "status": status,  # success, failed, skipped
            "detail": str(detail)[:300],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["syncs"].append(entry)
        _save_sync_log(data)
    except Exception:
        pass


def get_recent_syncs(limit=5):
    """جلب آخر عمليات المزامنة"""
    data = _load_sync_log()
    syncs = data.get("syncs", [])
    return syncs[-limit:][::-1]


# ============================================================
#  التوكن والإعدادات
# ============================================================
def _get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        # محاولة قراءة من ملف محلي اختياري
        try:
            tok_file = Path(__file__).resolve().parent / "github_token.txt"
            if tok_file.exists():
                token = tok_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return token


def is_enabled():
    return bool(_get_token())


def _headers():
    return {
        "Authorization": f"token {_get_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ============================================================
#  دوال مساعدة مع إعادة المحاولة
# ============================================================
def _retry_request(method, url, **kwargs):
    """
    تنفيذ طلب HTTP مع إعادة المحاولة.
    method: 'get' أو 'put'
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            kwargs.setdefault("timeout", (CONNECT_TIMEOUT, READ_TIMEOUT))
            r = getattr(requests, method)(url, **kwargs)
            return r
        except requests.exceptions.Timeout as e:
            last_error = f"انتهت المهلة (attempt {attempt+1}/{MAX_RETRIES})"
            logger.warning(f"github_sync: مهلة في الطلب ({attempt+1}/{MAX_RETRIES}): {e}")
        except requests.exceptions.ConnectionError as e:
            last_error = f"خطأ اتصال (attempt {attempt+1}/{MAX_RETRIES})"
            logger.warning(f"github_sync: خطأ اتصال ({attempt+1}/{MAX_RETRIES}): {e}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"github_sync: خطأ ({attempt+1}/{MAX_RETRIES}): {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    logger.error(f"github_sync: فشل بعد {MAX_RETRIES} محاولات: {last_error}")
    return None


def _get_file_sha(path_in_repo):
    """جلب sha لملف موجود (مطلوب للتحديث، وليس للإنشاء)."""
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path_in_repo}"
    r = _retry_request("get", url, headers=_headers(), params={"ref": GITHUB_BRANCH})
    if r and r.status_code == 200:
        return r.json().get("sha")
    return None


# ============================================================
#  رفع الملفات
# ============================================================
def upload_text_file(path_in_repo, text_content, commit_message):
    """رفع/تحديث ملف نصي (مثل offers.json) إلى المستودع."""
    token = _get_token()
    if not token:
        logger.info("github_sync: GITHUB_TOKEN غير مضبوط — تخطّي الرفع (وضع محلي)")
        log_sync(f"upload_text:{path_in_repo}", "skipped", "GITHUB_TOKEN غير مضبوط")
        return False
    try:
        sha = _get_file_sha(path_in_repo)
        payload = {
            "message": commit_message,
            "branch": GITHUB_BRANCH,
            "content": base64.b64encode(
                text_content.encode("utf-8")
            ).decode("ascii"),
        }
        if sha:
            payload["sha"] = sha
        url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path_in_repo}"
        r = _retry_request("put", url, headers=_headers(), json=payload)
        if r and r.status_code in (200, 201):
            logger.info(f"github_sync: تم رفع {path_in_repo} ✓ (sha={'update' if sha else 'new'})")
            log_sync(f"upload_text:{path_in_repo}", "success")
            return True
        status = r.status_code if r else "no_response"
        err_text = r.text[:200] if r else last_error if 'last_error' in dir() else "unknown"
        logger.error(f"github_sync: فشل رفع {path_in_repo}: {status} {err_text}")
        log_sync(f"upload_text:{path_in_repo}", "failed", f"{status}: {err_text}")
        return False
    except Exception as e:
        logger.error(f"github_sync: استثناء عند رفع {path_in_repo}: {e}")
        log_sync(f"upload_text:{path_in_repo}", "failed", str(e))
        return False


def upload_binary_file(path_in_repo, file_path, commit_message):
    """رفع ملف ثنائي (صورة) إلى المستودع."""
    token = _get_token()
    if not token:
        logger.info("github_sync: GITHUB_TOKEN غير مضبوط — تخطّي رفع الصورة (وضع محلي)")
        log_sync(f"upload_image:{path_in_repo}", "skipped", "GITHUB_TOKEN غير مضبوط")
        return False
    try:
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("ascii")
        sha = _get_file_sha(path_in_repo)
        payload = {
            "message": commit_message,
            "branch": GITHUB_BRANCH,
            "content": content,
        }
        if sha:
            payload["sha"] = sha
        url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path_in_repo}"
        r = _retry_request("put", url, headers=_headers(), json=payload)
        if r and r.status_code in (200, 201):
            logger.info(f"github_sync: تم رفع الصورة {path_in_repo} ✓")
            log_sync(f"upload_image:{path_in_repo}", "success")
            return True
        status = r.status_code if r else "no_response"
        err_text = r.text[:200] if r else "unknown"
        logger.error(f"github_sync: فشل رفع الصورة {path_in_repo}: {status} {err_text}")
        log_sync(f"upload_image:{path_in_repo}", "failed", f"{status}: {err_text}")
        return False
    except Exception as e:
        logger.error(f"github_sync: استثناء عند رفع الصورة {path_in_repo}: {e}")
        log_sync(f"upload_image:{path_in_repo}", "failed", str(e))
        return False


# ============================================================
#  مزامنة الملفات الخاصة
# ============================================================
def sync_office_data_to_github():
    """مزامنة ملف بوصلة الأسعار (office-data.json) إلى GitHub."""
    token = _get_token()
    if not token:
        logger.info("github_sync: GITHUB_TOKEN غير مضبوط — تخطّي مزامنة البوصلة")
        log_sync("office_data", "skipped", "GITHUB_TOKEN غير مضبوط")
        return False
    try:
        base = Path(__file__).resolve().parent
        office_file = base.parent / "offers-data" / "office-data.json"
        if not office_file.exists():
            logger.warning("github_sync: office-data.json غير موجود محلياً")
            log_sync("office_data", "failed", "الملف غير موجود")
            return False
        text = office_file.read_text(encoding="utf-8")
        ok = upload_text_file(
            "offers-data/office-data.json",
            text,
            "🧭 تحديث تلقائي لبوصلة الأسعار العقارية"
        )
        if ok:
            logger.info("github_sync: تمت مزامنة بوصلة الأسعار إلى GitHub ✓")
        return ok
    except Exception as e:
        logger.error(f"github_sync: فشل مزامنة office-data.json: {e}")
        log_sync("office_data", "failed", str(e))
        return False


def sync_news_to_github():
    """مزامنة ملف الأخبار العقارية (news.json) إلى GitHub."""
    token = _get_token()
    if not token:
        logger.info("github_sync: GITHUB_TOKEN غير مضبوط — تخطّي مزامنة الأخبار")
        log_sync("news", "skipped", "GITHUB_TOKEN غير مضبوط")
        return False
    try:
        base = Path(__file__).resolve().parent
        news_file = base.parent / "offers-data" / "news.json"
        if not news_file.exists():
            logger.warning("github_sync: news.json غير موجود محلياً")
            log_sync("news", "failed", "الملف غير موجود")
            return False
        text = news_file.read_text(encoding="utf-8")
        ok = upload_text_file(
            "offers-data/news.json",
            text,
            "🗞️ تحديث تلقائي للأخبار العقارية"
        )
        if ok:
            logger.info("github_sync: تمت مزامنة الأخبار إلى GitHub ✓")
        return ok
    except Exception as e:
        logger.error(f"github_sync: فشل مزامنة news.json: {e}")
        log_sync("news", "failed", str(e))
        return False


def sync_offer_to_github(offer, local_image_paths):
    """
    رفع عرض جديد بالكامل: الصور + offers.json.
    local_image_paths: قائمة المسارات المحلية الكاملة للصور.
    """
    offer_id = offer.get("id", "")
    offer_category = offer.get("category", "")
    offer_area = offer.get("area", "")

    # 1) رفع الصور
    images_uploaded = 0
    images_failed = 0
    for local_path, rel_repo_path in local_image_paths:
        ok = upload_binary_file(
            rel_repo_path,
            local_path,
            f"صورة عرض جديد: {offer_id} ({offer_category})"
        )
        if ok:
            images_uploaded += 1
        else:
            images_failed += 1

    # 2) رفع offers.json
    try:
        base = Path(__file__).resolve().parent
        offers_file = base.parent / "offers-data" / "offers.json"
        if offers_file.exists():
            text = offers_file.read_text(encoding="utf-8")
            ok = upload_text_file(
                "offers-data/offers.json",
                text,
                f"عرض جديد: {offer_id} — {offer_category} — {offer_area}"
            )
            log_sync(
                f"offer:{offer_id}",
                "success" if ok else "partial",
                f"صور: {images_uploaded} نجحت, {images_failed} فشلت"
            )
            return ok and images_failed == 0
        else:
            log_sync(f"offer:{offer_id}", "failed", "offers.json غير موجود")
            return False
    except Exception as e:
        logger.error(f"github_sync: فشل مزامنة offers.json: {e}")
        log_sync(f"offer:{offer_id}", "failed", str(e))
        return False


# ============================================================
#  جلب صور طلبات الزوار من GitHub (Phase 4)
# ============================================================
def fetch_visitor_request_images(request_id):
    """
    جلب مسارات صور طلب زائر من visitor_requests.json على GitHub.
    يُرجع قائمة بمسارات الصور (relative paths) مثل images/visitor/REQ-xxx/img_0_xxx.jpg
    """
    if not is_enabled():
        return []
    try:
        url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/bot/data/visitor_requests.json"
        r = _retry_request("get", url, headers=_headers(), params={"ref": GITHUB_BRANCH})
        if r and r.status_code == 200:
            import base64 as _b64
            data = r.json()
            content_text = _b64.b64decode(data.get("content", "")).decode("utf-8")
            vdata = json.loads(content_text)
            # البحث في requests و inquiries
            for section in ("requests", "inquiries", "offer_submissions"):
                for item in vdata.get(section, []):
                    if item.get("id") == request_id:
                        imgs = item.get("images", [])
                        if imgs:
                            return imgs
        return []
    except Exception as e:
        logger.error(f"github_sync: فشل جلب صور الطلب {request_id}: {e}")
        return []


def download_visitor_image(repo_path, local_dir):
    """
    تنزيل صورة من GitHub إلى المسار المحلي.
    repo_path: مسار الصورة في المستودع (مثل images/visitor/REQ-xxx/img.jpg)
    local_dir: المجلد الأساسي للموقع (Path)
    يُرجع المسار النسبي للصورة محلياً أو None عند الفشل.
    """
    if not is_enabled():
        return None
    try:
        url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{repo_path}"
        r = _retry_request("get", url, headers=_headers(), params={"ref": GITHUB_BRANCH})
        if r and r.status_code == 200:
            import base64 as _b64
            data = r.json()
            if data.get("encoding") == "base64" or data.get("content"):
                img_bytes = _b64.b64decode(data.get("content", ""))
                # تحديد المسار المحلي: نُخزّن الصور في images/visitor/ محلياً
                local_full = local_dir / repo_path
                local_full.parent.mkdir(parents=True, exist_ok=True)
                local_full.write_bytes(img_bytes)
                return repo_path
        # محاولة تنزيل عبر raw URL
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{repo_path}"
        r2 = _retry_request("get", raw_url, headers=_headers())
        if r2 and r2.status_code == 200:
            local_full = local_dir / repo_path
            local_full.parent.mkdir(parents=True, exist_ok=True)
            local_full.write_bytes(r2.content)
            return repo_path
        return None
    except Exception as e:
        logger.error(f"github_sync: فشل تنزيل الصورة {repo_path}: {e}")
        return None
