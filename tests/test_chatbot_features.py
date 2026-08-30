import os
import json
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_javascript_files_exist():
    js_dir = os.path.join(os.path.dirname(__file__), "..", "js")
    files_to_check = [
        ("chatbot.js", ["AI_KNOWLEDGE", "setChatContext", "getAIResponse", "calculateSimilarity"]),
        ("faq.js", ["FAQ_DATA", "renderFAQ", "toggleFAQ"]),
        ("booking.js", ["class BookingSystem", "renderBookingForm", "handleSubmit"]),
        ("inquiry.js", ["class InquirySystem", "showInquiryModal", "handleSubmit"]),
        ("compare.js", ["class PropertyComparison", "addToCompare", "showComparison"]),
        ("mortgage-calculator.js", ["class MortgageCalculator", "renderCalculator", "calculate"]),
        ("recommendations.js", ["class PropertyRecommender", "recommend", "renderRecommendationForm"])
    ]

    for filename, expected_tokens in files_to_check:
        filepath = os.path.join(js_dir, filename)
        assert os.path.exists(filepath), f"{filename} does not exist"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            for token in expected_tokens:
                assert token in content, f"{token} not found in {filename}"

def test_api_bookings_endpoint():
    payload = {
        "name": "اختبار حجز",
        "phone": "0500000000",
        "email": "test@example.com",
        "date": "2025-09-01",
        "time": "10:00",
        "notes": "معاينة المزرعة",
        "propertyId": "PROP-0000000001"
    }
    response = client.post("/api/bookings", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "id" in data
    assert data.get("id").startswith("BOOK-")

def test_api_inquiries_endpoint():
    payload = {
        "name": "اختبار استفسار",
        "phone": "0511111111",
        "email": "inquiry@example.com",
        "question": "هل السعر قابل للتفاوض؟",
        "propertyId": "PROP-0000000002"
    }
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "id" in data
    assert data.get("id").startswith("INQ-")
