def format_number(num):
    """تنسيق الأرقام بفواصل"""
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)

def generate_property_link(property_id):
    """توليد رابط حقيقي وقصير للعرض في الموقع"""
    base_url = "https://abonasr0907-beep.github.io"
    if str(property_id).startswith("PROP-"):
        try:
            short_id = str(int(str(property_id).replace("PROP-", "")))
            return f"{base_url}/?p={short_id}"
        except ValueError:
            pass
    return f"{base_url}/?p={property_id}"

def format_currency(amount):
    """تنسيق العملة"""
    return f"{format_number(amount)} ريال"
