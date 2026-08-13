#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
listing_lifecycle.py — نظام دورة حياة العقار (Phase 3: Bot & Listing Lifecycle)

يدير هذا الموديول:
  1. جدول العقارات (listings) بحقول جديدة:
     - external_id (UUID دائم)
     - slug (للرابط الدائم /offer/{external_id}/{slug})
     - status (draft / pending / published / rejected / archived)
     - source (bot_manager / bot_visitor / site_visitor / site_manager /
               approved_site_as_bot / legacy)
     - created_by_role, created_by_user_id, approved_by_user_id
     - published_at, category, title, description, marketing_text
     - price_mode (sale / sum / auction), price, sum_price, current_bid,
       allow_bidding, lat, lng, location_text
     - old_id (رابط بالعقار القديم للحفاظ على الـ URL المفهرس)

  2. جدول صور العقارات (listing_images):
     - id, listing_id (external_id), image_url, telegram_file_id,
       alt_ar, alt_en, sort_order, created_at

  3. Backfill آمن: قراءة offers.json الموجود وإنشاء سجلات listings
     بـ external_id + slug + status=published + source=legacy،
     مع الحفاظ على الـ id القديم في old_id (لا حذف، لا تغيير للروابط).

قواعد صارمة:
  - التخزين ADD-ONLY (إضافة فقط، لا حذف لجدول/عمود/سجل قديم)
  - الكتابة ذرّية (atomic) مع thread lock
  - لا يتم لمس offers.json الأصلي (يُقرأ فقط للـ backfill)
  - لا يتم لمس sitemap.xml / robots.txt / Google Search Console

التخزين: bot/data/listings.json + bot/data/listing_images.json
"""

import json
import logging
import re
import threading
import uuid as _uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("afaq_bot.listing_lifecycle")

# ============================================================
#  المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LISTINGS_FILE = DATA_DIR / "listings.json"
LISTING_IMAGES_FILE = DATA_DIR / "listing_images.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  ثوابت الحالات والمصادر
# ============================================================
# حالات العقار
STATUS_DRAFT = "draft"          # مسودة (لم تُرسل بعد)
STATUS_PENDING = "pending"      # بانتظار المراجعة/الاعتماد
STATUS_PUBLISHED = "published"  # منشور ومرئي للزوار
STATUS_REJECTED = "rejected"    # مرفوض (غير مرئي)
STATUS_ARCHIVED = "archived"    # مؤرشف (غير مرئي)

# الحالات المرئية للزوار (فقط هذه تظهر على الموقع)
VISIBLE_STATUSES = (STATUS_PUBLISHED,)

# مصادر العقار
SOURCE_BOT_MANAGER = "bot_manager"            # مدير أضاف عبر البوت
SOURCE_BOT_VISITOR = "bot_visitor"            # زائر أضاف عبر البوت
SOURCE_SITE_VISITOR = "site_visitor"          # زائر أضاف عبر الموقع
SOURCE_SITE_MANAGER = "site_manager"          # مدير أضاف عبر الموقع
SOURCE_APPROVED_SITE_AS_BOT = "approved_site_as_bot"  # عرض موقع اعتمده مدير
SOURCE_LEGACY = "legacy"                       # عقار قديم (backfill)

# أوضاع التسعير
PRICE_MODE_SALE = "sale"       # بيع
PRICE_MODE_SUM = "sum"         # مبلغ مقطوع
PRICE_MODE_AUCTION = "auction"  # مزاد

ALL_STATUSES = (
    STATUS_DRAFT, STATUS_PENDING, STATUS_PUBLISHED,
    STATUS_REJECTED, STATUS_ARCHIVED,
)

ALL_SOURCES = (
    SOURCE_BOT_MANAGER, SOURCE_BOT_VISITOR,
    SOURCE_SITE_VISITOR, SOURCE_SITE_MANAGER,
    SOURCE_APPROVED_SITE_AS_BOT, SOURCE_LEGACY,
)

# ============================================================
#  التخزين (thread-safe, atomic writes)
# ============================================================
_lock = threading.Lock()
_listings = {}          # external_id -> listing dict
_listing_images = []    # list of image dicts
_initialized = False


def _load_listings():
    """تحميل listings.json (أو إنشاء ملف فارغ)."""
    global _listings
    if LISTINGS_FILE.exists():
        try:
            with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _listings = data.get("listings", {}) if isinstance(data, dict) else {}
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"listings.json تالف أو غير قابل للقراءة: {e} — بدء بجدول فارغ")
            _listings = {}
    else:
        _listings = {}


def _load_listing_images():
    """تحميل listing_images.json (أو إنشاء ملف فارغ)."""
    global _listing_images
    if LISTING_IMAGES_FILE.exists():
        try:
            with open(LISTING_IMAGES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _listing_images = data.get("images", []) if isinstance(data, dict) else []
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"listing_images.json تالف: {e} — بدء بقائمة فارغة")
            _listing_images = []
    else:
        _listing_images = []


def _save_listings():
    """حفظ ذرّي لـ listings.json."""
    tmp = LISTINGS_FILE.with_suffix(".json.tmp")
    payload = {"listings": _listings, "_version": 1, "_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(LISTINGS_FILE)


def _save_listing_images():
    """حفظ ذرّي لـ listing_images.json."""
    tmp = LISTING_IMAGES_FILE.with_suffix(".json.tmp")
    payload = {"images": _listing_images, "_version": 1, "_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(LISTING_IMAGES_FILE)


def init():
    """تهيئة الموديول (تحميل الملفات). آمن للاستدعاء المتكرر."""
    global _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        _load_listings()
        _load_listing_images()
        _initialized = True
        logger.info(f"listing_lifecycle: تم تحميل {len(_listings)} عقار و {len(_listing_images)} صورة")


# ============================================================
#  أدوات مساعدة
# ============================================================
_ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
_NON_SLUG_CHARS = re.compile(r'[^a-zA-Z0-9\u0600-\u06FF\u0750-\u077F-]')


def generate_external_id() -> str:
    """توليد external_id فريد (UUID4 hex بدون شرطات)."""
    return _uuid.uuid4().hex


def slugify(text: str, max_len: int = 60) -> str:
    """
    توليد slug من نص عربي/إنجليزي.
    - يحوّل المسافات إلى شرطات
    - يحذف الرموز الخاصة (يبقي الحروف العربية والإنجليزية والأرقام والشرطة)
    - يقتصر على max_len حرف
    - إذا كان النص فارغاً يرجع 'listing'
    """
    if not text or not text.strip():
        return "listing"
    slug = text.strip()
    # حذف الرموز الخاصة مع الإبقاء على العربية والإنجليزية والأرقام والشرطة
    slug = _NON_SLUG_CHARS.sub('-', slug)
    # دمج الشرطات المتتالية
    slug = re.sub(r'-+', '-', slug)
    # حذف الشرطات من البداية والنهاية
    slug = slug.strip('-')
    if not slug:
        return "listing"
    # اقتطاع إلى max_len (مع مراعاة عدم قطع كلمة)
    if len(slug) > max_len:
        slug = slug[:max_len].rsplit('-', 1)[0] if '-' in slug[:max_len] else slug[:max_len]
        slug = slug.strip('-')
    return slug or "listing"


def generate_slug(title: str, existing_slugs: set = None) -> str:
    """
    توليد slug فريد من العنوان. إذا كان موجوداً يضيف لاحقة رقمية.
    """
    base = slugify(title)
    if existing_slugs is None:
        existing_slugs = set()
        with _lock:
            for lst in _listings.values():
                s = lst.get("slug")
                if s:
                    existing_slugs.add(s)
    slug = base
    counter = 2
    while slug in existing_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


# ============================================================
#  إنشاء / تحديث العقار
# ============================================================
def create_listing(
    *,
    external_id: str = None,
    old_id: str = None,
    slug: str = None,
    title: str = "",
    category: str = "",
    description: str = "",
    marketing_text: str = "",
    status: str = STATUS_DRAFT,
    source: str = SOURCE_BOT_MANAGER,
    created_by_role: str = "",
    created_by_user_id: str = "",
    approved_by_user_id: str = "",
    published_at: str = "",
    price_mode: str = PRICE_MODE_SALE,
    price: float = None,
    sum_price: float = None,
    current_bid: float = None,
    allow_bidding: bool = False,
    lat: float = None,
    lng: float = None,
    location_text: str = "",
    extra: dict = None,
) -> dict:
    """
    إنشاء عقار جديد في جدول listings.
    يرجع السجل المنشأ. لا يحفظ تلقائياً في offers.json (هذا منفصل).
    """
    init()
    if external_id is None:
        external_id = generate_external_id()
    if slug is None:
        slug = generate_slug(title)
    if status not in ALL_STATUSES:
        status = STATUS_DRAFT
    if source not in ALL_SOURCES:
        source = SOURCE_BOT_MANAGER
    if price_mode not in (PRICE_MODE_SALE, PRICE_MODE_SUM, PRICE_MODE_AUCTION):
        price_mode = PRICE_MODE_SALE

    listing = {
        "external_id": external_id,
        "old_id": old_id or "",
        "slug": slug,
        "status": status,
        "source": source,
        "created_by_role": created_by_role,
        "created_by_user_id": str(created_by_user_id) if created_by_user_id else "",
        "approved_by_user_id": str(approved_by_user_id) if approved_by_user_id else "",
        "published_at": published_at,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # المحتوى
        "title": title,
        "category": category,
        "description": description,
        "marketing_text": marketing_text,
        # التسعير
        "price_mode": price_mode,
        "price": price,
        "sum_price": sum_price,
        "current_bid": current_bid,
        "allow_bidding": allow_bidding,
        # الموقع
        "lat": lat,
        "lng": lng,
        "location_text": location_text,
    }
    # حقول إضافية (type, area, size_sqm, images, map_link, featured, ...)
    if extra and isinstance(extra, dict):
        for k, v in extra.items():
            if k not in listing:
                listing[k] = v

    with _lock:
        _listings[external_id] = listing
        _save_listings()

    logger.info(f"create_listing: external_id={external_id} status={status} source={source} title={title[:40]}")
    return listing


def update_listing(external_id: str, updates: dict) -> bool:
    """
    تحديث عقار موجود. ADD-ONLY: لا يحذف حقولاً غير موجودة في updates.
    يرجع True إذا نجح، False إذا لم يوجد العقار.
    """
    init()
    with _lock:
        if external_id not in _listings:
            return False
        listing = _listings[external_id]
        for k, v in updates.items():
            listing[k] = v
        listing["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _save_listings()
    logger.info(f"update_listing: {external_id} updated {len(updates)} field(s)")
    return True


def set_status(external_id: str, new_status: str, approved_by_user_id: str = "") -> bool:
    """تغيير حالة العقار. إذا نُشر، يسجل published_at."""
    init()
    if new_status not in ALL_STATUSES:
        return False
    updates = {"status": new_status}
    if new_status == STATUS_PUBLISHED:
        updates["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if approved_by_user_id:
        updates["approved_by_user_id"] = str(approved_by_user_id)
    return update_listing(external_id, updates)


# ============================================================
#  البحث والاستعلام
# ============================================================
def get_listing(external_id: str) -> dict:
    """الحصول على عقار بـ external_id. يرجع None إذا لم يوجد."""
    init()
    with _lock:
        return _listings.get(external_id)


def get_listing_by_old_id(old_id: str) -> dict:
    """الحصول على عقار بـ old_id (للروابط القديمة المفهرسة)."""
    init()
    with _lock:
        for lst in _listings.values():
            if lst.get("old_id") == old_id:
                return lst
    return None


def get_listing_by_slug(slug: str) -> dict:
    """الحصول على عقار بـ slug (للروابط /offer/{external_id}/{slug})."""
    init()
    with _lock:
        for lst in _listings.values():
            if lst.get("slug") == slug:
                return lst
    return None


def get_published_listings() -> list:
    """جميع العقارات المنشورة (المرئية للزوار فقط)."""
    init()
    with _lock:
        return [lst for lst in _listings.values() if lst.get("status") == STATUS_PUBLISHED]


def get_pending_listings() -> list:
    """جميع العقارات بانتظار الاعتماد."""
    init()
    with _lock:
        return [lst for lst in _listings.values() if lst.get("status") == STATUS_PENDING]


def get_all_listings() -> list:
    """جميع العقارات (للمدير فقط)."""
    init()
    with _lock:
        return list(_listings.values())


def get_listings_by_status(status: str) -> list:
    """العقارات بحالة معينة."""
    init()
    if status not in ALL_STATUSES:
        return []
    with _lock:
        return [lst for lst in _listings.values() if lst.get("status") == status]


def count_listings() -> dict:
    """إحصائيات سريعة: عدد العقارات حسب الحالة."""
    init()
    with _lock:
        counts = {s: 0 for s in ALL_STATUSES}
        for lst in _listings.values():
            s = lst.get("status")
            if s in counts:
                counts[s] += 1
        counts["total"] = len(_listings)
        return counts


# ============================================================
#  صور العقارات (listing_images)
# ============================================================
def add_listing_image(
    *,
    listing_id: str,
    image_url: str = "",
    telegram_file_id: str = "",
    alt_ar: str = "",
    alt_en: str = "",
    sort_order: int = 0,
) -> dict:
    """
    إضافة صورة لعقار.
    listing_id = external_id للعقار.
    """
    init()
    img = {
        "id": _uuid.uuid4().hex,
        "listing_id": listing_id,
        "image_url": image_url,
        "telegram_file_id": telegram_file_id,
        "alt_ar": alt_ar,
        "alt_en": alt_en,
        "sort_order": sort_order,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with _lock:
        _listing_images.append(img)
        _save_listing_images()
    logger.info(f"add_listing_image: listing={listing_id} url={image_url[:50]} alt_ar={alt_ar[:30]}")
    return img


def get_listing_images(listing_id: str) -> list:
    """جميع صور عقار معين (مرتبة حسب sort_order)."""
    init()
    with _lock:
        imgs = [img for img in _listing_images if img.get("listing_id") == listing_id]
        imgs.sort(key=lambda x: (x.get("sort_order", 0), x.get("created_at", "")))
        return imgs


def update_image_alt(image_id: str, alt_ar: str = None, alt_en: str = None) -> bool:
    """تحديث النص البديل (alt) لصورة."""
    init()
    with _lock:
        for img in _listing_images:
            if img.get("id") == image_id:
                if alt_ar is not None:
                    img["alt_ar"] = alt_ar
                if alt_en is not None:
                    img["alt_en"] = alt_en
                _save_listing_images()
                return True
    return False


# ============================================================
#  Backfill — استيراد العقارات القديمة من offers.json
# ============================================================
def backfill_from_offers_json(offers_path: str = None, force: bool = False) -> dict:
    """
    Backfill آمن: قراءة offers.json الموجود وإنشاء سجلات listings
    لكل عرض لا يوجد له سجل بعد.

    القواعد:
      - ADD-ONLY: لا يحذف ولا يغيّر أي سجل موجود
      - status=published (لأنها معروضة على الموقع)
      - source=legacy
      - old_id = id القديم (للحفاظ على الرابط المفهرس)
      - لا يلمس offers.json الأصلي (قراءة فقط)
      - إذا force=False، يتخطى العقارات الموجودة بالفعل

    يرجع dict بإحصائيات: {total, imported, skipped, errors}
    """
    init()
    if offers_path is None:
        # المسار الافتراضي: نقطع من bot/ إلى offers-data/
        offers_path = str(BASE_DIR.parent / "offers-data" / "offers.json")

    try:
        with open(offers_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"backfill: تعذر قراءة offers.json من {offers_path}: {e}")
        return {"total": 0, "imported": 0, "skipped": 0, "errors": 1, "error": str(e)}

    offers = data.get("offers", []) if isinstance(data, dict) else data
    if not isinstance(offers, list):
        offers = []

    stats = {"total": len(offers), "imported": 0, "skipped": 0, "errors": 0}

    # بناء set من old_ids الموجودة بالفعل
    with _lock:
        existing_old_ids = {lst.get("old_id") for lst in _listings.values() if lst.get("old_id")}

    existing_slugs = set()
    with _lock:
        for lst in _listings.values():
            s = lst.get("slug")
            if s:
                existing_slugs.add(s)

    for offer in offers:
        old_id = offer.get("id", "")
        if not old_id:
            stats["errors"] += 1
            continue

        # تخطي إذا موجود بالفعل (إلا إذا force=True)
        if old_id in existing_old_ids and not force:
            stats["skipped"] += 1
            continue

        title = offer.get("title", "")
        category = offer.get("category", "") or offer.get("property_type", "")
        description = offer.get("description", "")

        # استخراج الموقع
        location_text = offer.get("area", "") or ""
        lat = offer.get("lat")
        lng = offer.get("lng")
        if lat is not None:
            try:
                lat = float(lat)
            except (TypeError, ValueError):
                lat = None
        if lng is not None:
            try:
                lng = float(lng)
            except (TypeError, ValueError):
                lng = None

        # السعر
        price = offer.get("price")
        if price is not None:
            try:
                price = float(price)
            except (TypeError, ValueError):
                price = None

        # وضع التسعير
        operation_type = offer.get("operation_type", "sale")
        if operation_type == "auction":
            price_mode = PRICE_MODE_AUCTION
        else:
            price_mode = PRICE_MODE_SALE

        slug = generate_slug(title, existing_slugs)
        existing_slugs.add(slug)

        # الحقول الإضافية من offer
        extra = {}
        for k in ("type", "area", "area_en", "size_sqm", "price_text",
                   "features", "images", "map_link", "date_added",
                   "featured", "section", "property_type", "operation_type"):
            if k in offer:
                extra[k] = offer[k]

        try:
            listing = create_listing(
                external_id=generate_external_id(),
                old_id=old_id,
                slug=slug,
                title=title,
                category=category,
                description=description,
                marketing_text="",
                status=STATUS_PUBLISHED,
                source=SOURCE_LEGACY,
                created_by_role="system",
                created_by_user_id="backfill",
                published_at=offer.get("date_added", ""),
                price_mode=price_mode,
                price=price,
                lat=lat,
                lng=lng,
                location_text=location_text,
                extra=extra,
            )
            stats["imported"] += 1
            existing_old_ids.add(old_id)

            # استيراد الصور الموجودة في offer إلى listing_images
            images = offer.get("images", [])
            if isinstance(images, list):
                for idx, img_url in enumerate(images):
                    if isinstance(img_url, str) and img_url:
                        add_listing_image(
                            listing_id=listing["external_id"],
                            image_url=img_url,
                            telegram_file_id="",
                            alt_ar=title,
                            alt_en="",
                            sort_order=idx,
                        )
        except Exception as e:
            logger.error(f"backfill: فشل استيراد {old_id}: {e}")
            stats["errors"] += 1

    logger.info(f"backfill: {stats}")
    return stats


# ============================================================
#  تصدير العقارات إلى صيغة offers.json (للمزامنة مع الموقع)
# ============================================================
def export_published_to_offers_format() -> list:
    """
    تصدير العقارات المنشورة إلى صيغة متوافقة مع offers.json.
    يحافظ على الحقول القديمة (id, type, title, ...) ويضيف الجديدة
    (external_id, slug, status, source).

    القاعدة: العقارات القديمة (legacy) تحتفظ بـ old_id كـ id
    لئلا تتغير الروابط المفهرسة.
    العقارات الجديدة تستخدم external_id كـ id للرابط الدائم.
    """
    init()
    result = []
    with _lock:
        for lst in _listings.values():
            if lst.get("status") != STATUS_PUBLISHED:
                continue
            # للعقارات القديمة: id = old_id (للحفاظ على الرابط)
            # للعقارات الجديدة: id = external_id أو old_id إن وُجد
            offer_id = lst.get("old_id") or lst["external_id"]

            offer = {
                "id": offer_id,
                "external_id": lst["external_id"],
                "slug": lst.get("slug", ""),
                "status": lst.get("status", STATUS_PUBLISHED),
                "source": lst.get("source", SOURCE_LEGACY),
                "type": lst.get("type", ""),
                "category": lst.get("category", ""),
                "title": lst.get("title", ""),
                "area": lst.get("area", ""),
                "area_en": lst.get("area_en", ""),
                "size_sqm": lst.get("size_sqm"),
                "price": lst.get("price"),
                "price_text": lst.get("price_text", ""),
                "description": lst.get("description", ""),
                "marketing_text": lst.get("marketing_text", ""),
                "features": lst.get("features", []),
                "images": lst.get("images", []),
                "map_link": lst.get("map_link", ""),
                "date_added": lst.get("published_at") or lst.get("date_added", ""),
                "featured": lst.get("featured", False),
                "section": lst.get("section", ""),
                "property_type": lst.get("property_type", ""),
                "operation_type": lst.get("operation_type", "sale"),
                # حقول جديدة
                "price_mode": lst.get("price_mode", PRICE_MODE_SALE),
                "location_text": lst.get("location_text", ""),
                "lat": lst.get("lat"),
                "lng": lst.get("lng"),
            }
            # حذف الحقول الفارغة (لتنظيف JSON)
            offer = {k: v for k, v in offer.items() if v is not None and v != ""}
            result.append(offer)
    return result


# ============================================================
#  سجل التدقيق (Audit) لأفعال العقارات
# ============================================================
def log_listing_action(
    action: str,
    external_id: str,
    performed_by_user_id: str,
    performed_by_role: str,
    detail: str = "",
):
    """
    تسجيل إجراء على عقار في سجل التدقيق.
    يستخدم نظام audit_log الموجود في user_manager.log_audit.
    الأفعال: listing_created / listing_edited / listing_published /
             listing_rejected / listing_approved / listing_archived
    """
    try:
        import user_manager
        user_manager.log_audit(
            action=action,
            performed_by=performed_by_user_id,
            detail=f"[{performed_by_role}] listing={external_id} {detail}".strip(),
        )
    except Exception as e:
        logger.warning(f"log_listing_action: تعذر التسجيل في audit: {e}")


# ============================================================
#  التهيئة عند الاستيراد (lazy)
# ============================================================
# init() يُستدعى عند أول استخدام — لا هنا، لتجنب مشاكل الاستيراد
