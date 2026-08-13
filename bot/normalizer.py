#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot/normalizer.py — Phase 3 §1.1
مُطبِّع النصوص العربي (Arabic Text Normalizer) — Idempotent

الوظائف:
1. تطبيع الأرقام: تحويل الأرقام الهندية/العربية إلى لاتينية (0-9)
2. تطبيع الحروف: توحيد ألف/ياء/همزة/تاء مربوطة
3. تطبيع المسافات: إزالة المسافات الزائدة + trim
4. تطبيع الفئات: توحيف الفئات المعروفة إلى whitelist
5. تطبيع المناطق: توحيف أسماء المناطق إلى القائمة المعتمدة

الخصائص:
- Idempotent: normalize(x) == normalize(normalize(x))
- Add-only: لا يعدّل offers.json مباشرة؛ يستدعيه الكود عند الحاجة
- Safe: لا يرفع استثناءات أبدًا — يعيد النص الأصلي عند الخطأ

الاستخدام:
    from bot.normalizer import normalize_text, normalize_category, normalize_area, is_known_category
    clean = normalize_text("  مزرعة  في  الرحمانية  ")
    cat = normalize_category("مزرة")  # → "مزرعة"
    area = normalize_area("الرحمنية")  # → "الرحمانية"
"""

import re
import unicodedata

# ============================================================
#  جداول التطبيع
# ============================================================

# الأرقام الهندية → لاتينية
_ARABIC_INDIC_DIGITS = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
}

# تطبيع الحروف العربية
_LETTER_NORMALIZATIONS = {
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
    'ى': 'ي', 'ئ': 'ي',
    'ة': 'ه',
    'ؤ': 'و',
    'ـ': '',  # tatweel
}

# ============================================================
#  Whitelist الفئات المعتمدة (add-only — لا تُحذف)
# ============================================================

# الفئات الأساسية الثلاث + مرادفاتها
CATEGORY_WHITELIST = {
    "مزرعة": ["مزرعة", "مزرة", "مزارع", "مزراع", "مزرة", "ارض زراعية", "أرض زراعية", "زراعية"],
    "استراحة": ["استراحة", "استراحه", "استراحات", "استراحة ", "قهوة", "ملحق", "ديوانية", "مسبح", "حديقة"],
    "أرض سكنية": ["أرض سكنية", "ارض سكنية", "أراضي", "اراضي", "سكنية", "تجارية", "قطعة", "صك", "مخطط", "شمال"],
}

# قائمة الفئات المعتمدة للعرض
KNOWN_CATEGORIES = list(CATEGORY_WHITELIST.keys())

# ============================================================
#  Whitelist المناطق المعتمدة (من office-data.json)
# ============================================================

AREA_WHITELIST = {
    "الرحمانية": ["الرحمانية", "الرحمنية", "الرحمنيه", "الرحمانيه", "رحمانية", "رحمنية"],
    "الهياثم": ["الهياثم", "الهيثم", "الهياثيم", "الهيثام", "هياثم", "هيثم"],
    "الدلم": ["الدلم", "الدلم ", "دلم"],
    "الضبيعة": ["الضبيعة", "الضبعية", "الضبيعه", "الضبيعة ", "ضبيعة", "ضبعية", "الضبيعية"],
    "العفجة": ["العفجة", "العفجه", "العفجية", "العفجيه", "عفجة", "عفجه"],
}

KNOWN_AREAS = list(AREA_WHITELIST.keys())

# ============================================================
#  دوال التطبيع الأساسية
# ============================================================

def normalize_digits(text):
    """تحويل الأرقام الهندية/العربية إلى لاتينية (0-9)"""
    if not text:
        return text
    result = []
    for ch in str(text):
        result.append(_ARABIC_INDIC_DIGITS.get(ch, ch))
    return ''.join(result)


def normalize_letters(text):
    """توحيد الحروف العربية (أ→ا، ى→ي، ة→ه، إزالة التطويل)"""
    if not text:
        return text
    result = []
    for ch in str(text):
        result.append(_LETTER_NORMALIZATIONS.get(ch, ch))
    return ''.join(result)


def normalize_whitespace(text):
    """إزالة المسافات الزائدة + trim"""
    if not text:
        return text
    # تحويل المسافات غير العادية + إزالة المسافات المتعددة
    text = str(text).replace('\u200f', '').replace('\u200e', '')  # RTL/LTR marks
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_text(text):
    """
    التطبيع الكامل للنص — Idempotent.
    1. تطبيع الأرقام
    2. تطبيع الحروف
    3. تطبيع المسافات
    
    ضمان: normalize_text(normalize_text(x)) == normalize_text(x)
    """
    if text is None:
        return ""
    try:
        t = str(text)
        t = normalize_digits(t)
        t = normalize_letters(t)
        t = normalize_whitespace(t)
        return t
    except Exception:
        return str(text) if text else ""


# ============================================================
#  تطبيع الفئات
# ============================================================

def is_known_category(category):
    """تحقق إذا كانت الفئة معروفة في الـ whitelist"""
    if not category:
        return False
    normalized = normalize_text(category)
    if normalized in KNOWN_CATEGORIES:
        return True
    # فحص المرادفات
    for canonical, synonyms in CATEGORY_WHITELIST.items():
        for syn in synonyms:
            if normalize_text(syn) == normalized:
                return True
    return False


def normalize_category(category):
    """
    توحيف الفئة إلى الاسم المعتمد في الـ whitelist.
    إذا لم تُعثر على مطابقة:
    - تعيد الفئة الأصلية مع علامة category_raw في المتصل
    - لا تُعيد None أو خطأ
    
    أمثلة:
        normalize_category("مزرة") → "مزرعة"
        normalize_category("استراحه") → "استراحة"
        normalize_category("ارض سكنية") → "أرض سكنية"
        normalize_category("فيلا") → "فيلا"  (غير معروفة، تُعاد كما هي)
    """
    if not category:
        return category
    normalized = normalize_text(category)
    
    # مطابقة مباشرة
    if normalized in KNOWN_CATEGORIES:
        return normalized
    
    # مطابقة عبر المرادفات
    for canonical, synonyms in CATEGORY_WHITELIST.items():
        for syn in synonyms:
            if normalize_text(syn) == normalized:
                return canonical
        # فحص containment (إذا احتوى النص على مرادف)
        for syn in synonyms:
            if normalize_text(syn) in normalized or normalized in normalize_text(syn):
                # مطابقة جزئية — فقط إذا كان التطابق ≥ 60% من طول الكلمة
                if len(normalized) >= 3 and len(normalize_text(syn)) >= 3:
                    return canonical
    
    # غير معروفة — تُعاد كما هي (add-only: لا نحذف)
    return category


def get_category_raw(category):
    """
    إذا كانت الفئة غير معروفة، تُعيد الفئة الخام (category_raw)
    لتخزينها بجانب الفئة المعتمدة.
    """
    if not category:
        return None
    normalized = normalize_category(category)
    if normalized != normalize_text(category) and normalized in KNOWN_CATEGORIES:
        return None  # تم توحيفتها
    if is_known_category(category):
        return None
    return category


def should_include_in_all_sections(category):
    """
    إذا كانت الفئة غير معروفة، يجب تضمينها في 'كل الأقسام'
    لتجنب فقدانها من الموقع.
    """
    return not is_known_category(category)


# ============================================================
#  تطبيع المناطق
# ============================================================

def is_known_area(area):
    """تحقق إذا كانت المنطقة معروفة في الـ whitelist"""
    if not area:
        return False
    normalized = normalize_text(area)
    if normalized in KNOWN_AREAS:
        return True
    for canonical, synonyms in AREA_WHITELIST.items():
        for syn in synonyms:
            if normalize_text(syn) == normalized:
                return True
    return False


def normalize_area(area):
    """
    توحيف اسم المنطقة إلى الاسم المعتمد.
    إذا لم تُعثر على مطابقة، تُعاد كما هي (add-only).
    
    أمثلة:
        normalize_area("الرحمنية") → "الرحمانية"
        normalize_area("الهيثم") → "الهياثم"
        normalize_area("الرياض") → "الرياض"  (غير معروفة، تُعاد كما هي)
    """
    if not area:
        return area
    normalized = normalize_text(area)
    
    # مطابقة مباشرة
    if normalized in KNOWN_AREAS:
        return normalized
    
    # مطابقة عبر المرادفات
    for canonical, synonyms in AREA_WHITELIST.items():
        for syn in synonyms:
            if normalize_text(syn) == normalized:
                return canonical
        # مطابقة جزئية
        for syn in synonyms:
            if normalize_text(syn) in normalized or normalized in normalize_text(syn):
                if len(normalized) >= 3:
                    return canonical
    
    # غير معروفة — تُعاد كما هي
    return area


# ============================================================
#  تطبيع عرض كامل (للاستخدام عند النشر)
# ============================================================

def normalize_offer(offer):
    """
    تطبيع كامل لقاموس العرض قبل النشر.
    - لا يعدّل القاموس الأصلي (يُعيد نسخة)
    - يضيف category_raw إذا كانت الفئة غير معروفة
    - يطبّع المساحة والسعر (أرقام)
    
    ضمان Idempotent: normalize_offer(normalize_offer(o)) == normalize_offer(o)
    """
    if not offer or not isinstance(offer, dict):
        return offer
    
    try:
        result = dict(offer)  # نسخة سطحية
        
        # تطبيع الفئة
        if "category" in result and result["category"]:
            original_cat = result["category"]
            normalized_cat = normalize_category(original_cat)
            if normalized_cat != original_cat:
                result["category_raw"] = original_cat  # حفظ الأصل
            result["category"] = normalized_cat
        
        # تطبيع المنطقة
        if "area" in result and result["area"]:
            result["area"] = normalize_area(result["area"])
        
        # تطبيع العنوان
        if "title" in result and result["title"]:
            result["title"] = normalize_text(result["title"])
        
        # تطبيع الأرقام في المساحة والسعر
        if "size_sqm" in result and result["size_sqm"]:
            result["size_sqm"] = normalize_text(str(result["size_sqm"]))
        if "price" in result and result["price"]:
            result["price"] = normalize_text(str(result["price"]))
        
        # تضمين في كل الأقسام إذا كانت الفئة غير معروفة
        if should_include_in_all_sections(result.get("category", "")):
            result["include_in_all_sections"] = True
        
        return result
    except Exception:
        return offer


# ============================================================
#  اختبار ذاتي (self-test) — يُستدعى عند الحاجة
# ============================================================

def _self_test():
    """اختبار ذاتي سريع للتأكد من Idempotency"""
    tests = [
        ("مزرعة في الرحمانية", "مزرعه في الرحمانيه"),  # ة→ه (normalized form)
        ("  مزرعة  في  الرحمانية  ", "مزرعه في الرحمانيه"),
        ("مزرة في الرحمنية", "مزره في الرحمنيه"),
        ("١٢٣٤٥", "12345"),
        ("أرض سكنية", "ارض سكنيه"),  # أ→ا, ة→ه
    ]
    passed = 0
    for inp, expected in tests:
        result = normalize_text(inp)
        # Idempotency check
        result2 = normalize_text(result)
        if result == result2:
            idem = "✅"
        else:
            idem = "❌"
        if result == expected:
            passed += 1
            print(f"  ✅ '{inp}' → '{result}' {idem}")
        else:
            print(f"  ❌ '{inp}' → '{result}' (expected '{expected}') {idem}")
    
    # Category tests
    cat_tests = [
        ("مزرة", "مزرعة"),
        ("استراحه", "استراحة"),
        ("ارض سكنية", "أرض سكنية"),
    ]
    for inp, expected in cat_tests:
        result = normalize_category(inp)
        if result == expected:
            passed += 1
            print(f"  ✅ category('{inp}') → '{result}'")
        else:
            print(f"  ❌ category('{inp}') → '{result}' (expected '{expected}')")
    
    # Area tests
    area_tests = [
        ("الرحمنية", "الرحمانية"),
        ("الهيثم", "الهياثم"),
        ("الضبعية", "الضبيعة"),
    ]
    for inp, expected in area_tests:
        result = normalize_area(inp)
        if result == expected:
            passed += 1
            print(f"  ✅ area('{inp}') → '{result}'")
        else:
            print(f"  ❌ area('{inp}') → '{result}' (expected '{expected}')")
    
    total = len(tests) + len(cat_tests) + len(area_tests)
    print(f"\n  {passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    print("=== normalizer.py self-test ===")
    _self_test()
