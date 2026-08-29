import os
import unittest
from unittest.mock import AsyncMock, MagicMock
from telegram import User, Chat
from main import normalize, ROUTES
from bot.database import save_properties, load_properties
from bot.config import PROPERTIES_FILE, COMPASS_FILE
from bot.database import load_json, save_json
from bot.modules.add_property import (
    start_add_property, select_type, handle_area_callback, select_location,
    select_streets, handle_feature_callback, handle_price_input, handle_photo_upload_step,
    handle_preview_action, SELECTING_TYPE, SELECTING_AREA, SELECTING_LOCATION, SELECTING_STREETS,
    SELECTING_FEATURES, ENTERING_PRICE, UPLOADING_PHOTOS, PREVIEW
)

class TestFullFlowSimulation(unittest.TestCase):

    def setUp(self):
        self.orig_properties = load_json(PROPERTIES_FILE, default=[])
        self.orig_compass = load_json(COMPASS_FILE, default={})
        save_properties([])

    def tearDown(self):
        save_json(PROPERTIES_FILE, self.orig_properties)
        save_json(COMPASS_FILE, self.orig_compass)

    def test_text_normalization(self):
        self.assertEqual(normalize("➕ إضافة عرض جديد"), "اضافة عرض جديد")
        self.assertEqual(normalize("📋 قائمة العروض"), "قائمة العروض")
        self.assertEqual(normalize("✏️ تعديل عرض"), "تعديل عرض")
        self.assertEqual(normalize("🗑️ حذف عرض"), "حذف عرض")
        self.assertIn(normalize("➕ إضافة عرض جديد"), ROUTES)

    async def async_test_e2e_property_creation_flow(self):
        context = MagicMock()
        context.user_data = {}
        context.bot = MagicMock()
        context.bot.get_file = AsyncMock(return_value=MagicMock(file_path="http://example.com/photo.jpg"))

        user = User(id=123, is_bot=False, first_name="TestUser")
        chat = Chat(id=123, type="private")

        # Step 1: Text "➕ إضافة عرض جديد" -> start_add_property
        msg_start = MagicMock()
        msg_start.text = "➕ إضافة عرض جديد"
        msg_start.from_user = user
        msg_start.chat = chat
        msg_start.reply_text = AsyncMock()

        update_start = MagicMock()
        update_start.message = msg_start
        update_start.callback_query = None

        state1 = await start_add_property(update_start, context)
        self.assertEqual(state1, SELECTING_TYPE)

        # Step 1 -> Step 2: Select Type (type_land)
        query_type = MagicMock()
        query_type.data = "type_land"
        query_type.answer = AsyncMock()
        query_type.edit_message_text = AsyncMock()
        update_type = MagicMock()
        update_type.callback_query = query_type
        update_type.message = None

        state2 = await select_type(update_type, context)
        self.assertEqual(state2, SELECTING_AREA)
        self.assertEqual(context.user_data["property"]["type"], "land")

        # Step 2 -> Step 3: Select Area (area_val_500)
        query_area = MagicMock()
        query_area.data = "area_val_500"
        query_area.answer = AsyncMock()
        query_area.edit_message_text = AsyncMock()
        update_area = MagicMock()
        update_area.callback_query = query_area
        update_area.message = None

        state3 = await handle_area_callback(update_area, context)
        self.assertEqual(state3, SELECTING_LOCATION)
        self.assertEqual(context.user_data["property"]["area"], 500)

        # Step 3 -> Step 4: Select Location (loc_الرحمانية)
        query_loc = MagicMock()
        query_loc.data = "loc_الرحمانية"
        query_loc.answer = AsyncMock()
        query_loc.edit_message_text = AsyncMock()
        update_loc = MagicMock()
        update_loc.callback_query = query_loc
        update_loc.message = None

        state4 = await select_location(update_loc, context)
        self.assertEqual(state4, SELECTING_STREETS)
        self.assertEqual(context.user_data["property"]["location"], "الرحمانية")

        # Step 4 -> Step 5: Select Streets (streets_2)
        query_streets = MagicMock()
        query_streets.data = "streets_2"
        query_streets.answer = AsyncMock()
        query_streets.edit_message_text = AsyncMock()
        update_streets = MagicMock()
        update_streets.callback_query = query_streets
        update_streets.message = None

        state5 = await select_streets(update_streets, context)
        self.assertEqual(state5, SELECTING_FEATURES)
        self.assertEqual(context.user_data["property"]["streets"], "2")

        # Step 5: Select Features
        # 5a: land_kind -> فضاء (finishes features immediately)
        query_feat = MagicMock()
        query_feat.data = "featval_land_kind:فضاء"
        query_feat.answer = AsyncMock()
        query_feat.edit_message_text = AsyncMock()
        update_feat = MagicMock()
        update_feat.callback_query = query_feat
        update_feat.message = None

        state6 = await handle_feature_callback(update_feat, context)
        self.assertEqual(state6, ENTERING_PRICE)

        # Step 6: Input Price ("500000") -> UPLOADING_PHOTOS
        msg_price = MagicMock()
        msg_price.text = "500000"
        msg_price.photo = None
        msg_price.reply_text = AsyncMock()
        update_price = MagicMock()
        update_price.message = msg_price
        update_price.callback_query = None

        state7 = await handle_price_input(update_price, context)
        self.assertEqual(state7, UPLOADING_PHOTOS)
        self.assertEqual(context.user_data["property"]["price"], 500000)

        # Step 7: Upload Photo
        photo_mock = MagicMock()
        photo_mock.file_id = "photo_12345"
        msg_photo = MagicMock()
        msg_photo.photo = [photo_mock]
        msg_photo.text = None
        msg_photo.reply_text = AsyncMock()
        update_photo = MagicMock()
        update_photo.message = msg_photo
        update_photo.callback_query = None

        state8 = await handle_photo_upload_step(update_photo, context)
        self.assertEqual(state8, UPLOADING_PHOTOS)
        self.assertIn("photo_12345", context.user_data["property"]["photos"])

        # Step 7 End: Text "/done" -> PREVIEW
        msg_done = MagicMock()
        msg_done.text = "/done"
        msg_done.photo = None
        msg_done.reply_text = AsyncMock()
        msg_done.reply_media_group = AsyncMock()
        update_done = MagicMock()
        update_done.message = msg_done
        update_done.callback_query = None

        state9 = await handle_photo_upload_step(update_done, context)
        self.assertEqual(state9, PREVIEW)

        # Step 8: Preview Action -> Publish (action_publish)
        query_pub = MagicMock()
        query_pub.data = "action_publish"
        query_pub.answer = AsyncMock()
        query_pub.edit_message_text = AsyncMock()
        update_pub = MagicMock()
        update_pub.callback_query = query_pub
        update_pub.message = None

        end_state = await handle_preview_action(update_pub, context)
        self.assertEqual(end_state, -1) # ConversationHandler.END is -1

        # Assert property was saved in database with short link ?p=
        props = load_properties()
        self.assertEqual(len(props), 1)
        self.assertEqual(props[0]["id"], "PROP-0000000001")
        self.assertIn("?p=1", props[0]["property_link"])

        # Assert published message contained success text and short link
        published_msg = query_pub.edit_message_text.call_args[0][0]
        self.assertIn("تم نشر العرض بنجاح", published_msg)
        self.assertIn("?p=1", published_msg)

    def test_e2e_property_creation_flow(self):
        import asyncio
        asyncio.run(self.async_test_e2e_property_creation_flow())

if __name__ == '__main__':
    unittest.main()
