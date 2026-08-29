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

if __name__ == '__main__':
    unittest.main()
