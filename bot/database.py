import os
import json
from datetime import datetime
from bot.config import (
    DATA_DIR, PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE,
    COMPASS_FILE, BACKUPS_DIR, PHOTOS_DIR
)

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)

    for filepath in [PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE, COMPASS_FILE]:
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                if filepath == PROPERTIES_FILE:
                    json.dump({"properties": []}, f, ensure_ascii=False, indent=2)
                elif filepath == VISITORS_FILE:
                    json.dump({"visitors": []}, f, ensure_ascii=False, indent=2)
                elif filepath == ADMINS_FILE:
                    json.dump({"admins": []}, f, ensure_ascii=False, indent=2)
                elif filepath == COMPASS_FILE:
                    json.dump({}, f, ensure_ascii=False, indent=2)

def load_json(filepath, default=None):
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and "properties" in data and filepath == PROPERTIES_FILE:
                return data["properties"]
            if isinstance(data, dict) and "visitors" in data and filepath == VISITORS_FILE:
                return data["visitors"]
            if isinstance(data, dict) and "admins" in data and filepath == ADMINS_FILE:
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
    return load_json(PROPERTIES_FILE, default=[])

def save_properties(properties):
    save_json(PROPERTIES_FILE, properties, root_key="properties")
