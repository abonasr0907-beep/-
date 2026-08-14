#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sitemap_updater.py — تحديث sitemap.xml (إضافة فقط — add-only) للمرحلة الثالثة §2.5
=====================================================================================
يضيف روابط العروض الجديدة المنشورة إلى sitemap.xml دون حذف أو تعديل أي رابط موجود.

قواعد صارمة:
  - لا يُحذف أي <url> موجود
  - لا يُعدَّل أي <url> موجود
  - يضيف فقط روابط جديدة للعروض المنشورة (status=published)
  - idempotent: لا يضيف رابطًا موجودًا بالفعل
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq.seo_engine.sitemap_updater")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SITEMAP_PATH = BASE_DIR / "sitemap.xml"
OFFERS_PATH = BASE_DIR / "offers-data" / "offers.json"
LEGACY_SITE_URL = "https://abonasr0907-beep.github.io/-/"


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


def _get_existing_locs(sitemap_content):
    """استخراج كل روابط <loc> الموجودة في sitemap."""
    return set(re.findall(r"<loc>(.*?)</loc>", sitemap_content, re.DOTALL))


def _build_offer_url(offer):
    """بناء رابط العرض الجديد."""
    offer_id = offer.get("id", "")
    slug = _slugify(offer.get("title", offer_id))
    return f"{LEGACY_SITE_URL}offer/{offer_id}/{slug}"


def _build_url_entry(url, lastmod, changefreq="weekly", priority="0.8", image_url="", image_title=""):
    """بناء إدخال <url> كامل."""
    lines = [
        "  <url>",
        f"    <loc>{url}</loc>",
        f"    <lastmod>{lastmod}</lastmod>",
        f"    <changefreq>{changefreq}</changefreq>",
        f"    <priority>{priority}</priority>",
    ]
    if image_url:
        if not image_url.startswith("http"):
            image_url = LEGACY_SITE_URL + image_url.lstrip("/")
        lines.extend([
        "    <image:image>",
        f"      <image:loc>{image_url}</image:loc>",
        f"      <image:title>{image_title}</image:title>",
        "    </image:image>",
        ])
    lines.append("  </url>")
    return "\n".join(lines)


def update_sitemap_add_only(offers=None):
    """
    إضافة روابط العروض المنشورة إلى sitemap.xml (إضافة فقط).
    لا يُحذف أو يُعدِّل أي رابط موجود.
    idempotent: لا يضيف رابطًا موجودًا.

    يُرجع: (added_count, skipped_count, total_urls)
    """
    # قراءة sitemap الحالي
    try:
        sitemap_content = SITEMAP_PATH.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"تعذّر قراءة sitemap.xml: {e}")
        return (0, 0, 0)

    existing_locs = _get_existing_locs(sitemap_content)
    initial_count = len(existing_locs)

    # تحميل العروض
    if offers is None:
        try:
            with open(OFFERS_PATH, "r", encoding="utf-8") as f:
                offers = json.load(f).get("offers", [])
        except Exception as e:
            logger.warning(f"تعذّر تحميل offers.json: {e}")
            return (0, 0, initial_count)

    today = datetime.now().strftime("%Y-%m-%d")
    new_entries = []
    added = 0
    skipped = 0

    for offer in offers:
        # فقط العروض المنشورة
        if offer.get("status") != "published":
            continue

        url = _build_offer_url(offer)
        if url in existing_locs:
            skipped += 1
            continue

        # الصورة الأولى
        images = offer.get("images", [])
        image_url = ""
        image_title = offer.get("title", "")
        if isinstance(images, list) and images:
            first_img = images[0] if isinstance(images[0], str) else images[0].get("url", "")
            if first_img:
                image_url = first_img

        priority = "0.9" if offer.get("featured") else "0.8"
        entry = _build_url_entry(
            url,
            offer.get("date_added", today),
            changefreq="weekly",
            priority=priority,
            image_url=image_url,
            image_title=image_title,
        )
        new_entries.append(entry)
        existing_locs.add(url)
        added += 1

    if new_entries:
        # إدخال الإدخالات الجديدة قبل </urlset>
        insert_block = "\n  <!-- Phase 3 §2.5: روابط العروض المنشورة (add-only) -->\n" + "\n".join(new_entries) + "\n"
        new_content = sitemap_content.replace("</urlset>", insert_block + "</urlset>")
        try:
            SITEMAP_PATH.write_text(new_content, encoding="utf-8")
            logger.info(f"sitemap.xml: تمت إضافة {added} رابط جديد، تخطّي {skipped} موجود")
        except Exception as e:
            logger.error(f"تعذّر كتابة sitemap.xml: {e}")
            return (0, skipped, initial_count)

    return (added, skipped, len(existing_locs))


def verify_sitemap_integrity():
    """
    التحقق من سلامة sitemap.xml — يرجع True إذا كان صحيحًا.
    """
    try:
        content = SITEMAP_PATH.read_text(encoding="utf-8")
    except Exception:
        return False

    if "</urlset>" not in content:
        return False
    if "<?xml" not in content:
        return False

    # عد الروابط
    locs = _get_existing_locs(content)
    return len(locs) > 0


# ============================================================
# اختبار ذاتي
# ============================================================
def _self_test():
    print("=== sitemap_updater self-test ===")

    # قراءة قبل
    content_before = SITEMAP_PATH.read_text(encoding="utf-8")
    locs_before = _get_existing_locs(content_before)
    count_before = len(locs_before)
    print(f"  URLs before: {count_before}")

    # تشغيل التحديث
    added, skipped, total = update_sitemap_add_only()
    print(f"  Added: {added}, Skipped: {skipped}, Total: {total}")

    # قراءة بعد
    content_after = SITEMAP_PATH.read_text(encoding="utf-8")
    locs_after = _get_existing_locs(content_after)
    count_after = len(locs_after)
    print(f"  URLs after: {count_after}")

    # التحقق: لم تنقص الروابط
    assert count_after >= count_before, f"ROLES VIOLATED: URLs decreased from {count_before} to {count_after}"
    print("  Add-only verified: URLs did not decrease — OK")

    # التحقق: سلامة
    assert verify_sitemap_integrity(), "Sitemap integrity failed"
    print("  Integrity verified — OK")

    # Idempotent: تشغيل مرة ثانية لا يضيف شيئًا
    added2, skipped2, total2 = update_sitemap_add_only()
    assert added2 == 0, f"Idempotency failed: added {added2} on second run"
    print(f"  Idempotent: second run added {added2} — OK")

    print("=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    _self_test()
