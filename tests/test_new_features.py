import os
import pytest
import asyncio
from bot.modules.sitemap_generator import generate_sitemap, add_url
from bot.modules.social_media import TwitterPublisher
from bot.modules.telegram_channel import TelegramChannelPublisher
from bot.modules.compass_api import REGACompassAPI

def test_sitemap_generator(tmp_path):
    output_file = str(tmp_path / "test_sitemap.xml")
    res = generate_sitemap(output_file)
    assert os.path.exists(res)
    with open(res, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'urlset' in content
    assert 'https://abonasr0907-beep.github.io/' in content

def test_twitter_publisher():
    publisher = TwitterPublisher()
    sample_prop = {
        'id': 'PROP-0000000001',
        'title': 'فيلا فاخرة',
        'price': 1500000,
        'location': 'الرحمانية',
        'size_sqm': 500,
        'type': 'land'
    }
    tweet_text = publisher.generate_tweet_text(sample_prop)
    assert 'فيلا فاخرة' in tweet_text
    assert '1,500,000 SAR' in tweet_text
    assert len(tweet_text) <= 280

def test_telegram_channel_publisher():
    publisher = TelegramChannelPublisher()
    sample_prop = {
        'id': 'PROP-0000000001',
        'title': 'استراحة فاخرة',
        'price': 800000,
        'location': 'العفجة',
        'size_sqm': 1000,
        'type': 'resthouse'
    }
    # Without BOT_TOKEN or TELEGRAM_CHANNEL_ID, publish returns False gracefully
    result = asyncio.run(publisher.publish_property(sample_prop))
    assert result is False

def test_compass_api():
    api = REGACompassAPI()
    assert api.base_url == "https://api.rega.gov.sa/v1"
    # Calling without valid REGA API key should return None gracefully
    index = api.get_area_price_index("الرحمانية")
    assert index is None

def test_new_assets_exist():
    assert os.path.exists("css/property-card.css")
    assert os.path.exists("css/property-features.css")
    assert os.path.exists("css/skeletons.css")
    assert os.path.exists("css/theme-toggle.css")
    assert os.path.exists("js/marketing-phrases.js")
    assert os.path.exists("js/property-features.js")
    assert os.path.exists("js/pdf-export.js")
    assert os.path.exists("js/seo-landing-pages.js")
    assert os.path.exists("js/skeleton-loader.js")
    assert os.path.exists("js/theme-toggle.js")
    assert os.path.exists("js/price-chart.js")
