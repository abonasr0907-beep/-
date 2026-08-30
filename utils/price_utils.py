# utils/price_utils.py
"""
أدوات تحويل وعرض الأسعار
يدعم الإدخال بالعربية والإنجليزية
العرض بالإنجليزية فقط
"""

import re

# خريطة الأرقام العربية إلى الإنجليزية
ARABIC_TO_ENGLISH_DIGITS = str.maketrans(
    '٠١٢٣٤٥٦٧٨٩',
    '0123456789'
)

def normalize_arabic_numbers(text: str) -> str:
    """
    تحويل الأرقام العربية إلى إنجليزية
    مثال: "١٬٢٣٤٬٥٦٧" -> "1234567"
    """
    if not text:
        return "0"

    # تحويل الأرقام العربية
    normalized = str(text).translate(ARABIC_TO_ENGLISH_DIGITS)

    # إزالة كل شيء غير الرقم
    digits_only = re.sub(r'[^\d]', '', normalized)

    return digits_only if digits_only else "0"

def parse_price_input(text: str) -> int:
    """
    تحليل أي مدخل سعر (عربي/إنجليزي/فواصل/نقاط)
    مثال: "1,200,000" -> 1200000
    مثال: "١٢٠٠٠٠٠" -> 1200000
    """
    normalized = normalize_arabic_numbers(text)

    # إزالة الفواصل والنقاط
    clean = normalized.replace(',', '').replace('.', '')

    try:
        return int(clean)
    except ValueError:
        return 0

def format_price_en(price: int) -> str:
    """
    تنسيق السعر بالإنجليزية
    مثال: 1200000 -> "1,200,000 SAR"
    """
    if not price:
        return "0 SAR"

    formatted = f"{price:,}"
    return f"{formatted} SAR"

def format_price_ar(price: int) -> str:
    """
    تنسيق السعر بالعربية (للبوت فقط)
    مثال: 1200000 -> "1,200,000 ريال"
    """
    if not price:
        return "0 ريال"

    formatted = f"{price:,}"
    return f"{formatted} ريال"
