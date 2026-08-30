# bot/modules/compass_api.py (جديد)

import os
import requests
from datetime import datetime

REGA_API_KEY = os.environ.get("REGA_API_KEY", "")
REGA_API_URL = os.environ.get("REGA_API_URL", "https://api.rega.gov.sa/v1")

class REGACompassAPI:
    def __init__(self):
        self.api_key = REGA_API_KEY
        self.base_url = REGA_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get_area_price_index(self, area_name):
        """
        الحصول على مؤشر أسعار المنطقة من البوصلة العقارية
        """
        try:
            response = requests.get(
                f"{self.base_url}/price-index",
                headers=self.headers,
                params={'area': area_name},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'avg_price_per_sqm': data.get('average_price_per_sqm', 0),
                    'price_trend': data.get('trend', 'stable'),
                    'last_updated': data.get('last_updated', datetime.now().isoformat()),
                    'transactions_count': data.get('transactions_count', 0),
                }

            return None
        except Exception as e:
            print(f"REGA API error: {e}")
            return None

    def get_property_valuation(self, property_data):
        """
        الحصول على التقييم العقاري من REGA
        """
        try:
            response = requests.post(
                f"{self.base_url}/valuation",
                headers=self.headers,
                json={
                    'area': property_data.get('location', property_data.get('area')),
                    'type': property_data.get('type'),
                    'size': property_data.get('size_sqm', property_data.get('area_sqm')),
                    'features': property_data.get('features', {}),
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

            return None
        except Exception as e:
            print(f"REGA valuation error: {e}")
            return None
