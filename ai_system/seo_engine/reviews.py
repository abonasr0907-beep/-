#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reviews.py — نظام المراجعات الشرعية للمرحلة الثالثة §2.7
=============================================================
يجمع ويعرض المراجعات الحقيقية فقط من العملاء الفعليين.

قواعد صارمة:
  - لا تُولّد مراجعات وهمية أو نجوم عشوائية
  - كل مراجعة يجب أن تكون من عميل فعلي (اسم + رقم جوال للتحقق)
  - المراجعات معلّقة حتى موافقة المدير
  - تُعرض فقط المراجعات المعتمدة (status=approved)
  - يتم توليد AggregateRating من المراجعات المعتمدة فقط
  - idempotent: إضافة نفس المراجعة عدة مرات آمن (dedup by phone+offer_id)

آلية الجمع:
  1. زائر يملأ نموذج مراجعة (اسم، تقييم 1-5، نص، رقم جوال، معرف العرض)
  2. تُحفظ المراجعة كـ pending في reviews.json
  3. المدير يراجع ويوافق/يرفض عبر البوت
  4. عند الموافقة → status=approved → تُعرض على الموقع
  5. AggregateRating يُحسب من المعتمدة فقط
"""

import json
import re
import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("afaq.seo_engine.reviews")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REVIEWS_PATH = BASE_DIR / "offers-data" / "reviews.json"
LEGACY_SITE_URL = "https://abonasr0907-beep.github.io/-/"


def _load_reviews():
    """تحميل المراجعات (آمن)."""
    try:
        if REVIEWS_PATH.exists():
            data = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("reviews", [])
            if isinstance(data, list):
                return data
        return []
    except Exception as e:
        logger.warning(f"تعذّر تحميل reviews.json: {e}")
        return []


def _save_reviews(reviews):
    """حفظ المراجعات (آمن)."""
    try:
        REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"reviews": reviews, "last_updated": datetime.now().isoformat()}
        REVIEWS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"تعذّر حفظ reviews.json: {e}")
        return False


def add_review(name, rating, text, phone, offer_id="", source="website"):
    """
    إضافة مراجعة جديدة (pending — تنتظر موافقة المدير).
    idempotent: dedup by (phone + offer_id).

    يُرجع: dict with 'id', 'status', 'duplicate'
    """
    # تنظيف المدخلات
    name = str(name).strip()[:100]
    text = str(text).strip()[:1000]
    phone = re.sub(r"\D", "", str(phone))
    rating = int(rating) if rating else 0
    if rating < 1:
        rating = 1
    if rating > 5:
        rating = 5

    if not name or not text or not phone:
        return {"id": None, "status": "rejected", "duplicate": False, "error": "missing fields"}

    reviews = _load_reviews()

    # فحص التكرار (dedup by phone + offer_id)
    for r in reviews:
        if r.get("phone") == phone and r.get("offer_id", "") == offer_id:
            return {"id": r.get("id"), "status": r.get("status", "pending"), "duplicate": True}

    # توليد معرف
    review_id = f"REV-{len(reviews) + 1:04d}"
    while any(r.get("id") == review_id for r in reviews):
        num = int(re.search(r"\d+", review_id).group()) + 1
        review_id = f"REV-{num:04d}"

    review = {
        "id": review_id,
        "name": name,
        "rating": rating,
        "text": text,
        "phone": phone,
        "offer_id": offer_id,
        "source": source,
        "status": "pending",  # ينتظر موافقة المدير
        "date_added": datetime.now().strftime("%Y-%m-%d"),
    }

    reviews.append(review)
    _save_reviews(reviews)

    logger.info(f"تمت إضافة مراجعة جديدة: {review_id} (pending)")
    return {"id": review_id, "status": "pending", "duplicate": False}


def approve_review(review_id):
    """موافقة المدير على مراجعة (pending → approved)."""
    reviews = _load_reviews()
    for r in reviews:
        if r.get("id") == review_id:
            r["status"] = "approved"
            r["approved_date"] = datetime.now().strftime("%Y-%m-%d")
            _save_reviews(reviews)
            logger.info(f"تمت الموافقة على مراجعة: {review_id}")
            return True
    return False


def reject_review(review_id, reason=""):
    """رفض مراجعة (pending → rejected)."""
    reviews = _load_reviews()
    for r in reviews:
        if r.get("id") == review_id:
            r["status"] = "rejected"
            if reason:
                r["reject_reason"] = reason
            _save_reviews(reviews)
            logger.info(f"تم رفض مراجعة: {review_id}")
            return True
    return False


def get_approved_reviews(offer_id=None, limit=100):
    """
    الحصول على المراجعات المعتمدة فقط.
    offer_id: فلترة حسب عرض معين (اختياري).
    limit: الحد الأقصى.
    """
    reviews = _load_reviews()
    approved = [r for r in reviews if r.get("status") == "approved"]
    if offer_id:
        approved = [r for r in approved if r.get("offer_id") == offer_id]
    return approved[:limit]


def get_pending_reviews():
    """الحصول على المراجعات المعلقة (للمدير)."""
    reviews = _load_reviews()
    return [r for r in reviews if r.get("status") == "pending"]


def calculate_aggregate_rating(offer_id=None):
    """
    حساب AggregateRating من المراجعات المعتمدة فقط.
    يُرجع dict جاهز لـ Schema.org أو None إذا لا توجد مراجعات معتمدة.
    """
    approved = get_approved_reviews(offer_id)
    if not approved:
        return None

    total = sum(r.get("rating", 0) for r in approved)
    count = len(approved)
    avg = round(total / count, 1) if count > 0 else 0

    return {
        "@type": "AggregateRating",
        "ratingValue": str(avg),
        "reviewCount": str(count),
        "bestRating": "5",
        "worstRating": "1",
    }


def generate_review_schema(review):
    """توليد Schema من نوع Review لمراجعة واحدة."""
    return {
        "@type": "Review",
        "author": {
            "@type": "Person",
            "name": review.get("name", "عميل"),
        },
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": str(review.get("rating", 5)),
            "bestRating": "5",
            "worstRating": "1",
        },
        "reviewBody": review.get("text", ""),
        "datePublished": review.get("approved_date", review.get("date_added", "")),
    }


def get_reviews_for_schema(offer_id=None):
    """
    الحصول على AggregateRating + قائمة Review schemas لعرض معين.
    يُرجع dict بـ aggregateRating و reviews (list of Review schemas) أو None.
    """
    approved = get_approved_reviews(offer_id)
    if not approved:
        return None

    aggregate = calculate_aggregate_rating(offer_id)
    review_schemas = [generate_review_schema(r) for r in approved[:20]]  # حد أقصى 20

    return {
        "aggregateRating": aggregate,
        "reviews": review_schemas,
        "count": len(approved),
    }


# ============================================================
# اختبار ذاتي
# ============================================================
def _self_test():
    print("=== reviews self-test ===")

    # إضافة مراجعة
    r1 = add_review("أحمد محمد", 5, "خدمة ممتازة وتعامل راقي", "0501234567", offer_id="FRM-001")
    assert r1["id"], "Add review failed"
    assert r1["status"] == "pending", "New review should be pending"
    print(f"  Add review: {r1['id']} pending — OK")

    # Dedup
    r1_dup = add_review("أحمد محمد", 4, "نص آخر", "0501234567", offer_id="FRM-001")
    assert r1_dup["duplicate"] == True, "Dedup failed"
    print("  Dedup — OK")

    # Approve
    assert approve_review(r1["id"]), "Approve failed"
    approved = get_approved_reviews()
    assert any(r["id"] == r1["id"] for r in approved), "Approved review not found"
    print("  Approve — OK")

    # Aggregate rating
    agg = calculate_aggregate_rating("FRM-001")
    assert agg is not None, "Aggregate rating None"
    assert agg["@type"] == "AggregateRating", "Aggregate type wrong"
    assert agg["reviewCount"] == "1", f"Review count wrong: {agg['reviewCount']}"
    print(f"  AggregateRating: {agg['ratingValue']} ({agg['reviewCount']} reviews) — OK")

    # Schema
    schemas = get_reviews_for_schema("FRM-001")
    assert schemas, "Reviews schema None"
    assert len(schemas["reviews"]) == 1, "Reviews schema count wrong"
    print("  Reviews schema — OK")

    # Reject
    r2 = add_review("سامي", 3, "مراجعة للاختبار", "0509876543", offer_id="FRM-002")
    assert reject_review(r2["id"], "محتوى غير مناسب"), "Reject failed"
    pending = get_pending_reviews()
    assert not any(r["id"] == r2["id"] for r in pending), "Rejected review still pending"
    print("  Reject — OK")

    print("=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    _self_test()
