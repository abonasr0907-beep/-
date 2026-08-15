import re
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq_guardian.link_guardian")

def derive_canonical_offer_path(external_id: str, title_or_category: str = "", area: str = "") -> str:
    """قانون موحد لاشتقاق رابط العرض: /offer/{external_id}/{slug}"""
    eid = str(external_id or "").strip()
    if not eid:
        eid = "unknown"

    raw_text = (str(title_or_category) + " " + str(area)).strip()
    clean_text = re.sub(r'[^\w\s-]', '', raw_text, flags=re.UNICODE)
    slug = re.sub(r'[\s_]+', '-', clean_text).strip('-')
    if not slug:
        slug = "property"
    return "/offer/" + eid + "/" + slug


def verify_and_repair_offer_links(offers_file_path: Path) -> dict:
    """فحص سلامة الروابط وإصلاح الكسر بمستوى LOW مع تقرير خفي"""
    if not offers_file_path.exists():
        return {"ok": False, "error": "file_not_found"}

    try:
        with open(offers_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    offers = data.get("offers", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    repaired_count = 0
    repaired_details = []

    for offer in offers:
        eid = str(offer.get("external_id") or offer.get("id") or "")
        if not eid:
            continue

        expected_path = derive_canonical_offer_path(
            eid,
            offer.get("title") or offer.get("category", ""),
            offer.get("area") or offer.get("location", "")
        )

        current_url = str(offer.get("url") or offer.get("canonical_url") or "")

        if expected_path not in current_url:
            repaired_count += 1
            offer["url"] = expected_path
            offer["canonical_url"] = expected_path
            offer["link_repaired_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            offer["link_repair_severity"] = "LOW"
            repaired_details.append({
                "id": eid,
                "old": current_url,
                "new": expected_path
            })

    if repaired_count > 0:
        if isinstance(data, dict):
            data["offers"] = offers
        try:
            with open(offers_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("فشل حفظ إصلاح الروابط: " + str(e))

    return {
        "ok": True,
        "total_checked": len(offers),
        "repaired_count": repaired_count,
        "repaired_details": repaired_details
    }
