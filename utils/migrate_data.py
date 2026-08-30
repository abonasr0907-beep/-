#!/usr/bin/env python3
"""
سكربت ترحيل البيانات من offers-data/offers.json إلى data/properties.json
تشغيل: python utils/migrate_data.py
"""

import json
from pathlib import Path

# المسارات
OFFERS_FILE = Path("offers-data/offers.json")
PROPERTIES_FILE = Path("data/properties.json")

def migrate():
    if not OFFERS_FILE.exists():
        print(f"⚠️ {OFFERS_FILE} not found.")
        return

    # اقرأ offers.json
    with open(OFFERS_FILE, "r", encoding="utf-8") as f:
        offers_data = json.load(f)

    offers = offers_data.get("offers", [])

    # حوّل التنسيق
    properties = []
    for offer in offers:
        prop = {
            "id": offer.get("id", ""),
            "type": offer.get("type", ""),  # farm, resthouse, land
            "title": offer.get("title", ""),
            "location": offer.get("area", "الخرج"),
            "area": offer.get("size_sqm", 0),
            "size_sqm": offer.get("size_sqm", 0),
            "price": offer.get("price", 0),
            "description": offer.get("description", ""),
            "features": offer.get("features", []),
            "photos": offer.get("images", []),
            "photo_urls": offer.get("images", []),
            "images": offer.get("images", []),
            "map_link": offer.get("map_link", ""),
            "date_added": offer.get("date_added", ""),
            "date": offer.get("date_added", ""),
            "created_at": offer.get("date_added", ""),
            "is_vip": offer.get("featured", False),
            "featured": offer.get("featured", False),
            "status": "active",
            "property_link": f"https://abonasr0907-beep.github.io/?p={offer.get('id', '')}",
        }
        properties.append(prop)

    # احفظ في properties.json
    PROPERTIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROPERTIES_FILE, "w", encoding="utf-8") as f:
        json.dump({"properties": properties}, f, ensure_ascii=False, indent=2)

    print(f"✅ تم ترحيل {len(properties)} عقار بنجاح!")
    print(f"📁 الملف الجديد: {PROPERTIES_FILE}")

if __name__ == "__main__":
    migrate()
