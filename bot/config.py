"""
الوحدة المركزية للإعدادات والمسارات - Single Source of Truth
مهمة M18: حصانة جذرية ضد الأعطال المتكررة
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# المسارات الرئيسية
REPO_ROOT = Path(__file__).resolve().parent.parent
OFFERS_PATH = REPO_ROOT / "offers-data" / "offers.json"
MANAGERS_PATH = REPO_ROOT / "data" / "managers.json"
CONFIG_JSON_PATH = Path(__file__).resolve().parent / "config.json"
INDEX_PATH = REPO_ROOT / "offers-index.json"

OWNER_ID = 7746757675
SITE_BASE_URL = "https://urldra.cloud.huawei.com/BExUoXngu4"


def is_owner(user_id) -> bool:
    """التحقق المباشر من المالك قراءة حية من MANAGERS_PATH أو CONFIG_OWNER_ID"""
    if user_id is None:
        return False
    uid = str(user_id).strip()
    if uid == str(OWNER_ID):
        return True
    if MANAGERS_PATH.exists():
        try:
            with open(MANAGERS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for m in data.get("managers", []):
                m_id = str(m.get("id") or m.get("telegram_id") or "").strip()
                if m_id == uid and m.get("role") == "owner" and m.get("status", "active") != "suspended":
                    return True
        except Exception as e:
            logger.error(f"Error checking is_owner from {MANAGERS_PATH}: {e}")
    return False


def is_manager(user_id) -> bool:
    """التحقق المباشر من صفة المدير قراءة حية من MANAGERS_PATH بدون كاش وبدون استهلاك"""
    if user_id is None:
        return False
    uid = str(user_id).strip()
    if is_owner(uid):
        return True
    if MANAGERS_PATH.exists():
        try:
            with open(MANAGERS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for m in data.get("managers", []):
                m_id = str(m.get("id") or m.get("telegram_id") or "").strip()
                if m_id == uid and m.get("status", "active") != "suspended":
                    return True
        except Exception as e:
            logger.error(f"Error checking is_manager from {MANAGERS_PATH}: {e}")
    return False


def load_config() -> dict:
    if CONFIG_JSON_PATH.exists():
        try:
            with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading config.json: {e}")
    return {}


def normalize_offer_video(offer: dict) -> dict:
    """تطبيع وحظر حقول الفيديو المزدوجة إلى video_url فقط"""
    if not isinstance(offer, dict):
        return offer
    v_url = offer.get("video_url") or offer.get("youtube_url") or offer.get("tour_url") or ""
    if v_url and str(v_url).strip():
        offer["video_url"] = str(v_url).strip()
    else:
        offer.pop("video_url", None)
    offer.pop("youtube_url", None)
    offer.pop("tour_url", None)
    return offer

def read_offers_live() -> dict:
    """قراءة حية عند الطلب من OFFERS_PATH بدون كاش مع تطبيع الفيديو"""
    if not OFFERS_PATH.exists():
        return {"offers": []}
    try:
        with open(OFFERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        offers = data.get("offers", [])
        for o in offers:
            normalize_offer_video(o)
        return data
    except Exception as e:
        logger.error(f"Error reading offers live from {OFFERS_PATH}: {e}")
        return {"offers": []}


def save_offers_live(data: dict) -> bool:
    """حفظ مباشر في OFFERS_PATH وحفظ تحديث الفهرس النحيف"""
    try:
        OFFERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OFFERS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        generate_offers_index(data)
        return True
    except Exception as e:
        logger.error(f"Error saving offers live to {OFFERS_PATH}: {e}")
        return False


def generate_offers_index(offers_data: dict = None) -> dict:
    """توليد ملف offers-index.json النحيف المخصص للتحميل السريع"""
    if offers_data is None:
        offers_data = read_offers_live()
    raw_offers = offers_data.get("offers", [])
    index_items = []
    for o in raw_offers:
        video_val = o.get("video_url") or o.get("youtube_url") or o.get("tour_url") or ""
        thumb = o.get("thumbnail") or (o.get("images", [""])[0] if o.get("images") else "")
        cat = o.get("category") or o.get("property_type") or o.get("section") or ""
        o_type = o.get("type")
        if not o_type:
            cat_str = str(cat)
            if "مزرع" in cat_str:
                o_type = "farm"
            elif "استراح" in cat_str:
                o_type = "resthouse"
            else:
                o_type = "land"

        item = {
            "id": o.get("id", ""),
            "title": o.get("title", ""),
            "price": o.get("price", 0),
            "price_text": o.get("price_text", ""),
            "thumbnail": thumb,
            "images": [thumb] if thumb else ["images/farms-bg.jpg"],
            "area": o.get("area", ""),
            "category": cat,
            "property_type": o.get("property_type") or cat,
            "type": o_type,
            "video_flag": bool(video_val and str(video_val).strip()),
            "video_url": str(video_val).strip() if video_val else "",
            "status": o.get("status", "published") or "published",
            "featured": o.get("featured", False),
            "sold": o.get("sold", False),
            "operation_type": o.get("operation_type", "sale"),
            "map_link": o.get("map_link", "")
        }
        index_items.append(item)
    index_payload = {"offers": index_items, "count": len(index_items)}
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving offers-index.json: {e}")
    return index_payload
