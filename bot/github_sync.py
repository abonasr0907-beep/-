#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مزامنة GitHub — رفع العروض والصور تلقائياً إلى المستودع
عند رفع أي ملف، يُعاد نشر GitHub Pages تلقائياً فتظهر الوسائط على الموقع العام.

يعتمد على متغير البيئة GITHUB_TOKEN (يُضبط في خدمة الاستضافة).
إن لم يكن موجوداً، يعمل البوت بشكل محلي فقط (للتطوير).
"""
import os
import base64
import json
import logging
import requests

logger = logging.getLogger("afaq_bot.github_sync")

# إعدادات المستودع
GITHUB_OWNER = "abonasr0907-beep"
GITHUB_REPO = "-"
GITHUB_BRANCH = "main"
GITHUB_API = "https://api.github.com"

# جلب التوكن من البيئة (أو من ملف اختياري للتشغيل المحلي)
def _get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        # محاولة قراءة من ملف محلي اختياري
        try:
            from pathlib import Path
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


def _get_file_sha(path_in_repo):
    """جلب sha لملف موجود (مطلوب للتحديث، وليس للإنشاء)."""
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path_in_repo}"
    r = requests.get(url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=20)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def upload_text_file(path_in_repo, text_content, commit_message):
    """رفع/تحديث ملف نصي (مثل offers.json) إلى المستودع."""
    token = _get_token()
    if not token:
        logger.info("github_sync: GITHUB_TOKEN غير مضبوط — تخطّي الرفع (وضع محلي)")
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
        r = requests.put(url, headers=_headers(), json=payload, timeout=30)
        if r.status_code in (200, 201):
            logger.info(f"github_sync: تم رفع {path_in_repo} ✓ (sha={'update' if sha else 'new'})")
            return True
        logger.error(f"github_sync: فشل رفع {path_in_repo}: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"github_sync: استثناء عند رفع {path_in_repo}: {e}")
        return False


def upload_binary_file(path_in_repo, file_path, commit_message):
    """رفع ملف ثنائي (صورة) إلى المستودع."""
    token = _get_token()
    if not token:
        logger.info("github_sync: GITHUB_TOKEN غير مضبوط — تخطّي رفع الصورة (وضع محلي)")
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
        r = requests.put(url, headers=_headers(), json=payload, timeout=60)
        if r.status_code in (200, 201):
            logger.info(f"github_sync: تم رفع الصورة {path_in_repo} ✓")
            return True
        logger.error(f"github_sync: فشل رفع الصورة {path_in_repo}: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"github_sync: استثناء عند رفع الصورة {path_in_repo}: {e}")
        return False


def sync_offer_to_github(offer, local_image_paths):
    """
    رفع عرض جديد بالكامل: الصور + offers.json.
    local_image_paths: قائمة المسارات المحلية الكاملة للصور.
    """
    # 1) رفع الصور
    for local_path, rel_repo_path in local_image_paths:
        upload_binary_file(
            rel_repo_path,
            local_path,
            f"صورة عرض جديد: {offer.get('id', '')} ({offer.get('category', '')})"
        )

    # 2) رفع offers.json (نُمرّر المحتوى من الملف المحلي المُحدّث)
    try:
        from pathlib import Path
        base = Path(__file__).resolve().parent
        offers_file = base.parent / "offers-data" / "offers.json"
        if offers_file.exists():
            text = offers_file.read_text(encoding="utf-8")
            upload_text_file(
                "offers-data/offers.json",
                text,
                f"عرض جديد: {offer.get('id', '')} — {offer.get('category', '')} — {offer.get('area', '')}"
            )
        return True
    except Exception as e:
        logger.error(f"github_sync: فشل مزامنة offers.json: {e}")
        return False
