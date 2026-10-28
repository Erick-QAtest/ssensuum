import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.domain.marketing import CustomerTouch, attribution, clean_source, metric_changes, normalize_channel
from app.domain.rules import TZ
from app.main import app
from app.services import mercadopago

# --- Reglas de dominio ---


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ig", "instagram"),
        ("Instagram", "instagram"),
        ("https://l.instagram.com/?u=https%3A%2F%2Fssensuum.mx", "instagram"),
        ("tt", "tiktok"),
        ("https://www.tiktok.com/@ssensuum", "tiktok"),
        ("twitter", "x"),
        ("https://t.co/abc", "x"),
        ("x.com", "x"),
        ("fb", "facebook"),
        ("m.facebook.com", "facebook"),
        ("https://www.google.com.mx/", "google"),
        ("pinterest.com", None),
        ("t.company.com", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_channel(raw, expected):
    assert normalize_channel(raw) == expected


def test_clean_source_accepts_manual_options():
    assert clean_source("recomendacion") == "recomendacion"
    assert clean_source(" IG ") == "instagram"
    assert clean_source("periódico") is None


def test_metric_changes_against_previous_capture():
    rows = metric_changes([
        {"day": "2026-10-01", "followers": 100, "reach": 900, "interactions": None, "link_clicks": 4},
        {"day": "2026-10-08", "followers": 130, "reach": 700, "interactions": 50, "link_clicks": 9},
    ])
    assert rows[0]["changes"]["followers"] is None
    assert rows[1]["changes"] == {"followers": 30, "reach": -200, "interactions": None, "link_clicks": 5}


def test_attribution_by_source():
    since = date(2026, 10, 1)
    events = [("instagram", "page_view", 40), ("instagram", "reserve_click", 6), (None, "page_view", 10), ("pinterest", "page_view", 3)]
    customers = [
        CustomerTouch("instagram", date(2026, 10, 5), "primera_visita", 1),
        CustomerTouch("instagram", date(2026, 9, 1), "miembro", 5),
        CustomerTouch("instagram", date(2026, 10, 20), "lead", 0),
        CustomerTouch("tiktok", date(2026, 8, 1), "en_riesgo", 3),
        CustomerTouch(None, date(2026, 10, 2), "lead", 0),
    ]
    rows = {row["source"]: row for row in attribution(events, customers, since)}
    instagram = rows["instagram"]
    assert (instagram["visits"], instagram["reserveClicks"]) == (40, 6)
    assert (instagram["newCustomers"], instagram["customers"], instagram["visited"], instagram["recurring"], instagram["members"]) == (2, 3, 2, 1, 1)
    assert instagram["conversion"] == 5.0
    assert rows["tiktok"]["atRisk"] == 1
    assert rows["tiktok"]["conversion"] is None
    # Lo que no viene de una red conocida queda en "sin origen".
    assert rows["sin_origen"]["visits"] == 13
    assert rows["sin_origen"]["newCustomers"] == 1


# --- API ---


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def unique_phone() -> str:
    return "33" + str(uuid.uuid4().int)[:8]


def test_events_keep_channel_and_feed_attribution(client):
    before = {row["source"]: row for row in client.get("/admin/marketing/attribution").json()["rows"]}
    assert client.post("/events", json={"name": "page_view", "label": "home", "channel": "ig"}).status_code == 204
    assert client.post("/events", json={"name": "page_view", "label": "home", "channel": "https://www.tiktok.com/"}).status_code == 204
    after = {row["source"]: row for row in client.get("/admin/marketing/attribution").json()["rows"]}
    assert after["instagram"]["visits"] == before["instagram"]["visits"] + 1
    assert after["tiktok"]["visits"] == before["tiktok"]["visits"] + 1


def test_checkout_saves_first_channel_only(client, monkeypatch):
    monkeypatch.setattr(settings, "mp_access_token", "TEST-token")
    monkeypatch.setattr(mercadopago, "create_preference", lambda **kwargs: {"init_point": "x", "sandbox_init_point": "x"})
    phone = unique_phone()
    for offset, channel in ((7, "ig"), (8, "fb")):
        starts = (datetime.now(TZ) + timedelta(days=offset)).date().isoformat()
        response = client.post("/checkout", json={
            "serviceId": "massage-special", "therapistIds": [], "startsAt": f"{starts}T13:00:00-06:00",
            "firstName": "Iker", "phone": phone, "channel": channel,
        })
        assert response.status_code == 201, response.text
    customer = client.get("/customers", params={"q": phone}).json()[0]
    assert customer["acquisitionSource"] == "instagram"

    by_source = client.get("/customers", params={"source": "instagram", "limit": 200}).json()
    assert phone in [row["phone"] for row in by_source]
    funnel = client.get("/customers/funnel", params={"source": "instagram"}).json()
    assert funnel["total"] >= 1
    assert client.get("/customers", params={"source": "myspace"}).status_code == 422


def test_record_asks_how_they_found_us(client):
    therapist = client.get("/therapists").json()[0]["id"]
    phone = unique_phone()
    body = {
        "customerName": "Leo Ruiz", "customerPhone": phone, "serviceId": "massage-special", "therapistIds": [therapist],
        "paidAt": "2026-10-20T18:00:00-06:00", "amount": 1500, "paymentMethod": "efectivo", "customerSource": "recomendacion",
    }
    assert client.post("/admin/records", json=body).status_code == 201
    assert client.post("/admin/records", json={**body, "customerSource": "tiktok"}).status_code == 201
    customer = client.get("/customers", params={"q": phone}).json()[0]
    assert customer["acquisitionSource"] == "recomendacion"
    assert client.post("/admin/records", json={**body, "customerSource": "radio"}).status_code == 422

    # Se corrige a mano desde la ficha.
    updated = client.patch(f"/customers/{customer['id']}", json={"acquisitionSource": "tiktok"}).json()
    assert updated["acquisitionSource"] == "tiktok"


def test_calendar_and_ideas(client):
    idea = client.post("/admin/marketing/ideas", json={"pillar": "equipo", "hook": "  Un día con   Mazer "}).json()
    assert idea["hook"] == "Un día con Mazer"
    post = client.post("/admin/marketing/posts", json={
        "channel": "instagram", "publishOn": "2026-11-03", "format": "reel", "pillar": "equipo",
        "title": "Presentación de Mazer", "ideaId": idea["id"],
    })
    assert post.status_code == 201, post.text
    post = post.json()
    assert post["status"] == "idea"

    published = client.put(f"/admin/marketing/posts/{post['id']}", json={
        **{key: post[key] for key in ("channel", "publishOn", "format", "pillar", "title", "ideaId")},
        "status": "publicado", "url": "https://instagram.com/p/abc",
    }).json()
    assert published["statusLabel"] == "Publicado"

    listed = client.get("/admin/marketing/posts", params={"from": "2026-11-01", "to": "2026-11-30"}).json()
    assert post["id"] in [row["id"] for row in listed]
    ideas = {row["id"]: row for row in client.get("/admin/marketing/ideas").json()}
    assert ideas[idea["id"]]["used"] == 1

    bad = {"channel": "myspace", "publishOn": "2026-11-03", "format": "reel", "title": "x"}
    assert client.post("/admin/marketing/posts", json=bad).status_code == 422
    assert client.post("/admin/marketing/posts", json={**bad, "channel": "x", "url": "instagram.com"}).status_code == 422

    assert client.delete(f"/admin/marketing/posts/{post['id']}").status_code == 204
    assert client.delete(f"/admin/marketing/ideas/{idea['id']}").status_code == 204


def test_metrics_one_capture_per_channel_and_day(client):
    first = client.post("/admin/marketing/metrics", json={"channel": "facebook", "day": "2026-09-01", "followers": 200})
    assert first.status_code == 201
    client.post("/admin/marketing/metrics", json={"channel": "facebook", "day": "2026-09-08", "followers": 210, "reach": 1500})
    rows = client.post("/admin/marketing/metrics", json={"channel": "facebook", "day": "2026-09-08", "followers": 215, "reach": 1500}).json()
    facebook = next(row for row in rows if row["channel"] == "facebook")
    september = [row for row in facebook["snapshots"] if row["day"].startswith("2026-09")]
    assert [row["day"] for row in september] == ["2026-09-08", "2026-09-01"]
    assert september[0]["followers"] == 215
    assert september[0]["changes"]["followers"] == 15

    future = (datetime.now(TZ).date() + timedelta(days=2)).isoformat()
    assert client.post("/admin/marketing/metrics", json={"channel": "facebook", "day": future, "followers": 1}).status_code == 422
    assert client.post("/admin/marketing/metrics", json={"channel": "facebook", "day": "2026-09-15"}).status_code == 422
