def format_number(num):
    """تنسيق الأرقام بفواصل"""
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)

def generate_property_link(property_id):
    """توليد رابط حقيقي للعرض في الموقع"""
    base_url = "https://abonasr0907-beep.github.io"
    return f"{base_url}/?property={property_id}"

def format_currency(amount):
    """تنسيق العملة"""
    return f"{format_number(amount)} ريال"
