import os
import json
import logging

logger = logging.getLogger("afaq_guardian_monitor")

class SystemMonitor:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir

    def check_file_integrity(self):
        protected_files = [
            "sitemap.xml",
            "robots.txt",
            "bot/config.json",
            "offers-data/offers.json"
        ]
        results = {}
        for pfile in protected_files:
            full_path = os.path.join(self.root_dir, pfile)
            exists = os.path.exists(full_path)
            results[pfile] = {
                "exists": exists,
                "size": os.path.getsize(full_path) if exists else 0
            }
        return results

    def check_offers_count(self):
        offers_path = os.path.join(self.root_dir, "offers-data", "offers.json")
        if not os.path.exists(offers_path):
            return 0
        try:
            with open(offers_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return len(data.get("offers", []))
        except Exception as e:
            logger.error(f"Error reading offers.json: {e}")
            return -1
