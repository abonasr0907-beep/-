import unittest
from bot.database import load_properties, save_properties, add_property
from utils.helpers import generate_property_link
from bot.modules.add_property import get_area_ranges, build_area_keyboard, get_feature_steps

class TestPhase2AddProperty(unittest.TestCase):

    def test_area_ranges(self):
        land_areas = get_area_ranges("land")
        self.assertEqual(land_areas[0], 200)
        self.assertEqual(land_areas[-1], 10000)

        resthouse_areas = get_area_ranges("resthouse")
        self.assertEqual(resthouse_areas[0], 250)
        self.assertEqual(resthouse_areas[-1], 25000)

        farm_areas = get_area_ranges("farm")
        self.assertEqual(farm_areas[0], 10000)
        self.assertEqual(farm_areas[-1], 190000)

    def test_area_keyboard_pagination(self):
        kb_page0 = build_area_keyboard("land", page=0)
        self.assertIsNotNone(kb_page0)
        self.assertTrue(len(kb_page0.inline_keyboard) > 0)

    def test_feature_steps(self):
        land_steps = get_feature_steps("land", {})
        self.assertEqual(len(land_steps), 1)
        self.assertEqual(land_steps[0][0], "land_kind")

        land_steps_built = get_feature_steps("land", {"land_kind": "مصورة"})
        self.assertEqual(len(land_steps_built), 5)

        resthouse_steps = get_feature_steps("resthouse", {})
        self.assertTrue(len(resthouse_steps) >= 10)

        farm_steps = get_feature_steps("farm", {})
        self.assertTrue(len(farm_steps) >= 10)

    def test_property_creation_schema(self):
        save_properties([])
        new_prop = {
            "type": "land",
            "area": 500,
            "location": "الرحمانية",
            "streets": "2",
            "price": 425000,
            "features": {
                "land_kind": "مصورة",
                "electricity": "نعم"
            },
            "photos": ["file_id_123"],
            "video_url": None,
            "is_vip": False,
            "status": "active",
            "property_link": generate_property_link("PROP-0000000001")
        }

        added = add_property(new_prop)
        self.assertEqual(added['id'], "PROP-0000000001")
        self.assertEqual(added['status'], "active")
        self.assertEqual(added['price'], 425000)
        self.assertEqual(added['property_link'], "https://abonasr0907-beep.github.io/?p=1")

        props = load_properties()
        self.assertEqual(len(props), 1)
        self.assertEqual(props[0]['id'], "PROP-0000000001")

if __name__ == '__main__':
    unittest.main()
