# utils/property_utils.py
"""
أدوات مشتركة للعقارات
تقليل التكرار في الكود
"""

from utils.price_utils import format_price_en

# خريطة أنواع العقارات
PROPERTY_TYPE_MAP = {
    # المدخلات الممكنة -> القيمة الموحدة
    'مزرعة': 'farm',
    'farm': 'farm',
    'farms': 'farm',
    'زراعي': 'farm',
    'استراحة': 'resthouse',
    'resthouse': 'resthouse',
    'resthouses': 'resthouse',
    'أرض سكنية': 'land',
    'land': 'land',
    'lands': 'land',
    'سكني': 'land',
}

# خريطة الصور الافتراضية
DEFAULT_IMAGES = {
    'farm': 'images/cat-farms.jpg',
    'resthouse': 'images/cat-rest.jpg',
    'land': 'images/cat-lands.jpg',
}

# التسميات العربية
TYPE_LABELS_AR = {
    'farm': 'مزرعة',
    'resthouse': 'استراحة',
    'land': 'أرض سكنية',
}

TYPE_LABELS_EN = {
    'farm': 'Farm',
    'resthouse': 'Resthouse',
    'land': 'Land',
}

def normalize_property_type(prop_type: str) -> str:
    """
    تحويل أي نوع مدخل إلى القيمة الموحدة
    """
    if not prop_type:
        return 'land'

    normalized = str(prop_type).lower().strip()
    return PROPERTY_TYPE_MAP.get(normalized, 'land')

def get_property_category(prop_type: str) -> str:
    """
    الحصول على التسمية العربية
    """
    normalized = normalize_property_type(prop_type)
    return TYPE_LABELS_AR.get(normalized, 'عقار')

def get_default_image(prop_type: str) -> str:
    """
    الحصول على الصورة الافتراضية
    """
    normalized = normalize_property_type(prop_type)
    return DEFAULT_IMAGES.get(normalized, 'images/farms-bg.jpg')

def format_property_price(price) -> str:
    """
    تنسيق سعر العقار بالإنجليزية
    """
    try:
        price_num = int(price)
        return format_price_en(price_num)
    except (ValueError, TypeError):
        return "0 SAR"

def build_property_card_data(property_obj: dict) -> dict:
    """
    بناء بيانات بطاقة العقار الموحدة
    """
    ptype = normalize_property_type(property_obj.get('type', ''))

    # تحديد الصورة
    photos = property_obj.get('photo_urls') or property_obj.get('photos') or property_obj.get('images', [])
    photo_url = photos[0] if photos else get_default_image(ptype)

    # تحديد المميزات
    features = property_obj.get('features', [])
    if isinstance(features, dict):
        features = [f"{k}: {v}" for k, v in features.items()]

    return {
        'id': property_obj.get('id', ''),
        'type': ptype,
        'category': get_property_category(ptype),
        'title': property_obj.get('title', f"{get_property_category(ptype)} في {property_obj.get('location', 'الخرج')}"),
        'area': property_obj.get('location') or property_obj.get('area', 'الخرج'),
        'size_sqm': int(property_obj.get('size_sqm') or property_obj.get('area', 0) or 0),
        'price': int(property_obj.get('price', 0) or 0),
        'price_text': format_property_price(property_obj.get('price', 0)),
        'description': property_obj.get('description', ''),
        'features': features,
        'images': photos if photos else [get_default_image(ptype)],
        'map_link': property_obj.get('map_link', ''),
        'date_added': property_obj.get('date') or property_obj.get('date_added') or property_obj.get('created_at', ''),
        'featured': property_obj.get('is_vip') or property_obj.get('featured', False),
        'status': property_obj.get('status', 'active'),
    }
