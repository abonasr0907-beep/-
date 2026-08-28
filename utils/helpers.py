def format_number(val):
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)
