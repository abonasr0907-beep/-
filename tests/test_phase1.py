import os
import json
import unittest
from bot.config import DATA_DIR, PROPERTIES_FILE, VISITORS_FILE, ADMINS_FILE, LOCATIONS, PROPERTY_TYPES
from bot.database import (
    init_db, load_properties, save_properties,
    add_property, update_property, delete_property, get_property
)
from utils.validators import validate_positive_int, validate_price, validate_area
from utils.helpers import format_number, generate_property_link, format_currency

class TestPhase1Basics(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_validators(self):
        self.assertEqual(validate_positive_int("100"), 100)
        self.assertEqual(validate_positive_int("1,000,000 ريال"), 1000000)
        self.assertEqual(validate_positive_int("500 م²"), 500)
        self.assertIsNone(validate_positive_int("-50"))
        self.assertIsNone(validate_positive_int("abc"))

        self.assertEqual(validate_price("250,000"), 250000)
        self.assertEqual(validate_area("400 م²"), 400)

    def test_helpers(self):
        self.assertEqual(format_number(1000000), "1,000,000")
        self.assertEqual(format_currency(500000), "500,000 ريال")
        self.assertTrue(generate_property_link("PROP-0000000001").startswith("https://abonasr0907-beep.github.io"))

    def test_database_crud(self):
        # Clear properties for testing
        save_properties([])
        self.assertEqual(load_properties(), [])

        # Add
        prop_data = {"type": "land", "location": "الرحمانية", "price": 500000}
        added = add_property(prop_data)
        self.assertEqual(added['id'], "PROP-0000000001")
        self.assertEqual(added['status'], 'active')

        # Get
        retrieved = get_property("PROP-0000000001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['location'], "الرحمانية")

        # Update
        updated = update_property("PROP-0000000001", {"price": 550000})
        self.assertEqual(updated['price'], 550000)

        # Delete
        delete_property("PROP-0000000001")
        self.assertIsNone(get_property("PROP-0000000001"))

if __name__ == '__main__':
    unittest.main()
