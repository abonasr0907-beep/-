#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
meta_generator.py — مولّد وسوم HTML الميتا للمرحلة الثالثة §2.2
===================================================================
يولّد:
  - <title>
  - <meta name="description">
  - <meta name="keywords">
  - <meta name="robots">
  - <link rel="canonical">
  - Open Graph (og:title, og:description, og:type, og:image, og:url, og:locale, og:site_name)
  - Twitter Card (twitter:card, twitter:title, twitter:description, twitter:image)
  - alt text للصور

كل الدوال idempotent.
"""

import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq.seo_engine.meta_generator")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LEGACY_SITE_URL = "https://abonasr0907-beep.github.io/-/"
SITE_BASE_URL = "https://urldra.cloud.huawei.com/BExUoXngu4"

SITE_NAME_AR = "مكتب آفاق الإنجاز العقاري"
SITE_NAME_EN = "Afaq Al-Injaz Real Estate Office"
DEFAULT_DESCRIPTION = (
    "مكتب آفاق الإنجاز العقاري — أفضل مكتب عقاري في الرياض والخرج. "
    "بيع وشراء عقارات في الرياض: مزارع، استراحات، أراضي سكنية، فلل للبيع في الرياض. "
    "مشاريع عقارية واستثمار عقاري بالرياض. مقاولات عامة وحفر آبار زراعية وإدارة الأملاك. خبرة 20 سنة."
)
DEFAULT_KEYWORDS = (
    "عقارات الخرج, مزارع الخرج, استراحات الخرج, أراضي سكنية الخرج, مخطط الرحمانية, "
    "الهياثم, الدلم, الضبيعة, العفجة, مكتب عقاري الرياض, آفاق الإنجاز العقاري, "
    "خدمات عقارية, حفر آبار, رخص بناء, مقاولات, تشطيبات, إدارة أملاك, عقارات الرياض, "
    "مزارع للبيع الرياض, استراحات للبيع الرياض, أراضي سكنية الرياض"
)

# أيام الأسبوع بالعربية للميتا الديناميكي
AREA_KEYWORDS_MAP = {
    "الرحمانية": "مخطط الرحمانية, عقارات الرحمانية, مزارع الرحمانية",
    "الهياثم": "حي الهياثم, عقارات الهياثم",
    "الدلم": "الدلم, عقارات الدلم, مزارع الدلم",
    "الضبيعة": "الضبيعة, عقارات الضبيعة",
    "العفجة": "العفجة, عقارات العفجة",
}

CATEGORY_KEYWORDS_MAP = {
    "مزرعة": "مزرعة للبيع, مزارع الخرج, مزارع الرياض",
    "استراحة": "استراحة للبيع, استراحات الخرج, استراحات الرياض",
    "أرض سكنية": "أرض سكنية للبيع, أراضي الخرج, أراضي الرياض",
}


def generate_title(offer=None, page_type="home", custom_title=""):
    """
    توليد وسم <title>.
    page_type: 'home' | 'property' | 'category' | 'area' | 'guide' | 'custom'
    idempotent.
    """
    if custom_title:
        return custom_title

    if page_type == "home":
        return f"{SITE_NAME_AR} | عقارات ومزارع واستراحات وأراضي سكنية ومقاولات وحفر آبار وإدارة أملاك في الخرج والرياض"

    if page_type == "property" and offer:
        title = offer.get("title", offer.get("id", "عرض عقاري"))
        area = offer.get("area", "")
        cat = offer.get("category", "")
        return f"{title} — {cat} في {area} | {SITE_NAME_AR}"

    if page_type == "category" and offer:
        cat = offer.get("category", "عقارات")
        return f"{cat} للبيع في الخرج والرياض | {SITE_NAME_AR}"

    if page_type == "area" and offer:
        area = offer.get("area", "الخرج")
        return f"عقارات {area} — مزارع واستراحات وأراضي | {SITE_NAME_AR}"

    if page_type == "guide":
        return f"أدلة عقارية | {SITE_NAME_AR}"

    return f"{SITE_NAME_AR}"


def generate_description(offer=None, page_type="home", custom_desc=""):
    """
    توليد وسم <meta name="description">.
    idempotent.
    """
    if custom_desc:
        return custom_desc[:160]

    if page_type == "property" and offer:
        desc = offer.get("description", "")[:120]
        area = offer.get("area", "الخرج")
        cat = offer.get("category", "عقار")
        price = offer.get("price_text", "")
        result = f"{cat} في {area} — {desc}"
        if price:
            result += f" — السعر: {price}"
        result += f". مكتب آفاق الإنجاز العقاري."
        return result[:160]

    if page_type == "category" and offer:
        cat = offer.get("category", "عقارات")
        return f"{cat} للبيع في الخرج والرياض — أفضل العروض من مكتب آفاق الإنجاز العقاري. خبرة 20 سنة في العقارات."[:160]

    if page_type == "area" and offer:
        area = offer.get("area", "الخرج")
        return f"عقارات {area} — مزارع واستراحات وأراضي سكنية للبيع. مكتب آفاق الإنجاز العقاري، خبرة 20 سنة."[:160]

    return DEFAULT_DESCRIPTION[:160]


def generate_keywords(offer=None, page_type="home"):
    """
    توليد وسم <meta name="keywords">.
    idempotent.
    """
    if page_type == "property" and offer:
        area = offer.get("area", "")
        cat = offer.get("category", "")
        kw = [cat, area, "مكتب آفاق الإنجاز العقاري", "عقارات الخرج", "عقارات الرياض"]
        if area in AREA_KEYWORDS_MAP:
            kw.append(AREA_KEYWORDS_MAP[area])
        if cat in CATEGORY_KEYWORDS_MAP:
            kw.append(CATEGORY_KEYWORDS_MAP[cat])
        return ", ".join(k for k in kw if k)

    if page_type == "category" and offer:
        cat = offer.get("category", "عقارات")
        base = CATEGORY_KEYWORDS_MAP.get(cat, cat)
        return f"{base}, عقارات الخرج, عقارات الرياض, {SITE_NAME_AR}"

    if page_type == "area" and offer:
        area = offer.get("area", "الخرج")
        base = AREA_KEYWORDS_MAP.get(area, f"عقارات {area}")
        return f"{base}, عقارات الخرج, عقارات الرياض, {SITE_NAME_AR}"

    return DEFAULT_KEYWORDS


def generate_canonical(page_type="home", offer=None, custom_url=""):
    """
    توليد <link rel="canonical">.
    idempotent.
    """
    if custom_url:
        return custom_url

    if page_type == "home":
        return LEGACY_SITE_URL

    if page_type == "property" and offer:
        slug = _slugify(offer.get("title", offer.get("id", "")))
        return f"{LEGACY_SITE_URL}offer/{offer.get('id','')}/{slug}"

    return LEGACY_SITE_URL


def generate_og_tags(title, description, url, image_url="", og_type="website"):
    """
    توليد وسوم Open Graph.
    idempotent.
    """
    if image_url and not image_url.startswith("http"):
        image_url = LEGACY_SITE_URL + image_url.lstrip("/")
    if not image_url:
        image_url = LEGACY_SITE_URL + "images/logo.jpg"

    return {
        "og:title": title,
        "og:description": description,
        "og:type": og_type,
        "og:url": url,
        "og:image": image_url,
        "og:locale": "ar_SA",
        "og:site_name": SITE_NAME_AR,
    }


def generate_twitter_tags(title, description, image_url=""):
    """
    توليد وسوم Twitter Card.
    idempotent.
    """
    if image_url and not image_url.startswith("http"):
        image_url = LEGACY_SITE_URL + image_url.lstrip("/")
    if not image_url:
        image_url = LEGACY_SITE_URL + "images/logo.jpg"

    return {
        "twitter:card": "summary_large_image",
        "twitter:title": title,
        "twitter:description": description,
        "twitter:image": image_url,
    }


def generate_alt_text(offer=None, image_index=0, context="property"):
    """
    توليد نص بديل (alt) للصور.
    idempotent.
    """
    if context == "property" and offer:
        title = offer.get("title", offer.get("id", "عقار"))
        area = offer.get("area", "الخرج")
        cat = offer.get("category", "عقار")
        if image_index == 0:
            return f"{title} — {cat} في {area} | {SITE_NAME_AR}"
        return f"صورة {image_index + 1} — {title} في {area} | {SITE_NAME_AR}"

    if context == "logo":
        return f"شعار {SITE_NAME_AR} في الخرج"

    if context == "hero":
        return f"مكتب آفاق الإنجاز العقاري — عقارات ومزارع واستراحات في الخرج والرياض"

    return f"صورة عقارية — {SITE_NAME_AR}"


def generate_meta_tags(offer=None, page_type="home", image_url="", custom_title="", custom_desc=""):
    """
    توليد كل الوسوم الميتا دفعة واحدة.
    يُرجع dict بكل القيم الجاهزة للإدراج في <head>.
    idempotent.
    """
    title = generate_title(offer, page_type, custom_title)
    description = generate_description(offer, page_type, custom_desc)
    keywords = generate_keywords(offer, page_type)
    canonical = generate_canonical(page_type, offer)
    og = generate_og_tags(title, description, canonical, image_url)
    twitter = generate_twitter_tags(title, description, image_url)

    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "robots": "index, follow",
        "canonical": canonical,
        "og": og,
        "twitter": twitter,
        "language": "Arabic",
        "geo_region": "SA-12",
        "geo_placename": "الخرج, الرياض",
        "geo_position": "24.1554;47.3068",
        "ICBM": "24.1554, 47.3068",
    }


def meta_tags_to_html(meta):
    """
    تحويل dict الميتا إلى سلاسل HTML جاهزة للإدراج في <head>.
    idempotent.
    """
    lines = []
    lines.append(f'<title>{meta["title"]}</title>')
    lines.append(f'<meta name="description" content="{_escape(meta["description"])}">')
    lines.append(f'<meta name="keywords" content="{_escape(meta["keywords"])}">')
    lines.append(f'<meta name="robots" content="{meta["robots"]}">')
    lines.append(f'<link rel="canonical" href="{meta["canonical"]}">')
    lines.append(f'<meta name="language" content="{meta["language"]}">')
    lines.append(f'<meta name="geo.region" content="{meta["geo_region"]}">')
    lines.append(f'<meta name="geo.placename" content="{_escape(meta["geo_placename"])}">')
    lines.append(f'<meta name="geo.position" content="{meta["geo_position"]}">')
    lines.append(f'<meta name="ICBM" content="{meta["ICBM"]}">')

    for k, v in meta["og"].items():
        lines.append(f'<meta property="{k}" content="{_escape(str(v))}">')

    for k, v in meta["twitter"].items():
        lines.append(f'<meta name="{k}" content="{_escape(str(v))}">')

    return "\n".join(lines)


def _escape(text):
    """تهريب أحرف HTML الخطرة."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _slugify(text):
    """تحويل نص إلى slug آمن (نسخة محلية)."""
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^\w\u0600-\u06FF-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower()


# ============================================================
# اختبار ذاتي
# ============================================================
def _self_test():
    print("=== meta_generator self-test ===")

    # Home page
    m = generate_meta_tags(page_type="home")
    assert m["title"], "Home title empty"
    assert "description" in m, "Home missing description"
    assert "keywords" in m, "Home missing keywords"
    assert m["canonical"] == LEGACY_SITE_URL, "Home canonical wrong"
    assert "og:title" in m["og"], "Home missing og:title"
    assert "twitter:card" in m["twitter"], "Home missing twitter:card"
    print("  Home page meta: OK")

    # Property page (simulate offer)
    offer = {
        "id": "FRM-001",
        "title": "مزرعة زراعية كاملة بمخطط الرحمانية",
        "area": "الرحمانية",
        "category": "مزرعة",
        "price_text": "1,200,000 ريال",
        "description": "مزرعة خصبة بمساحة 10,000 متر مربع",
        "images": ["images/farm1.jpg"],
    }
    m2 = generate_meta_tags(offer, page_type="property", image_url="images/farm1.jpg")
    assert "مزرعة" in m2["title"], "Property title missing category"
    assert "الرحمانية" in m2["title"], "Property title missing area"
    assert "offer/FRM-001/" in m2["canonical"], "Property canonical missing offer URL"
    assert m2["og"]["og:type"] == "website", "Property og:type wrong"
    print("  Property page meta: OK")

    # HTML output
    html = meta_tags_to_html(m2)
    assert "<title>" in html, "HTML missing title tag"
    assert '<meta name="description"' in html, "HTML missing description"
    assert 'rel="canonical"' in html, "HTML missing canonical"
    assert 'property="og:title"' in html, "HTML missing og:title"
    print("  HTML output: OK")

    # Alt text
    alt = generate_alt_text(offer, 0, "property")
    assert "مزرعة" in alt, "Alt text missing category"
    print("  Alt text: OK")

    # Robots
    assert m["robots"] == "index, follow", "Robots wrong"
    print("  Robots: OK")

    print("=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    _self_test()
