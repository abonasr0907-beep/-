import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from bot.modules.add_property import (
    start_add_property, show_preview, cancel_add_property,
    SELECTING_TYPE, PREVIEW
)

@pytest.fixture
def client():
    return TestClient(app)

import asyncio

def test_bot_cancel_flow_clears_user_data():
    async def _test():
        update = AsyncMock()
        context = MagicMock()
        context.user_data = {"property": {"type": "land"}, "temp": 123}

        res = await cancel_add_property(update, context)
        assert res == -1  # ConversationHandler.END
        assert len(context.user_data) == 0
    asyncio.run(_test())

def test_bot_start_clears_partial_session():
    async def _test():
        update = AsyncMock()
        context = MagicMock()
        context.user_data = {"old_data": True}

        res = await start_add_property(update, context)
        assert res == SELECTING_TYPE
        assert "old_data" not in context.user_data
        assert "property" in context.user_data
    asyncio.run(_test())

def test_text_only_preview_does_not_send_media_group():
    async def _test():
        update = AsyncMock()
        update.message = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "property": {
                "type": "land",
                "area": 500,
                "location": "الرحمانية",
                "price": 300000,
                "photos": ["file_id_1", "file_id_2"]
            }
        }

        res = await show_preview(update, context)
        assert res == PREVIEW
        # Verify reply_media_group was NOT called
        update.message.reply_media_group.assert_not_called()
        # Verify reply_text was called with preview text
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        assert "معاينة العرض" in args[0]
        assert "📸 *عدد الصور:* 2" in args[0]
    asyncio.run(_test())

def test_stealth_admin_notification_on_visitor_post(client, tmp_path):
    mock_visitors_file = str(tmp_path / "visitors.json")

    with patch("main.VISITORS_FILE", mock_visitors_file), \
         patch("main.load_json", return_value=[]), \
         patch("main.save_json") as mock_save, \
         patch("main.telegram_app") as mock_tg_app:

        mock_bot = AsyncMock()
        mock_tg_app.bot = mock_bot

        payload = {
            "type": "special_request",
            "name": "أحمد علي",
            "phone": "0501234567",
            "details": "مطلوب أرض سكنية بالرحمانية"
        }

        response = client.post("/api/visitors", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        assert mock_bot.send_message.call_count == 2
        calls = mock_bot.send_message.call_args_list

        chat_ids = [c.kwargs.get("chat_id") for c in calls]
        assert 544699933 in chat_ids
        assert 545888931 in chat_ids

        for c in calls:
            assert c.kwargs.get("disable_notification") is True
            assert "أحمد علي" in c.kwargs.get("text")
            assert "0501234567" in c.kwargs.get("text")
