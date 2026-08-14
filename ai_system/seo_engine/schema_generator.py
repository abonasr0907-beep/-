#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schema_generator.py — مولّد البيانات المنظّمة JSON-LD (Schema.org)
=====================================================================
المرحلة الثالثة §2.3: أنواع Schema المدعومة:
  - Organization
  - RealEstateAgent
  - RealEstateListing (لكل عرض)
  - Offer (لكل عرض — سعر + توفر)
  - ImageObject (لكل صورة)
  - BreadcrumbList
  - FAQPage
  - Article (للأدلة والمقالات)

كل الدوال idempotent وتُرجع dict جاهز للتسلسل إلى JSON-LD.
"""

import json
import re
import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq.seo_engine.schema_generator")

# ============================================================
# المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /workspace/afaq-repo
OFFICE_DATA_PATH = BASE_DIR / "offers-data" / "office-data.json"
OFFERS_PATH = BASE_DIR / "offers-data" / "offers.json"

# أرقام الهواتف الثابتة (من OFFICE_DATA — لا تُغيَّر)
PHONE_WHATSAPP_CALLS = "0545888931"
PHONE_CALLS_ONLY = "0544699933"
PHONE_WHATSAPP_CALLS_2 = "0561610748"
PHONE_SCHEMA_ONLY = "0548601430"  # يظهر في Schema فقط

SITE_BASE_URL = "https://urldra.cloud.huawei.com/BExUoXngu4"
LEGACY_SITE_URL = "https://abonasr0907-beep.github.io/-/"


def _load_office_data():
    """تحميل بيانات المكتب من ملف JSON (آمن)."""
    try:
        with open(OFFICE_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"تعذّر تحميل office-data.json: {e}")
        return {}


def _load_offers():
    """تحميل العروض من ملف JSON (آمن)."""
    try:
        with open(OFFERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("offers", [])
    except Exception as e:
        logger.warning(f"تعذّر تحميل offers.json: {e}")
        return []


def _phone_e164(local):
    """تحويل رقم محلي إلى صيغة E.164 (+966)."""
    digits = re.sub(r"\D", "", local)
    if digits.startswith("966"):
        return "+" + digits
    if digits.startswith("0"):
        return "+966" + digits[1:]
    return "+966" + digits


def _slugify(text):
    """تحويل نص عربي/إنجليزي إلى slug آمن للروابط."""
    if not text:
        return ""
    # الأحرف العربية → إبقاء كما هي لكن نُنشئ slug لاتيني بديل
    text = str(text).strip()
    # إزالة التشكيل
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # تحويل المسافات إلى شرطات
    text = re.sub(r"[\s_]+", "-", text)
    # إزالة الأحرف غير المرغوبة (إبقاء عربي ولاتيني وأرقام وشرطة)
    text = re.sub(r"[^\w\u0600-\u06FF-]", "", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower()


def _build_contact_points(office_data):
    """بناء نقاط الاتصال لـ Schema من بيانات المكتب."""
    phones = office_data.get("office", {}).get("phones", {})
    contact_points = []

    cp_map = [
        (phones.get("whatsapp_calls"), "customer service", PHONE_WHATSAPP_CALLS),
        (phones.get("calls_only"), "reservations", PHONE_CALLS_ONLY),
        (phones.get("whatsapp_calls_2"), "sales", PHONE_WHATSAPP_CALLS_2),
        (PHONE_SCHEMA_ONLY, "sales", PHONE_SCHEMA_ONLY),
    ]

    seen = set()
    for _, ctype, num in cp_map:
        if num and num not in seen:
            seen.add(num)
            contact_points.append({
                "@type": "ContactPoint",
                "telephone": _phone_e164(num),
                "contactType": ctype,
                "availableLanguage": ["Arabic"],
                "areaServed": "SA",
            })
    return contact_points


def generate_organization_schema():
    """
    توليد Schema من نوع Organization — للموقع الرئيسي.
    idempotent: لا يعتمد على أي حالة متغيرة.
    """
    od = _load_office_data()
    office = od.get("office", {})

    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": LEGACY_SITE_URL + "#organization",
        "name": office.get("name", "مكتب آفاق الإنجاز العقاري"),
        "alternateName": office.get("nameEn", "Afaq Al-Injaz Real Estate Office"),
        "url": LEGACY_SITE_URL,
        "logo": LEGACY_SITE_URL + "images/logo.jpg",
        "image": LEGACY_SITE_URL + "images/logo.jpg",
        "email": office.get("email", "afaqalqary@gmail.com"),
        "foundingDate": office.get("established", "2005"),
        "telephone": _phone_e164(PHONE_WHATSAPP_CALLS),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "الخرج",
            "addressRegion": "الرياض",
            "addressCountry": "SA",
        },
        "areaServed": ["الرياض", "الخرج", "الرحمانية", "الهياثم", "الدلم", "الضبيعة", "العفجة"],
        "sameAs": [
            office.get("social", {}).get("snapchat", ""),
            office.get("social", {}).get("tiktok", ""),
        ],
    }


def generate_real_estate_agent_schema():
    """
    توليد Schema من نوع RealEstateAgent — للموقع الرئيسي.
    يشمل نقاط الاتصال و geo و areaServed.
    """
    od = _load_office_data()
    office = od.get("office", {})
    contact_points = _build_contact_points(od)

    return {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "@id": LEGACY_SITE_URL + "#realestateagent",
        "name": office.get("name", "مكتب آفاق الإنجاز العقاري"),
        "alternateName": office.get("nameEn", "Afaq Al-Injaz Real Estate Office"),
        "description": (
            f"{office.get('name', 'مكتب آفاق الإنجاز العقاري')} — "
            f"{office.get('experience', '20 سنة خبرة')}. "
            f"بيع وشراء عقارات في الخرج والرياض: مزارع، استراحات، أراضي سكنية."
        ),
        "url": LEGACY_SITE_URL,
        "logo": LEGACY_SITE_URL + "images/logo.jpg",
        "image": LEGACY_SITE_URL + "images/logo.jpg",
        "email": office.get("email", "afaqalqary@gmail.com"),
        "telephone": _phone_e164(PHONE_WHATSAPP_CALLS),
        "foundingDate": office.get("established", "2005"),
        "priceRange": "$$",
        "areaServed": ["الرياض", "الخرج", "الرحمانية", "الهياثم", "الدلم", "الضبيعة", "العفجة"],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "الخرج",
            "addressRegion": "الرياض",
            "addressCountry": "SA",
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": "24.1554",
            "longitude": "47.3068",
        },
        "contactPoint": contact_points,
        "sameAs": [
            office.get("social", {}).get("snapchat", ""),
            office.get("social", {}).get("tiktok", ""),
        ],
    }


def generate_listing_schema(offer):
    """
    توليد Schema من نوع RealEstateListing لعرض واحد.
    idempotent: يعتمد فقط على بيانات العرض.
    """
    offer_id = offer.get("id", "")
    slug = _slugify(offer.get("title", offer_id))
    listing_url = f"{LEGACY_SITE_URL}offer/{offer_id}/{slug}"

    images = offer.get("images", [])
    if isinstance(images, list) and images:
        first_img = images[0] if isinstance(images[0], str) else images[0].get("url", "")
        image_url = first_img if first_img.startswith("http") else LEGACY_SITE_URL + first_img.lstrip("/")
    else:
        image_url = LEGACY_SITE_URL + "images/logo.jpg"

    price = offer.get("price", 0)
    try:
        price_num = int(re.sub(r"\D", "", str(price))) if price else 0
    except Exception:
        price_num = 0

    return {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "@id": listing_url + "#listing",
        "name": offer.get("title", offer_id),
        "description": offer.get("description", ""),
        "url": listing_url,
        "image": image_url,
        "datePosted": offer.get("date_added", datetime.now().strftime("%Y-%m-%d")),
        "category": offer.get("category", ""),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": offer.get("area", "الخرج"),
            "addressRegion": "الرياض",
            "addressCountry": "SA",
        },
        "offers": generate_offer_schema(offer),
        "agent": {
            "@type": "RealEstateAgent",
            "name": "مكتب آفاق الإنجاز العقاري",
            "telephone": _phone_e164(PHONE_WHATSAPP_CALLS),
        },
    }


def generate_offer_schema(offer):
    """
    توليد Schema من نوع Offer لعرض واحد (السعر + التوفر).
    idempotent.
    """
    price = offer.get("price", 0)
    try:
        price_num = int(re.sub(r"\D", "", str(price))) if price else 0
    except Exception:
        price_num = 0

    operation = offer.get("operation_type", "sale")
    if "rent" in str(operation).lower() or "إجار" in str(operation):
        business_func = "https://schema.org/RentAction"
    else:
        business_func = "https://schema.org/SellAction"

    offer_id = offer.get("id", "")
    slug = _slugify(offer.get("title", offer_id))
    listing_url = f"{LEGACY_SITE_URL}offer/{offer_id}/{slug}"

    return {
        "@type": "Offer",
        "@id": listing_url + "#offer",
        "price": str(price_num) if price_num else "0",
        "priceCurrency": "SAR",
        "priceSpecification": {
            "@type": "PriceSpecification",
            "price": str(price_num) if price_num else "0",
            "priceCurrency": "SAR",
        },
        "availability": "https://schema.org/InStock",
        "businessFunction": business_func,
        "itemOffered": {
            "@type": "Product",
            "name": offer.get("title", offer_id),
            "category": offer.get("category", ""),
        },
        "seller": {
            "@type": "RealEstateAgent",
            "name": "مكتب آفاق الإنجاز العقاري",
        },
    }


def generate_image_object_schema(image_url, caption="", offer_id=""):
    """
    توليد Schema من نوع ImageObject لصورة واحدة.
    idempotent.
    """
    if image_url and not image_url.startswith("http"):
        image_url = LEGACY_SITE_URL + image_url.lstrip("/")

    return {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "@id": (image_url or "") + "#imageobj",
        "url": image_url,
        "contentUrl": image_url,
        "caption": caption or f"صورة عقار — مكتب آفاق الإنجاز العقاري",
        "representativeOfPage": True,
        "provider": {
            "@type": "Organization",
            "name": "مكتب آفاق الإنجاز العقاري",
        },
    }


def generate_breadcrumb_schema(crumbs):
    """
    توليد Schema من نوع BreadcrumbList.
    crumbs: list of (name, url) tuples.
    idempotent.
    """
    items = []
    for i, (name, url) in enumerate(crumbs):
        items.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": name,
            "item": url,
        })

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def generate_faq_schema(faqs):
    """
    توليد Schema من نوع FAQPage.
    faqs: list of (question, answer) tuples.
    idempotent.
    """
    entities = []
    for q, a in faqs:
        entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a,
            },
        })

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities,
    }


def generate_article_schema(title, description, url, date_published, author="", image_url=""):
    """
    توليد Schema من نوع Article (للأدلة والمقالات).
    idempotent.
    """
    if image_url and not image_url.startswith("http"):
        image_url = LEGACY_SITE_URL + image_url.lstrip("/")
    if not image_url:
        image_url = LEGACY_SITE_URL + "images/logo.jpg"

    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": url,
        "datePublished": date_published,
        "dateModified": date_published,
        "author": {
            "@type": "Organization",
            "name": author or "مكتب آفاق الإنجاز العقاري",
        },
        "publisher": {
            "@type": "Organization",
            "name": "مكتب آفاق الإنجاز العقاري",
            "logo": {
                "@type": "ImageObject",
                "url": LEGACY_SITE_URL + "images/logo.jpg",
            },
        },
        "image": {
            "@type": "ImageObject",
            "url": image_url,
        },
        "inLanguage": "ar-SA",
    }


def generate_home_page_schemas():
    """
    توليد كل Schemas لصفحة الرئيسية (Organization + RealEstateAgent + FAQ).
    تُرجع قائمة dicts جاهزة للتضمين في <script type="application/ld+json">.
    """
    od = _load_office_data()
    schemas = [
        generate_organization_schema(),
        generate_real_estate_agent_schema(),
    ]

    # FAQ ثابت للصفحة الرئيسية
    faqs = [
        ("ما هي خدمات مكتب آفاق الإنجاز العقاري؟",
         "يقدم مكتب آفاق الإنجاز العقاري خدمات متكاملة تشمل بيع وشراء المزارع والاستراحات والأراضي السكنية في الخرج والرياض، بالإضافة إلى خدمات ما بعد البيع مثل استخراج رخص البناء والمقاولات والتشطيبات وإدارة الأملاك وحفر الآبار."),
        ("أين يقع مكتب آفاق الإنجاز العقاري؟",
         "يقع المكتب في مخطط الرحمانية بالخرج، ويخدم مناطق الرياض والخرج ومخطط الرحمانية والهياثم والدلم والضبيعة والعفجة."),
        ("كيف يمكنني التواصل مع مكتب آفاق الإنجاز العقاري؟",
         "يمكنك التواصل عبر الواتساب على 0545888931 أو الاتصال على 0544699933. كما نتوفر على رقم إضافي للواتساب والاتصال 0561610748."),
        ("هل يقدم المكتب خدمات إدارة الأملاك؟",
         "نعم، يقدم المكتب خدمات إدارة الأملاك العقارية بالكامل من تأجير وصيانة ومتابعة، بالإضافة إلى خدمات المقاولات وحفر الآبار."),
    ]
    schemas.append(generate_faq_schema(faqs))

    return schemas


def generate_property_page_schemas(offer):
    """
    توليد كل Schemas لصفحة عرض واحد (RealEstateListing + Offer + BreadcrumbList + ImageObject).
    offer: dict العرض.
    تُرجع قائمة dicts جاهزة للتضمين.
    """
    offer_id = offer.get("id", "")
    slug = _slugify(offer.get("title", offer_id))
    listing_url = f"{LEGACY_SITE_URL}offer/{offer_id}/{slug}"

    schemas = [
        generate_listing_schema(offer),
        generate_offer_schema(offer),
    ]

    # BreadcrumbList
    crumbs = [
        ("الرئيسية", LEGACY_SITE_URL),
        (offer.get("section") or offer.get("category", "العقارات"), LEGACY_SITE_URL + f"{offer.get('type', 'farms')}.html"),
        (offer.get("title", offer_id), listing_url),
    ]
    schemas.append(generate_breadcrumb_schema(crumbs))

    # ImageObject للصورة الأولى
    images = offer.get("images", [])
    if isinstance(images, list) and images:
        first_img = images[0] if isinstance(images[0], str) else images[0].get("url", "")
        if first_img:
            schemas.append(generate_image_object_schema(first_img, offer.get("title", ""), offer_id))

    return schemas


def schemas_to_jsonld_scripts(schemas):
    """
    تحويل قائمة schemas إلى سلاسل <script type="application/ld+json">... جاهزة للإدراج في HTML.
    idempotent: كل schema مستقل.
    """
    scripts = []
    for s in schemas:
        try:
            json_str = json.dumps(s, ensure_ascii=False, indent=2)
            scripts.append(f'<script type="application/ld+json">\n{json_str}\n</script>')
        except Exception as e:
            logger.warning(f"تعذّر تسلسل schema: {e}")
    return "\n".join(scripts)


# ============================================================
# اختبار ذاتي (self-test)
# ============================================================
def _self_test():
    """اختبار ذاتي سريع — يتحقق من إنتاج Schemas صحيحة."""
    print("=== schema_generator self-test ===")

    # Organization
    org = generate_organization_schema()
    assert org["@type"] == "Organization", "Organization type wrong"
    assert "name" in org, "Organization missing name"
    assert "telephone" in org, "Organization missing telephone"
    print("  Organization schema: OK")

    # RealEstateAgent
    agent = generate_real_estate_agent_schema()
    assert agent["@type"] == "RealEstateAgent", "RealEstateAgent type wrong"
    assert len(agent.get("contactPoint", [])) >= 3, "ContactPoints too few"
    print("  RealEstateAgent schema: OK")

    # Listing + Offer (from a sample offer)
    offers = _load_offers()
    if offers:
        o = offers[0]
        listing = generate_listing_schema(o)
        assert listing["@type"] == "RealEstateListing", "Listing type wrong"
        assert "offers" in listing, "Listing missing offers"
        print("  RealEstateListing schema: OK")

        offer_s = generate_offer_schema(o)
        assert offer_s["@type"] == "Offer", "Offer type wrong"
        assert "priceCurrency" in offer_s, "Offer missing currency"
        print("  Offer schema: OK")

        # Breadcrumb
        bc = generate_breadcrumb_schema([("الرئيسية", "https://x"), ("العقارات", "https://y")])
        assert bc["@type"] == "BreadcrumbList", "Breadcrumb type wrong"
        assert len(bc["itemListElement"]) == 2, "Breadcrumb wrong count"
        print("  BreadcrumbList schema: OK")

        # ImageObject
        io = generate_image_object_schema("images/test.jpg", "caption")
        assert io["@type"] == "ImageObject", "ImageObject type wrong"
        print("  ImageObject schema: OK")

        # Article
        art = generate_article_schema("عنوان", "وصف", "https://x", "2025-01-01")
        assert art["@type"] == "Article", "Article type wrong"
        print("  Article schema: OK")

        # FAQ
        faq = generate_faq_schema([("سؤال؟", "جواب")])
        assert faq["@type"] == "FAQPage", "FAQ type wrong"
        assert len(faq["mainEntity"]) == 1, "FAQ wrong count"
        print("  FAQPage schema: OK")

        # Property page schemas
        ps = generate_property_page_schemas(o)
        assert len(ps) >= 3, "Property page schemas too few"
        print(f"  Property page schemas: {len(ps)} items — OK")

        # Home page schemas
        hs = generate_home_page_schemas()
        assert len(hs) >= 3, "Home page schemas too few"
        print(f"  Home page schemas: {len(hs)} items — OK")

        # JSON-LD output
        scripts = schemas_to_jsonld_scripts(hs)
        assert "application/ld+json" in scripts, "JSON-LD script tag missing"
        print("  JSON-LD scripts: OK")

    # Phone E.164
    assert _phone_e164("0545888931") == "+966545888931", "E.164 conversion wrong"
    assert _phone_e164("0544699933") == "+966544699933", "E.164 conversion wrong"
    print("  Phone E.164: OK")

    # Slugify
    s = _slugify("مزرعة في الرحمانية")
    assert s and len(s) > 0, "Slugify empty"
    print(f"  Slugify: '{s}' — OK")

    print("=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    _self_test()
