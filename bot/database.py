import json
import os
from datetime import datetime
from bot.config import PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE, DATA_DIR

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الملفات إذا لم توجد"""
    os.makedirs(DATA_DIR, exist_ok=True)

    for file_path in [PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

def load_json(filepath, default=None):
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                if "properties" in data and filepath == PROPERTIES_FILE:
                    return data["properties"]
                if "visitors" in data and filepath == VISITORS_FILE:
                    return data["visitors"]
                if "admins" in data and filepath == ADMINS_FILE:
                    return data["admins"]
            return data
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return default

def save_json(filepath, data, root_key=None):
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        if root_key:
            json.dump({root_key: data}, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_properties():
    """تحميل جميع العروض"""
    return load_json(PROPERTIES_FILE, default=[])

def save_properties(properties):
    """حفظ جميع العروض"""
    save_json(PROPERTIES_FILE, properties, root_key="properties")

def add_property(property_data):
    """إضافة عرض جديد"""
    properties = load_properties()
    property_data['id'] = f"PROP-{len(properties) + 1:010d}"
    property_data['status'] = property_data.get('status', 'active')
    property_data['created_at'] = property_data.get('created_at', datetime.now().isoformat())
    properties.append(property_data)
    save_properties(properties)
    return property_data

def update_property(property_id, updates):
    """تحديث عرض موجود"""
    properties = load_properties()
    for prop in properties:
        if prop.get('id') == property_id:
            prop.update(updates)
            save_properties(properties)
            return prop
    return None

def delete_property(property_id):
    """حذف عرض"""
    properties = load_properties()
    properties = [p for p in properties if p.get('id') != property_id]
    save_properties(properties)

def get_property(property_id):
    """الحصول على عرض محدد"""
    properties = load_properties()
    for prop in properties:
        if prop.get('id') == property_id:
            return prop
    return None
