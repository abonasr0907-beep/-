# bot/modules/social_media.py (جديد)

import os
try:
    import tweepy
except ImportError:
    tweepy = None

TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")

class TwitterPublisher:
    def __init__(self):
        if tweepy and TWITTER_API_KEY and TWITTER_API_SECRET:
            auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
            auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
            self.api = tweepy.API(auth)
        else:
            self.api = None

    def publish_property(self, property_obj):
        if not self.api:
            print("Twitter API not configured")
            return None

        # توليد النص التسويقي
        text = self.generate_tweet_text(property_obj)

        # نشر التغريدة
        try:
            tweet = self.api.update_status(text)
            return getattr(tweet, 'id', None)
        except Exception as e:
            print(f"Twitter publish error: {e}")
            return None

    def generate_tweet_text(self, property_obj):
        prop_type = property_obj.get('type', 'عقار')
        price = property_obj.get('price', 0)
        location = property_obj.get('location', property_obj.get('area', 'الخرج'))
        size_sqm = property_obj.get('size_sqm', property_obj.get('area_sqm', 0))
        link = property_obj.get('property_link', f"https://abonasr0907-beep.github.io/?p={property_obj.get('id', '')}")

        hashtags = f"#{prop_type} #عقارات_الخرج #السعودية"

        text = (
            f"🏠 {property_obj.get('title', 'عقار مميز')}\n"
            f"💰 السعر: {price:,} SAR\n"
            f"📍 الموقع: {location}\n"
            f"📐 المساحة: {size_sqm:,} م²\n\n"
            f"🔗 {link}\n\n"
            f"{hashtags}"
        )

        return text[:280]  # Twitter limit
