import os
import unittest
from bot.database import load_properties, save_properties, add_property, get_property, update_property, delete_property
from bot.config import COMPASS_FILE, VISITORS_FILE, ADMINS_FILE
from bot.database import load_json, save_json
from bot.modules.compass import calculate_compass_data
from bot.modules.backup import create_backup
from bot.modules.site_sync import sync_site_data

from bot.config import PROPERTIES_FILE

class TestAllPhasesComprehensive(unittest.TestCase):

    def setUp(self):
        self.orig_props = load_json(PROPERTIES_FILE, default=[])
        self.orig_compass = load_json(COMPASS_FILE, default={})
        self.orig_visitors = load_json(VISITORS_FILE, default=[])
        self.orig_admins = load_json(ADMINS_FILE, default=[])
        save_properties([])

    def tearDown(self):
        save_json(PROPERTIES_FILE, self.orig_props)
        save_json(COMPASS_FILE, self.orig_compass)
        save_json(VISITORS_FILE, self.orig_visitors, root_key="visitors")
        save_json(ADMINS_FILE, self.orig_admins, root_key="admins")

    def test_compass_calculation(self):
        add_property({"type": "land", "location": "الرحمانية", "price": 500000, "area": 500, "status": "active"})
        add_property({"type": "land", "location": "الرحمانية", "price": 300000, "area": 300, "status": "active"})

        compass = calculate_compass_data()
        self.assertIn("الرحمانية", compass)
        self.assertEqual(compass["الرحمانية"]["avg_sqm_price"], 1000)
        self.assertEqual(compass["الرحمانية"]["count"], 2)

    def test_backup_and_site_sync(self):
        backup_dir = create_backup()
        self.assertTrue(os.path.exists(backup_dir))

        synced_count = sync_site_data()
        self.assertEqual(synced_count, len(load_properties()))

    def test_visitors_and_admins_schema(self):
        save_json(VISITORS_FILE, [{"id": "VIS-001", "name": "عميل تجريبي", "phone": "0500000000", "status": "new"}], root_key="visitors")
        visitors = load_json(VISITORS_FILE)
        self.assertEqual(len(visitors), 1)
        self.assertEqual(visitors[0]["id"], "VIS-001")

        save_json(ADMINS_FILE, [{"username": "admin", "name": "المدير الرئيسي", "role": "full"}], root_key="admins")
        admins = load_json(ADMINS_FILE)
        self.assertEqual(len(admins), 1)
        self.assertEqual(admins[0]["username"], "admin")

if __name__ == '__main__':
    unittest.main()
