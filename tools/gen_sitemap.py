#!/usr/bin/env python3
"""
مولد خرائط الموقع وتحديث الفهرسة الشامل - Sitemap & IndexNow Generator (M22-CORE)
ينتج:
  1. sitemap-index.xml (الفهرس الرئيسي)
  2. sitemap-pages.xml (الصفحات والمحاور الأساسية - priority 1.0 & 0.8)
  3. sitemap-offers.xml (عروض العقارات الحية - priority 0.6)
  4. sitemap.xml (للتوافق)
ويرسل إشعار IndexNow.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bot"))

CANONICAL_HOST = "https://abonasr0907-beep.github.io/-/"
INDEXNOW_KEY = "afaq_indexnow_key"
INDEXNOW_KEY_FILE = REPO_ROOT / "afaq_indexnow_key.txt"

# الصفحات الرئيسية والمحاور (priority 1.0 & 0.8)
STATIC_PAGES = [
    {"url": "", "priority": "1.0", "changefreq": "daily"},  # الرئيسية
    {"url": "farms.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "lands.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "resthouses.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "categories.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "areas.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "services.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "guides.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "compare.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "faq.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "why-us.html", "priority": "0.8", "changefreq": "monthly"},
    {"url": "contact.html", "priority": "0.8", "changefreq": "monthly"},
    {"url": "inquiry.html", "priority": "0.8", "changefreq": "weekly"},
    {"url": "list-property.html", "priority": "0.8", "changefreq": "weekly"},
    # محاور المناطق والأحياء
    {"url": "real-estate-riyadh/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "real-estate-alkharj/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "farms-riyadh/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "farms-alkharj/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "resthouses-riyadh/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "resthouses-alkharj/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "lands-riyadh/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "lands-alkharj/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "property-management-riyadh/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "well-drilling-services/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "well-location-services/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "center-alkharj/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "north-alkharj/", "priority": "0.8", "changefreq": "weekly"},
    {"url": "rahmaniyah-alkharj/", "priority": "0.8", "changefreq": "weekly"},
]


def slugify(text: str) -> str:
    """توليد slug عربي نظيف"""
    if not text:
        return "offer"
    clean = str(text).strip()
    clean = clean.replace(" ", "-").replace("/", "-")
    return urllib.parse.quote(clean, safe="-")


def generate_sitemaps() -> dict:
    """توليد ملفات السايت ماب الثلاثة"""
    today_date = datetime.now().strftime("%Y-%m-%d")

    # 1. sitemap-pages.xml
    pages_urls = []
    for item in STATIC_PAGES:
        full_url = f"{CANONICAL_HOST}{item['url']}"
        pages_urls.append(
            f"  <url>\n"
            f"    <loc>{full_url}</loc>\n"
            f"    <lastmod>{today_date}</lastmod>\n"
            f"    <changefreq>{item['changefreq']}</changefreq>\n"
            f"    <priority>{item['priority']}</priority>\n"
            f"  </url>"
        )

    xml_pages_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(pages_urls) + "\n"
        '</urlset>'
    )
    with open(REPO_ROOT / "sitemap-pages.xml", "w", encoding="utf-8") as f:
        f.write(xml_pages_content)

    # 2. sitemap-offers.xml
    offers_data = {"offers": []}
    offers_path = REPO_ROOT / "offers-data" / "offers.json"
    if offers_path.exists():
        try:
            with open(offers_path, "r", encoding="utf-8") as f:
                offers_data = json.load(f)
        except Exception as e:
            print(f"Error reading offers.json: {e}")

    offers_urls = []
    active_offers = [o for o in offers_data.get("offers", []) if o.get("status", "published") != "archived"]

    for o in active_offers[:1000]:  # ≤ 1000 رابط لكل ملف
        o_id = o.get("id", "")
        slug = slugify(o.get("title") or o.get("category") or "عقار")
        offer_url = f"{CANONICAL_HOST}offer/{o_id}/{slug}" if o_id else f"{CANONICAL_HOST}property.html?id={o_id}"
        offers_urls.append(
            f"  <url>\n"
            f"    <loc>{offer_url}</loc>\n"
            f"    <lastmod>{today_date}</lastmod>\n"
            f"    <changefreq>daily</changefreq>\n"
            f"    <priority>0.6</priority>\n"
            f"  </url>"
        )

    xml_offers_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(offers_urls) + "\n"
        '</urlset>'
    )
    with open(REPO_ROOT / "sitemap-offers.xml", "w", encoding="utf-8") as f:
        f.write(xml_offers_content)

    # 3. sitemap-index.xml
    xml_index_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <sitemap>\n'
        f'    <loc>{CANONICAL_HOST}sitemap-pages.xml</loc>\n'
        f'    <lastmod>{today_date}</lastmod>\n'
        f'  </sitemap>\n'
        f'  <sitemap>\n'
        f'    <loc>{CANONICAL_HOST}sitemap-offers.xml</loc>\n'
        f'    <lastmod>{today_date}</lastmod>\n'
        f'  </sitemap>\n'
        '</sitemapindex>'
    )
    with open(REPO_ROOT / "sitemap-index.xml", "w", encoding="utf-8") as f:
        f.write(xml_index_content)

    # 4. sitemap.xml للتوافقية
    with open(REPO_ROOT / "sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml_index_content)

    total_pages = len(STATIC_PAGES)
    total_offers = len(active_offers)
    total_urls = total_pages + total_offers

    print(f"✅ Generated sitemaps successfully:")
    print(f"  - sitemap-pages.xml: {total_pages} URLs")
    print(f"  - sitemap-offers.xml: {total_offers} URLs")
    print(f"  - sitemap-index.xml & sitemap.xml created.")
    print(f"  - Total URLs across sitemaps: {total_urls}")

    return {
        "total_pages": total_pages,
        "total_offers": total_offers,
        "total_urls": total_urls
    }


def send_indexnow_ping():
    """إرسال تنبيه IndexNow للمحركات"""
    key = INDEXNOW_KEY
    if INDEXNOW_KEY_FILE.exists():
        try:
            key = INDEXNOW_KEY_FILE.read_text().strip()
        except Exception:
            pass

    payload = {
        "host": "abonasr0907-beep.github.io",
        "key": key,
        "keyLocation": f"{CANONICAL_HOST}{key}.txt",
        "urlList": [
            f"{CANONICAL_HOST}",
            f"{CANONICAL_HOST}sitemap-index.xml",
            f"{CANONICAL_HOST}sitemap-pages.xml",
            f"{CANONICAL_HOST}sitemap-offers.xml"
        ]
    }
    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"🚀 IndexNow Ping Status: {resp.status}")
    except Exception as e:
        print(f"⚠️ IndexNow Ping failed or skipped: {e}")


def update_robots_txt():
    """تحديث robots.txt ليكون Allow: / وبسطر Sitemap واحد فقط"""
    robots_content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {CANONICAL_HOST}sitemap-index.xml\n"
    )
    with open(REPO_ROOT / "robots.txt", "w", encoding="utf-8") as f:
        f.write(robots_content)
    print("✅ robots.txt updated: Allow: / with exactly 1 Sitemap line.")


if __name__ == "__main__":
    update_robots_txt()
    stats = generate_sitemaps()
    send_indexnow_ping()

    # طباعة سطر إعادة الإرسال في Google Search Console للمالك
    sc_resubmit_url = f"https://search.google.com/search-console/sitemaps?resource_id={urllib.parse.quote(CANONICAL_HOST)}"
    print("\n" + "="*60)
    print("📌 سطر إعادة الإرسال في Google Search Console للمالك:")
    print(f"🔗 رابط إرسال السايت ماب في SC:\n   {sc_resubmit_url}")
    print(f"📄 ملف السايت ماب للتقديم:\n   sitemap-index.xml")
    print("="*60 + "\n")
