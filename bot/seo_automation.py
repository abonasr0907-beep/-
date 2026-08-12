#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام أتمتة SEO التلقائي — SEO Automation System
===============================================
يقوم تلقائياً بإنشاء جميع عناصر SEO عند إضافة عقار/أرض/مزرعة/استراحة/خدمة/عرض جديد:

- SEO Title (عربي)
- Meta Description
- Keywords
- Canonical URL
- Schema JSON-LD (RealEstateListing / Service / FAQPage)
- Open Graph tags
- Twitter Card tags
- ALT Images (عربي + إنجليزي)
- Internal Links

كما يمنع إنشاء صفحات مكررة — يتحقق من وجود صفحة مشابهة قبل الإنشاء.
"""

import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

BASE_URL = "https://abonasr0907-beep.github.io/-/"
WEBSITE_DIR = Path(__file__).resolve().parent.parent

# ========== Keyword Maps ==========
TYPE_KEYWORDS = {
    "farm": {"ar": "مزرعة للبيع", "en": "farm for sale", "section": "مزارع"},
    "resthouse": {"ar": "استراحة للبيع", "en": "resthouse for sale", "section": "استراحات"},
    "land": {"ar": "أرض للبيع", "en": "land for sale", "section": "أراضي"},
    "villa": {"ar": "فلة للبيع", "en": "villa for sale", "section": "فلل"},
    "service": {"ar": "خدمات عقارية", "en": "real estate services", "section": "خدمات"},
    "well_drilling": {"ar": "حفر آبار", "en": "well drilling", "section": "خدمات"},
    "property_management": {"ar": "إدارة أملاك", "en": "property management", "section": "خدمات"},
}

AREA_KEYWORDS = {
    "الرياض": {"en": "Riyadh", "region": "SA-01"},
    "الخرج": {"en": "Al-Kharj", "region": "SA-12"},
    "الرحمانية": {"en": "Al-Rahmaniyah", "region": "SA-12"},
    "الرحمنية": {"en": "Al-Rahmaniyah", "region": "SA-12"},
    "الهياثم": {"en": "Al-Hayatham", "region": "SA-12"},
    "الدلم": {"en": "Al-Dalam", "region": "SA-12"},
    "الضبيعة": {"en": "Al-Dhabiyyah", "region": "SA-12"},
    "العفجة": {"en": "Al-Afjah", "region": "SA-12"},
}

# ========== Duplicate Detection ==========
def compute_content_hash(title, area, type_):
    """Compute a hash for duplicate detection."""
    normalized = f"{title.lower().strip()}|{area.lower().strip()}|{type_.lower().strip()}"
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def check_duplicate(title, area, type_, offers_file="offers-data/offers.json"):
    """
    تحقق من وجود عقار مشابه قبل الإضافة.
    يرجع: (is_duplicate, existing_id, similarity_score)
    """
    offers_path = WEBSITE_DIR / offers_file
    if not offers_path.exists():
        return False, None, 0.0
    
    try:
        with open(offers_path, 'r', encoding='utf-8') as f:
            offers_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False, None, 0.0
    
    # Handle both {"offers": [...]} wrapper and bare [...] list formats
    if isinstance(offers_data, dict):
        offers = offers_data.get("offers", [])
    elif isinstance(offers_data, list):
        offers = offers_data
    else:
        return False, None, 0.0
    
    new_hash = compute_content_hash(title, area, type_)
    new_title_words = set(re.findall(r'\w+', title.lower()))
    
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        existing_title = offer.get("title", "")
        existing_area = offer.get("area", "")
        existing_type = offer.get("type", "")
        
        # Exact hash match
        existing_hash = compute_content_hash(existing_title, existing_area, existing_type)
        if existing_hash == new_hash:
            return True, offer.get("id"), 1.0
        
        # Word similarity check (Jaccard)
        existing_words = set(re.findall(r'\w+', existing_title.lower()))
        if existing_words and new_title_words:
            intersection = new_title_words & existing_words
            union = new_title_words | existing_words
            similarity = len(intersection) / len(union) if union else 0
            
            # Same area + same type + high title similarity = likely duplicate
            if (existing_area == area and existing_type == type_ and similarity > 0.7):
                return True, offer.get("id"), similarity
    
    return False, None, 0.0

# ========== SEO Element Generation ==========
def generate_seo_title(offer):
    """Generate SEO-optimized title."""
    title = offer.get("title", "")
    area = offer.get("area", "")
    type_ = offer.get("type", "property")
    kw = TYPE_KEYWORDS.get(type_, TYPE_KEYWORDS["land"])
    
    # Pattern: [Title] — [Area Keyword] | آفاق الإنجاز العقاري
    if area:
        seo_title = f"{title} — {kw['ar']} في {area} | مكتب آفاق الإنجاز العقاري"
    else:
        seo_title = f"{title} | مكتب آفاق الإنجاز العقاري"
    
    # Keep under 60 characters for the core title, but allow longer for Arabic
    if len(seo_title) > 120:
        seo_title = seo_title[:117] + "..."
    
    return seo_title

def generate_meta_description(offer):
    """Generate meta description from offer data."""
    title = offer.get("title", "")
    area = offer.get("area", "")
    price_text = offer.get("price_text", "")
    size_sqm = offer.get("size_sqm", "")
    description = offer.get("description", "")
    features = offer.get("features", [])
    type_ = offer.get("type", "property")
    kw = TYPE_KEYWORDS.get(type_, TYPE_KEYWORDS["land"])
    
    # Build description
    parts = []
    if description:
        # Use first 100 chars of description
        short_desc = description[:100]
        if len(description) > 100:
            short_desc = short_desc.rsplit(' ', 1)[0] + "..."
        parts.append(short_desc)
    
    if area:
        parts.append(f"في {area}")
    
    if size_sqm:
        parts.append(f"مساحة {size_sqm} م²")
    
    if price_text:
        parts.append(f"السعر: {price_text}")
    
    if features:
        parts.append("مواصفات: " + "، ".join(features[:3]))
    
    parts.append("مكتب آفاق الإنجاز العقاري")
    
    meta_desc = " — ".join(parts)
    
    # Keep under 160 characters
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."
    
    return meta_desc

def generate_keywords(offer):
    """Generate keywords string from offer data."""
    area = offer.get("area", "")
    area_en = offer.get("area_en", "")
    type_ = offer.get("type", "property")
    kw = TYPE_KEYWORDS.get(type_, TYPE_KEYWORDS["land"])
    
    keywords = [
        kw["ar"], kw["en"],
        f"{kw['ar']} في {area}" if area else "",
        f"{kw['en']} in {area_en}" if area_en else "",
        "عقارات في الرياض",
        "عقارات في الخرج",
        "مكتب عقاري في الرياض",
        "مكتب عقاري في الخرج",
        "آفاق الإنجاز العقاري",
        "بيع عقارات",
        "شراء عقارات",
        "استثمار عقاري",
    ]
    
    # Filter empty and deduplicate
    seen = set()
    unique = []
    for k in keywords:
        if k and k not in seen:
            seen.add(k)
            unique.append(k)
    
    return ", ".join(unique)

def generate_canonical(offer):
    """Generate canonical URL for the property page."""
    offer_id = offer.get("id", "")
    return f"{BASE_URL}property.html?id={offer_id}"

def generate_schema_jsonld(offer):
    """Generate Schema JSON-LD for the property."""
    offer_id = offer.get("id", "")
    title = offer.get("title", "")
    description = offer.get("description", "")
    price = offer.get("price", 0)
    area = offer.get("area", "")
    size_sqm = offer.get("size_sqm", 0)
    images = offer.get("images", [])
    type_ = offer.get("type", "property")
    kw = TYPE_KEYWORDS.get(type_, TYPE_KEYWORDS["land"])
    
    # Product/RealEstateListing schema
    image_urls = [BASE_URL + img for img in images] if images else [BASE_URL + "images/logo.jpg"]
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": title,
        "description": description[:300] if description else "",
        "url": generate_canonical(offer),
        "image": image_urls,
        "offers": {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": "SAR",
            "availability": "https://schema.org/InStock",
            "seller": {
                "@type": "RealEstateAgent",
                "name": "مكتب آفاق الإنجاز العقاري",
                "url": BASE_URL
            }
        },
        "brand": {
            "@type": "Brand",
            "name": "آفاق الإنجاز العقاري"
        }
    }
    
    # Add area as keyword
    if area:
        schema["category"] = f"{kw['ar']} في {area}"
    
    # Add additional property for size
    if size_sqm:
        schema["additionalProperty"] = {
            "@type": "PropertyValue",
            "name": "المساحة",
            "value": f"{size_sqm} متر مربع"
        }
    
    # Also generate BreadcrumbList
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "الرئيسية",
                "item": BASE_URL
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": kw["section"],
                "item": f"{BASE_URL}{kw['section']}.html" if kw["section"] in ["مزارع", "استراحات", "أراضي", "خدمات"] else BASE_URL
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title[:50],
                "item": generate_canonical(offer)
            }
        ]
    }
    
    return [schema, breadcrumb]

def generate_og_tags(offer):
    """Generate Open Graph tags."""
    title = offer.get("title", "")
    description = offer.get("description", "")
    images = offer.get("images", [])
    
    og = {
        "og:title": generate_seo_title(offer),
        "og:description": generate_meta_description(offer),
        "og:type": "website",
        "og:locale": "ar_SA",
        "og:site_name": "مكتب آفاق الإنجاز العقاري",
        "og:url": generate_canonical(offer),
    }
    
    if images:
        og["og:image"] = BASE_URL + images[0]
    else:
        og["og:image"] = BASE_URL + "images/logo.jpg"
    
    return og

def generate_twitter_tags(offer):
    """Generate Twitter Card tags."""
    images = offer.get("images", [])
    
    tw = {
        "twitter:card": "summary_large_image",
        "twitter:title": generate_seo_title(offer),
        "twitter:description": generate_meta_description(offer),
    }
    
    if images:
        tw["twitter:image"] = BASE_URL + images[0]
    else:
        tw["twitter:image"] = BASE_URL + "images/logo.jpg"
    
    return tw

def generate_alt_text(offer, image_index=0):
    """Generate bilingual ALT text for property images."""
    title = offer.get("title", "")
    area = offer.get("area", "")
    area_en = offer.get("area_en", "")
    type_ = offer.get("type", "property")
    kw = TYPE_KEYWORDS.get(type_, TYPE_KEYWORDS["land"])
    
    alt_ar = f"{title}"
    if area:
        alt_ar += f" — {kw['ar']} في {area}"
    alt_ar += " — آفاق الإنجاز العقاري"
    
    alt_en = f"{kw['en']}"
    if area_en:
        alt_en += f" in {area_en}"
    alt_en += " — Afaq Al-Injaz Real Estate"
    
    if image_index > 0:
        alt_ar += f" (صورة {image_index + 1})"
        alt_en += f" (image {image_index + 1})"
    
    return f"{alt_ar} | {alt_en}"

def generate_internal_links(offer):
    """Generate relevant internal links for the property page."""
    type_ = offer.get("type", "property")
    area = offer.get("area", "")
    kw = TYPE_KEYWORDS.get(type_, TYPE_KEYWORDS["land"])
    section = kw["section"]
    
    links = []
    
    # Section page
    section_map = {"مزارع": "farms.html", "استراحات": "resthouses.html", 
                   "أراضي": "lands.html", "خدمات": "services.html"}
    if section in section_map:
        links.append({"text": f"{kw['ar']} في الرياض والخرج", "href": section_map[section]})
    
    # Area-specific landing pages
    if "الرياض" in area or "Riyadh" in area:
        if section == "مزارع":
            links.append({"text": "مزارع للبيع في الرياض", "href": "farms-riyadh/"})
        elif section == "استراحات":
            links.append({"text": "استراحات للبيع في الرياض", "href": "resthouses-riyadh/"})
        elif section == "أراضي":
            links.append({"text": "أراضي للبيع في الرياض", "href": "lands-riyadh/"})
        links.append({"text": "عقارات في الرياض", "href": "real-estate-riyadh/"})
    elif "الخرج" in area or "Al-Kharj" in area or "الرحمانية" in area or "الدلم" in area:
        if section == "مزارع":
            links.append({"text": "مزارع للبيع في الخرج", "href": "farms-alkharj/"})
        elif section == "استراحات":
            links.append({"text": "استراحات للبيع في الخرج", "href": "resthouses-alkharj/"})
        elif section == "أراضي":
            links.append({"text": "أراضي للبيع في الخرج", "href": "lands-alkharj/"})
        links.append({"text": "عقارات في الخرج", "href": "real-estate-alkharj/"})
    
    # Service links
    if type_ in ["service", "well_drilling", "property_management"]:
        links.append({"text": "حفر الآبار في الرياض", "href": "well-drilling-services/"})
        links.append({"text": "تحديد مواقع الآبار", "href": "well-location-services/"})
        links.append({"text": "إدارة الأملاك العقارية", "href": "property-management-riyadh/"})
    
    # Standard links
    links.append({"text": "تواصل معنا", "href": "contact.html"})
    links.append({"text": "طلب عقار", "href": "inquiry.html"})
    
    return links

# ========== Full SEO Generation ==========
def generate_full_seo(offer):
    """
    توليد جميع عناصر SEO لعقار جديد.
    Generate all SEO elements for a new property/offer.
    
    Returns dict with all SEO elements.
    """
    # First check for duplicates
    is_dup, existing_id, similarity = check_duplicate(
        offer.get("title", ""),
        offer.get("area", ""),
        offer.get("type", "property")
    )
    
    if is_dup:
        return {
            "status": "duplicate",
            "existing_id": existing_id,
            "similarity": similarity,
            "message": f"تم العثور على عقار مشابه (ID: {existing_id}, تشابه: {similarity:.0%}). لا يمكن إنشاء نسخة مكررة."
        }
    
    # Generate all SEO elements
    seo_data = {
        "status": "ok",
        "offer_id": offer.get("id", ""),
        "seo_title": generate_seo_title(offer),
        "meta_description": generate_meta_description(offer),
        "keywords": generate_keywords(offer),
        "canonical": generate_canonical(offer),
        "schema_jsonld": generate_schema_jsonld(offer),
        "open_graph": generate_og_tags(offer),
        "twitter_card": generate_twitter_tags(offer),
        "alt_texts": [generate_alt_text(offer, i) for i in range(len(offer.get("images", [""])))],
        "internal_links": generate_internal_links(offer),
        "generated_at": datetime.now().isoformat(),
    }
    
    return seo_data

def generate_html_head_tags(seo_data):
    """
    توليد وسوم HTML head من بيانات SEO.
    Generate HTML head tags from SEO data.
    """
    tags = []
    
    # Title
    tags.append(f'    <title>{seo_data["seo_title"]}</title>')
    
    # Meta description
    tags.append(f'    <meta name="description" content="{seo_data["meta_description"]}">')
    
    # Keywords
    tags.append(f'    <meta name="keywords" content="{seo_data["keywords"]}">')
    
    # Robots
    tags.append('    <meta name="robots" content="index, follow">')
    
    # Language
    tags.append('    <meta name="language" content="Arabic">')
    
    # Geo tags
    tags.append('    <meta name="geo.region" content="SA-12">')
    tags.append('    <meta name="geo.placename" content="الخرج، الرياض">')
    tags.append('    <meta name="geo.position" content="24.1551;47.3104">')
    tags.append('    <meta name="ICBM" content="24.1551, 47.3104">')
    
    # Canonical
    tags.append(f'    <link rel="canonical" href="{seo_data["canonical"]}">')
    
    # Open Graph
    for prop, value in seo_data["open_graph"].items():
        tags.append(f'    <meta property="{prop}" content="{value}">')
    
    # Twitter Card
    for name, value in seo_data["twitter_card"].items():
        tags.append(f'    <meta name="{name}" content="{value}">')
    
    # Schema JSON-LD
    for schema in seo_data["schema_jsonld"]:
        tags.append('    <script type="application/ld+json">')
        tags.append(json.dumps(schema, ensure_ascii=False, indent=4))
        tags.append('    </script>')
    
    return "\n".join(tags)

# ========== Backup before delete ==========
def create_backup_before_delete(file_path, backup_dir="bot/data/backups"):
    """
    إنشاء نسخة احتياطية قبل حذف أي ملف.
    Create backup before deleting any file.
    """
    backup_path = WEBSITE_DIR / backup_dir
    backup_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(file_path)
    backup_file = backup_path / f"{filename}.backup_{timestamp}"
    
    import shutil
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_file)
        return str(backup_file)
    return None

# ========== CLI Entry Point ==========
if __name__ == "__main__":
    # Test with a sample offer
    sample_offer = {
        "id": "TEST-001",
        "type": "farm",
        "title": "مزرعة زراعية جديدة في الخرج",
        "area": "الخرج",
        "area_en": "Al-Kharj",
        "size_sqm": 5000,
        "price": 800000,
        "price_text": "800,000 ريال",
        "description": "مزرعة زراعية خصبة في الخرج بمساحة 5000 متر مربع، تشمل بئر ماء و شبكة ري.",
        "features": ["بئر ماء", "شبكة ري", "أرض صالحة للزراعة"],
        "images": ["images/farms-bg.jpg"],
        "section": "مزارع",
        "property_type": "مزرعة",
    }
    
    print("=" * 60)
    print("🧪 SEO Automation System Test")
    print("=" * 60)
    
    seo = generate_full_seo(sample_offer)
    print(f"\nStatus: {seo['status']}")
    
    if seo['status'] == 'ok':
        print(f"\n📌 SEO Title: {seo['seo_title']}")
        print(f"\n📌 Meta Description: {seo['meta_description']}")
        print(f"\n📌 Keywords: {seo['keywords']}")
        print(f"\n📌 Canonical: {seo['canonical']}")
        print(f"\n📌 ALT Text: {seo['alt_texts']}")
        print(f"\n📌 Internal Links: {len(seo['internal_links'])} links")
        print(f"\n📌 Schema: {len(seo['schema_jsonld'])} blocks")
        
        print("\n" + "=" * 60)
        print("📄 Generated HTML Head Tags:")
        print("=" * 60)
        print(generate_html_head_tags(seo))
    else:
        print(f"\n⚠️ {seo['message']}")
