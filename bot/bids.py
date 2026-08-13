#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bids.py — مخزن المزايدات (Phase 2)

حقول السجل: id, listing_id, bidder_name, bidder_phone, amount,
            status (pending|approved|rejected), created_at, reviewed_by

القاعدة الذهبية: سعر العقار و current_bid لا يتغيران تلقائيًا أبدًا.
/approve_bid هو فقط من يحدّث current_bid يدويًا وبعد موافقة صريحة.
"""

import json
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# مسار ملف المزايدات — يُمرّر من bot.py
_BIDS_FILE = None


def init(bids_file):
    """تعيين مسار bids.json (يُستدعى مرة واحدة من bot.py عند الإقلاع)."""
    global _BIDS_FILE
    _BIDS_FILE = bids_file


def _path():
    return _BIDS_FILE


def load_bids():
    """تحميل سجلات المزايدات. يُرجع دائمًا {bids: [...]}."""
    p = _path()
    if p and os.path.exists(str(p)):
        try:
            with open(str(p), "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "bids" in data:
                return data
            return {"bids": []}
        except Exception:
            return {"bids": []}
    return {"bids": []}


def save_bids(data):
    """حفظ آمن (atomic) لسجلات المزايدات."""
    p = _path()
    if not p:
        return
    tmp = str(p) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(p))


def _new_id():
    """معرّف فريد للمزايدة: BID-<timestamp>-<short>"""
    return f"BID-{int(time.time())}-{os.urandom(3).hex()}"


def add_bid(listing_id, bidder_name, bidder_phone, amount, extra=None):
    """
    إضافة مزايدة جديدة بحالة pending.
    لا يُغيّر سعر العقار أو current_bid — مجرد تخزين السجل فقط.
    يُرجع السجل المنشأ.
    """
    try:
        amt = float(str(amount).replace(",", ""))
    except (ValueError, TypeError):
        raise ValueError("amount غير صالح")

    data = load_bids()
    record = {
        "id": _new_id(),
        "listing_id": str(listing_id),
        "bidder_name": str(bidder_name or "").strip(),
        "bidder_phone": str(bidder_phone or "").strip(),
        "amount": amt,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reviewed_by": None,
    }
    if isinstance(extra, dict):
        for k in ("offerTitle", "offerUrl"):
            if k in extra:
                record[k] = extra[k]
    data.setdefault("bids", []).append(record)
    save_bids(data)
    logger.info(f"تم حفظ مزايدة {record['id']} للعقار {listing_id} بمبلغ {amt}")
    return record


def get_pending():
    """قائمة المزايدات بحالة pending فقط."""
    data = load_bids()
    return [b for b in data.get("bids", []) if b.get("status") == "pending"]


def get_all():
    """كل سجلات المزايدات."""
    data = load_bids()
    return data.get("bids", [])


def find_bid(bid_id):
    """البحث عن سجل مزايدة بمعرّفه. يُرجع (السجل, الفهرس) أو (None, -1)."""
    data = load_bids()
    for i, b in enumerate(data.get("bids", [])):
        if str(b.get("id", "")) == str(bid_id):
            return b, i
    return None, -1


def set_status(bid_id, status, reviewer_id):
    """
    تحديث حالة المزايدة (approved / rejected).
    يُرجع السجل المحدّث أو None إذا لم يُوجد.
    لا يُغيّر سعر العقار — المُستدعي (bot.py) مسؤول عن تحديث
    current_bid يدويًا عند الموافقة الصريحة فقط.
    """
    if status not in ("approved", "rejected"):
        raise ValueError("status يجب أن يكون approved أو rejected")
    data = load_bids()
    for b in data.get("bids", []):
        if str(b.get("id", "")) == str(bid_id):
            b["status"] = status
            b["reviewed_by"] = reviewer_id
            b["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_bids(data)
            logger.info(f"تم تحديث مزايدة {bid_id} → {status} بواسطة {reviewer_id}")
            return b
    return None
