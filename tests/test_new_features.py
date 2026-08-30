import unittest
from utils.helpers import generate_property_link

class TestNewFeatures(unittest.TestCase):

    def test_short_link_generation(self):
        link1 = generate_property_link("PROP-0000000002")
        self.assertEqual(link1, "https://abonasr0907-beep.github.io/?p=2")

        link2 = generate_property_link("PROP-0000000105")
        self.assertEqual(link2, "https://abonasr0907-beep.github.io/?p=105")

        link3 = generate_property_link("custom_id")
        self.assertEqual(link3, "https://abonasr0907-beep.github.io/?p=custom_id")

    def test_bot_report_imports(self):
        from bot.modules.reports import morning_report_command, export_csv_command
        self.assertTrue(callable(morning_report_command))
        self.assertTrue(callable(export_csv_command))

    def test_bot_visitor_imports(self):
        from bot.modules.visitors import update_visitor_status
        self.assertTrue(callable(update_visitor_status))

    def test_database_helper_functions(self):
        import tempfile
        import os
        from unittest.mock import patch
        from bot.database import (
            get_property_by_id, delete_property_by_id, archive_property,
            unarchive_property, toggle_property_status, toggle_vip_status
        )

        dummy_data = [
            {"id": "PROP-0000000001", "title": "Test 1", "status": "active", "is_vip": False},
            {"id": "PROP-0000000002", "title": "Test 2", "status": "archived", "is_vip": True}
        ]

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name

        try:
            with patch("bot.database.PROPERTIES_FILE", tmp_path):
                from bot.database import save_properties, load_properties
                save_properties(dummy_data)

                # Test get_property_by_id
                prop1 = get_property_by_id("PROP-0000000001")
                self.assertEqual(prop1.get("title"), "Test 1")
                self.assertEqual(get_property_by_id("NONEXISTENT"), {})

                # Test toggle_property_status
                toggle_property_status("PROP-0000000001")
                self.assertEqual(get_property_by_id("PROP-0000000001").get("status"), "sold")
                toggle_property_status("PROP-0000000001")
                self.assertEqual(get_property_by_id("PROP-0000000001").get("status"), "active")

                # Test toggle_vip_status
                toggle_vip_status("PROP-0000000001")
                self.assertTrue(get_property_by_id("PROP-0000000001").get("is_vip"))

                # Test archive_property and unarchive_property
                archive_property("PROP-0000000001")
                self.assertEqual(get_property_by_id("PROP-0000000001").get("status"), "archived")
                unarchive_property("PROP-0000000001")
                self.assertEqual(get_property_by_id("PROP-0000000001").get("status"), "active")

                # Test delete_property_by_id
                self.assertTrue(delete_property_by_id("PROP-0000000002"))
                self.assertFalse(delete_property_by_id("NONEXISTENT"))
                self.assertEqual(len(load_properties()), 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
