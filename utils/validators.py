def validate_positive_int(value):
    """التحقق من أن القيمة عدد صحيح موجب"""
    try:
        # إزالة الفواصل والمسافات
        cleaned = str(value).replace(',', '').replace(' ', '').replace('م²', '').replace('م', '').replace('ريال', '')
        num = int(cleaned)
        if num > 0:
            return num
        return None
    except (ValueError, TypeError):
        return None

def validate_price(value):
    """التحقق من السعر"""
    return validate_positive_int(value)

def validate_area(value):
    """التحقق من المساحة"""
    return validate_positive_int(value)
