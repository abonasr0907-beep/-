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

if __name__ == '__main__':
    unittest.main()
