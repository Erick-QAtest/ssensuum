from fastapi.testclient import TestClient

from app.main import app


def test_records_known_events_and_summarizes():
    with TestClient(app) as client:
        assert client.post("/events", json={"name": "whatsapp_click", "label": "flotante"}).status_code == 204
        assert client.post("/events", json={"name": "whatsapp_click", "label": "flotante"}).status_code == 204
        assert client.post("/events", json={"name": "page_view", "label": "home"}).status_code == 204

        summary = client.get("/admin/events", params={"days": 1}).json()["events"]
        assert summary["whatsapp_click"]["byLabel"]["flotante"] >= 2
        assert summary["page_view"]["total"] >= 1


def test_rejects_unknown_events():
    with TestClient(app) as client:
        assert client.post("/events", json={"name": "anything"}).status_code == 422
        assert client.post("/events", json={"name": "page_view", "label": "x" * 200}).status_code == 422
