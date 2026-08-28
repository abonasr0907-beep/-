import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", "8080"))

DATA_DIR = "data"
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties.json")
VISITORS_FILE = os.path.join(DATA_DIR, "visitors.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
COMPASS_FILE = os.path.join(DATA_DIR, "compass_data.json")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")

LOCATIONS = [
    "الرحمانية",
    "الخريج",
    "الهياثم",
    "العفجة",
    "الشديدة",
    "الدلم",
    "الضبيعة",
    "أخرى"
]

PROPERTY_TYPES = {
    "land": "🏡 أرض سكنية",
    "resthouse": "🏠 استراحة",
    "farm": "🚜 مزرعة"
}
