import time
import pytest
from fastapi.testclient import TestClient
from main import app, CRM_EVENTS

client = TestClient(app)

def test_crm_events_api():
    # Test POST /api/events
    payload = {
        "type": "whatsapp_click",
        "details": {"button": "واتساب المستشار"},
        "url": "http://localhost/seo/رحمانية-اراضي.html"
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "ok"
    assert "event_id" in res_data

    # Test GET /api/events
    response_get = client.get("/api/events")
    assert response_get.status_code == 200
    events_data = response_get.json()
    assert events_data["total"] >= 1
    assert any(e["type"] == "whatsapp_click" for e in events_data["events"])

def test_rate_limiting_middleware():
    # Make multiple rapid requests to /api/properties
    for _ in range(5):
        resp = client.get("/api/properties")
        assert resp.status_code == 200

def test_properties_archived_filtering():
    # Test GET /api/properties (active only)
    resp_active = client.get("/api/properties")
    assert resp_active.status_code == 200

    # Test GET /api/properties/all (includes archived flag)
    resp_all = client.get("/api/properties/all")
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert isinstance(all_data, list)
