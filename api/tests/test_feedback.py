"""Calificación de cada servicio registrado: recepción pide la calificación con un SMS de un clic."""
from datetime import datetime
from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from app.main import app

PAID_AT = "2026-04-14T13:00:00-06:00"
DAY = "2026-04-14"


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def served(client, name="Iván Ruiz") -> dict:
    phone = f"33{datetime.now().strftime('%H%M%S%f')[-8:]}"
    body = {
        "customerName": name, "customerPhone": phone, "serviceId": "swedish", "therapistIds": ["kevin"],
        "paidAt": PAID_AT, "amount": 1500, "paymentMethod": "efectivo", "tips": [], "source": "instagram",
    }
    created = client.post("/admin/records", json=body)
    assert created.status_code == 201, created.text
    return created.json()


def listed(client, record_id: str) -> dict:
    items = client.get("/admin/records", params={"from": DAY, "days": 1}).json()["items"]
    return next(item for item in items if item["id"] == record_id)


def test_each_service_has_a_one_click_sms_to_ask_for_the_rating(client):
    record = served(client)
    request = record["feedbackRequest"]
    assert request["href"].startswith(f"sms:+52{record['customerPhone']}?&body=")
    assert f"/?calificar={record['id']}" in unquote(request["href"])
    # Sin acentos, como los recordatorios: así el SMS cabe en el alfabeto básico.
    assert request["text"].startswith("SSENSUUM: Hola Ivan, gracias por tu visita.")
    assert not any(char in request["text"] for char in "áíóú")
    assert record["feedbackRequestedAt"] is None

    marked = client.post(f"/admin/records/{record['id']}/feedback-request").json()
    assert marked["feedbackRequestedAt"]
    assert listed(client, record["id"])["feedbackRequestedAt"] == marked["feedbackRequestedAt"]


def test_customer_rates_massage_and_cleanliness(client):
    record = served(client)
    context = client.get(f"/feedback/{record['id']}").json()
    assert context["firstName"] == "Iván"
    assert context["serviceName"] == "Masaje sueco relajante"
    assert context["serviceId"] == "swedish" and context["therapistIds"] == ["kevin"]
    assert context["therapistNames"] == ["Kevin"]
    assert context["answered"] is False
    assert "phone" not in str(context).lower() and "amount" not in context

    sent = client.post(f"/feedback/{record['id']}", json={"massageRating": 5, "cleanlinessRating": 4, "comment": "  Más toallas  "})
    assert sent.status_code == 201, sent.text
    assert sent.json()["comment"] == "Más toallas"
    assert client.get(f"/feedback/{record['id']}").json()["answered"] is True

    row = listed(client, record["id"])
    assert row["feedback"]["massageRating"] == 5 and row["feedback"]["cleanlinessRating"] == 4
    assert row["feedbackRequest"] is None  # ya calificó: no se vuelve a pedir


def test_one_rating_per_visit(client):
    record = served(client)
    body = {"massageRating": 5, "cleanlinessRating": 5}
    assert client.post(f"/feedback/{record['id']}", json=body).status_code == 201
    assert client.post(f"/feedback/{record['id']}", json=body).status_code == 409


def test_ratings_must_be_one_to_five(client):
    record = served(client)
    assert client.post(f"/feedback/{record['id']}", json={"massageRating": 6, "cleanlinessRating": 5}).status_code == 422
    assert client.post(f"/feedback/{record['id']}", json={"massageRating": 0, "cleanlinessRating": 5}).status_code == 422
    assert client.post(f"/feedback/{record['id']}", json={"massageRating": 5}).status_code == 422
    assert client.get("/feedback/no-existe").status_code == 404
    assert client.post("/feedback/no-existe", json={"massageRating": 5, "cleanlinessRating": 5}).status_code == 404


def test_records_summary_averages_the_ratings(client):
    for massage, cleanliness in ((5, 4), (3, 5)):
        record = served(client)
        client.post(f"/feedback/{record['id']}", json={"massageRating": massage, "cleanlinessRating": cleanliness})
    ratings = client.get("/admin/records", params={"from": DAY, "days": 1}).json()["summary"]["ratings"]
    assert ratings["count"] >= 2
    assert 1 <= ratings["massage"] <= 5 and 1 <= ratings["cleanliness"] <= 5
