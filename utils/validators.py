def validate_positive_int(text):
    clean_text = text.strip().replace(",", "").replace("م²", "").replace("م", "").replace("ريال", "")
    if clean_text.isdigit() and int(clean_text) > 0:
        return True, int(clean_text)
    return False, None
