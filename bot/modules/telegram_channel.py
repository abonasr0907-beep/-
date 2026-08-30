# bot/modules/telegram_channel.py (جديد)

import os
from telegram import Bot
from bot.config import BOT_TOKEN

TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

class TelegramChannelPublisher:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
        self.channel_id = TELEGRAM_CHANNEL_ID

    async def publish_property(self, property_obj):
        if not self.bot or not self.channel_id:
            print("Telegram Bot or Channel ID not configured")
            return False

        price = property_obj.get('price', 0)
        location = property_obj.get('location', property_obj.get('area', 'الخرج'))
        size_sqm = property_obj.get('size_sqm', property_obj.get('area_sqm', 0))
        link = property_obj.get('property_link', f"https://abonasr0907-beep.github.io/?p={property_obj.get('id', '')}")

        text = (
            f"🏠 *{property_obj.get('title', 'عقار مميز')}*\n\n"
            f"💰 السعر: `{price:,} SAR`\n"
            f"📍 الموقع: {location}\n"
            f"📐 المساحة: {size_sqm:,} م²\n"
            f"🏷️ النوع: {property_obj.get('type', 'عقار')}\n\n"
            f"🔗 [عرض التفاصيل]({link})\n\n"
            f"📱 للتواصل: 0567890123"
        )

        try:
            # إرسال الصورة إن وجدت
            if property_obj.get('photos') and len(property_obj['photos']) > 0 and os.path.exists(property_obj['photos'][0]):
                with open(property_obj['photos'][0], 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=photo,
                        caption=text,
                        parse_mode='Markdown'
                    )
            else:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=text,
                    parse_mode='Markdown'
                )

            return True
        except Exception as e:
            print(f"Telegram channel publish error: {e}")
            return False
