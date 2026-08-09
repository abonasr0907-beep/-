#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام تحسين وضغط الصور
يحلّ محل دالة enhance_image القديمة

المميزات:
- تحويل إلى WebP (أصغر حجم) أو JPEG
- كشف الصور المكررة عبر SHA256
- توليد أسماء ملفات فريدة مرتبطة بمعرف العرض
- معالجة دوران EXIF تلقائياً
- إنشاء صور مصغرة (thumbnails)
- تحسين الجودة: شدّ، تباين، سطوع، تقليل ضجيج
"""

import hashlib
import logging
import os
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger("afaq_bot.image_utils")

# ============================================================
#  الإعدادات
# ============================================================
MAX_WIDTH = 3840          # أقصى عرض (4K)
THUMB_WIDTH = 400         # عرض الصورة المصغرة
WEBP_QUALITY = 88         # جودة WebP (1-100)
JPEG_QUALITY = 90         # جودة JPEG (1-100)
MIN_DIMENSION = 200       # أقل بُعد مقبول


# ============================================================
#  كشف التكرار
# ============================================================
def _file_hash(file_path: str) -> str:
    """حساب SHA256 للملف"""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"خطأ في حساب hash للملف {file_path}: {e}")
        return ""


def _image_content_hash(img: Image.Image) -> str:
    """حساب hash لمحتوى الصورة (بعد تصغيرها لسرعة المقارنة)"""
    try:
        small = img.resize((32, 32), Image.LANCZOS).convert("RGB")
        import io
        buf = io.BytesIO()
        small.save(buf, format="PNG")
        return hashlib.sha256(buf.getvalue()).hexdigest()
    except Exception:
        return ""


def _is_duplicate(file_path: str, existing_hashes: set) -> tuple:
    """
    التحقق من تكرار الصورة.
    يُعيد: (True, hash) إذا كانت مكررة، (False, hash) إذا لم تكن.
    """
    fhash = _file_hash(file_path)
    if not fhash:
        return False, ""
    if fhash in existing_hashes:
        return True, fhash
    # أيضاً فحص hash المحتوى (يكشف الصور المتطابقة بأسماء مختلفة)
    try:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            chash = _image_content_hash(img)
            if chash and chash in existing_hashes:
                return True, chash
            return False, fhash
    except Exception:
        return False, fhash


def get_existing_image_hashes(images_dir) -> set:
    """
    فحص مجلد الصور وبناء مجموعة hash للصور الموجودة.
    يُستخدم لكشف التكرار عند رفع صور جديدة.
    """
    hashes = set()
    images_path = Path(images_dir)
    if not images_path.exists():
        return hashes
    for f in images_path.iterdir():
        if f.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png"):
            fhash = _file_hash(str(f))
            if fhash:
                hashes.add(fhash)
    return hashes


# ============================================================
#  توليد أسماء الملفات
# ============================================================
def generate_image_name(offer_id: str, index: int) -> str:
    """
    توليد اسم ملف فريد مرتبط بمعرف العرض.
    مثال: AFQ_2026_0001_0_1786260000
    """
    # تنظيف معرف العرض (إزالة الشرطات)
    clean_id = offer_id.replace("-", "_").replace(" ", "_") if offer_id else "draft"
    if not offer_id or offer_id == "draft":
        clean_id = "draft"
    timestamp = int(datetime.now().timestamp())
    return f"{clean_id}_{index}_{timestamp}"


# ============================================================
#  التحسين والضغط
# ============================================================
def enhance_and_compress(
    input_path: str,
    output_base: str,
    fmt: str = "webp",
    max_width: int = MAX_WIDTH,
    create_thumb: bool = True,
) -> tuple:
    """
    تحسين وضغط صورة.

    المعاملات:
        input_path: مسار الصورة الأصلية
        output_base: المسار الأساسي للإخراج (بدون امتداد)
        fmt: 'webp' أو 'jpeg'
        max_width: أقصى عرض للصورة
        create_thumb: إنشاء صورة مصغرة

    يُعيد:
        (main_path, thumb_path) — مسار الصورة الرئيسية والمصغرة
        thumb_path قد يكون None إذا تم تعطيله
    """
    try:
        with Image.open(input_path) as img:
            # ── معالجة دوران EXIF ──
            img = ImageOps.exif_transpose(img)

            # ── التحويل إلى RGB (إزالة شفافية alpha إذا كانت) ──
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # ── تصغير الحجم إذا كان كبيراً ──
            w, h = img.size
            if w > max_width:
                ratio = max_width / w
                new_h = int(h * ratio)
                img = img.resize((max_width, new_h), Image.LANCZOS)
                logger.info(f"  📐 تم تصغير الصورة من {w}x{h} إلى {max_width}x{new_h}")

            # ── تحسينات الجودة ──
            # تقليل الضجيج (خفيف للحفاظ على التفاصيل)
            img = img.filter(ImageFilter.SMOOTH_MORE)

            # شدّ (sharpness) — زيادة طفيفة
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.15)

            # التباين (contrast) — زيادة طفيفة
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.08)

            # السطوع (brightness) — زيادة طفيفة
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.03)

            # الألوان (color) — زيادة طفيفة
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.10)

            # ── حفظ الصورة الرئيسية ──
            ext = "webp" if fmt == "webp" else "jpg"
            main_path = f"{output_base}.{ext}"

            if fmt == "webp":
                img.save(main_path, format="WEBP", quality=WEBP_QUALITY, method=6)
            else:
                img.save(main_path, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

            file_size = os.path.getsize(main_path) / 1024  # KB
            logger.info(f"  ✅ تم حفظ الصورة: {main_path} ({file_size:.1f} KB)")

            # ── إنشاء الصورة المصغرة ──
            thumb_path = None
            if create_thumb:
                thumb = img.copy()
                thumb.thumbnail((THUMB_WIDTH, THUMB_WIDTH), Image.LANCZOS)
                thumb_path = f"{output_base}_thumb.{ext}"
                if fmt == "webp":
                    thumb.save(thumb_path, format="WEBP", quality=75, method=4)
                else:
                    thumb.save(thumb_path, format="JPEG", quality=75, optimize=True)

            return main_path, thumb_path

    except Exception as e:
        logger.error(f"❌ خطأ في تحسين الصورة {input_path}: {e}")
        raise


def get_image_info(file_path: str) -> dict:
    """جلب معلومات الصورة (الأبعاد والحجم)"""
    try:
        with Image.open(file_path) as img:
            w, h = img.size
            size_kb = os.path.getsize(file_path) / 1024
            return {
                "width": w,
                "height": h,
                "size_kb": round(size_kb, 1),
                "format": img.format,
            }
    except Exception:
        return {}


def create_thumbnail(input_path: str, output_path: str, size: int = THUMB_WIDTH) -> bool:
    """إنشاء صورة مصغرة مستقلة"""
    try:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((size, size), Image.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            ext = Path(output_path).suffix.lower()
            if ext == ".webp":
                img.save(output_path, format="WEBP", quality=75, method=4)
            else:
                img.save(output_path, format="JPEG", quality=75, optimize=True)
        return True
    except Exception as e:
        logger.error(f"خطأ في إنشاء صورة مصغرة: {e}")
        return False
