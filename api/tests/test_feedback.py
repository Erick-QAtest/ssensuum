"""Calificación de cada servicio registrado: recepción la pide con un WhatsApp de un clic y el cliente
califica el masaje, a cada masajista y la limpieza, completa sus datos y acepta (o no) promociones."""
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


def served(client, name="Iván Ruiz", therapists=("kevin",), service="swedish") -> dict:
    phone = f"33{datetime.now().strftime('%H%M%S%f')[-8:]}"
    body = {
        "customerName": name, "customerPhone": phone, "serviceId": service, "therapistIds": list(therapists),
        "paidAt": PAID_AT, "amount": 1500, "paymentMethod": "efectivo", "tips": [],
    }
    created = client.post("/admin/records", json=body)
    assert created.status_code == 201, created.text
    return created.json()


def rating(record: dict, **overrides) -> dict:
    body = {
        "massageRating": 5,
        "cleanlinessRating": 4,
        "therapistRatings": [{"therapistId": tid, "rating": 5} for tid in record["therapistIds"]],
        "whatsappOptIn": True,
    }
    body.update(overrides)
    return body


def listed(client, record_id: str) -> dict:
    items = client.get("/admin/records", params={"from": DAY, "days": 1}).json()["items"]
    return next(item for item in items if item["id"] == record_id)


def customer(client, record: dict) -> dict:
    return client.get(f"/customers/{record['customerId']}").json()


def test_each_service_has_a_one_click_whatsapp_to_ask_for_the_rating(client):
    record = served(client)
    request = record["feedbackRequest"]
    assert request["href"].startswith(f"https://wa.me/52{record['customerPhone']}?text=")
    assert unquote(request["href"].split("?text=", 1)[1]) == request["text"]
    assert f"/?calificar={record['id']}" in request["text"]
    assert request["text"].startswith("Hola Iván, gracias por visitarnos en SSENSUUM.")
    assert record["feedbackRequestedAt"] is None

    marked = client.post(f"/admin/records/{record['id']}/feedback-request").json()
    assert marked["feedbackRequestedAt"]
    assert listed(client, record["id"])["feedbackRequestedAt"] == marked["feedbackRequestedAt"]


def test_customer_rates_massage_therapist_and_cleanliness(client):
    record = served(client)
    context = client.get(f"/feedback/{record['id']}").json()
    assert context["firstName"] == "Iván"
    assert context["serviceName"] == "Masaje sueco relajante"
    assert context["therapistIds"] == ["kevin"] and context["therapistNames"] == ["Kevin"]
    assert context["answered"] is False
    assert "phone" not in str(context).lower() and "amount" not in context

    sent = client.post(f"/feedback/{record['id']}", json=rating(record, comment="  Más toallas  "))
    assert sent.status_code == 201, sent.text
    assert sent.json()["comment"] == "Más toallas"
    assert sent.json()["therapistRatings"] == [{"therapistId": "kevin", "rating": 5}]
    assert client.get(f"/feedback/{record['id']}").json()["answered"] is True

    row = listed(client, record["id"])
    assert row["feedback"]["massageRating"] == 5 and row["feedback"]["cleanlinessRating"] == 4
    assert row["feedbackRequest"] is None  # ya calificó: no se vuelve a pedir


def test_each_therapist_of_a_two_therapist_service_is_rated(client):
    record = served(client, therapists=("kevin", "richy"), service="four-hands")
    assert client.get(f"/feedback/{record['id']}").json()["therapistNames"] == ["Kevin", "Richy"]
    only_one = rating(record, therapistRatings=[{"therapistId": "kevin", "rating": 5}])
    assert client.post(f"/feedback/{record['id']}", json=only_one).status_code == 422
    stranger = rating(record, therapistRatings=[{"therapistId": "kevin", "rating": 5}, {"therapistId": "jairo", "rating": 5}])
    assert client.post(f"/feedback/{record['id']}", json=stranger).status_code == 422
    both = rating(record, therapistRatings=[{"therapistId": "richy", "rating": 3}, {"therapistId": "kevin", "rating": 5}])
    assert client.post(f"/feedback/{record['id']}", json=both).status_code == 201


def test_asks_only_for_missing_customer_data_and_fills_it(client):
    record = served(client)
    context = client.get(f"/feedback/{record['id']}").json()
    assert context["asks"] == {"email": True, "birthday": True, "source": True}
    assert {"id": "instagram", "label": "Instagram"} in context["sourceOptions"]

    body = rating(record, email=" Ivan@Correo.MX ", birthday="1990-06-21", source="instagram")
    assert client.post(f"/feedback/{record['id']}", json=body).status_code == 201
    saved = customer(client, record)
    assert saved["email"] == "ivan@correo.mx"
    assert saved["birthday"] == "1990-06-21"
    assert saved["acquisitionSource"] == "instagram"

    # Con los datos completos, la siguiente visita ya no los pide.
    again = served(client, name="Iván Ruiz")
    client.put(f"/admin/records/{again['id']}", json={
        "customerName": "Iván Ruiz", "customerPhone": saved["phone"], "serviceId": "swedish", "therapistIds": ["kevin"],
        "paidAt": PAID_AT, "amount": 1500, "paymentMethod": "efectivo", "tips": [],
    })
    assert client.get(f"/feedback/{again['id']}").json()["asks"] == {"email": False, "birthday": False, "source": False}


def test_bad_customer_data_is_rejected(client):
    record = served(client)
    assert client.post(f"/feedback/{record['id']}", json=rating(record, email="no-es-correo")).status_code == 422
    assert client.post(f"/feedback/{record['id']}", json=rating(record, source="myspace")).status_code == 422
    assert client.post(f"/feedback/{record['id']}", json=rating(record, birthday="2999-01-01")).status_code == 422
    assert client.get(f"/feedback/{record['id']}").json()["answered"] is False


def test_whatsapp_promotions_consent_is_saved_either_way(client):
    yes, no = served(client), served(client)
    assert client.post(f"/feedback/{yes['id']}", json=rating(yes, whatsappOptIn=True)).status_code == 201
    assert client.post(f"/feedback/{no['id']}", json=rating(no, whatsappOptIn=False)).status_code == 201
    accepted, declined = customer(client, yes), customer(client, no)
    assert accepted["whatsappOptIn"] is True and accepted["whatsappOptInAt"]
    assert declined["whatsappOptIn"] is False and declined["whatsappOptInAt"]

    accepted_list = [row["phone"] for row in client.get("/customers", params={"whatsapp": "si", "limit": 200}).json()]
    declined_list = [row["phone"] for row in client.get("/customers", params={"whatsapp": "no", "limit": 200}).json()]
    assert accepted["phone"] in accepted_list and accepted["phone"] not in declined_list
    assert declined["phone"] in declined_list and declined["phone"] not in accepted_list
    assert client.post(f"/feedback/{yes['id']}", json={k: v for k, v in rating(yes).items() if k != "whatsappOptIn"}).status_code in (409, 422)


def test_one_rating_per_visit(client):
    record = served(client)
    assert client.post(f"/feedback/{record['id']}", json=rating(record)).status_code == 201
    assert client.post(f"/feedback/{record['id']}", json=rating(record)).status_code == 409


def test_ratings_must_be_one_to_five(client):
    record = served(client)
    assert client.post(f"/feedback/{record['id']}", json=rating(record, massageRating=6)).status_code == 422
    assert client.post(f"/feedback/{record['id']}", json=rating(record, cleanlinessRating=0)).status_code == 422
    assert client.post(f"/feedback/{record['id']}", json=rating(record, therapistRatings=[{"therapistId": "kevin", "rating": 7}])).status_code == 422
    assert client.get("/feedback/no-existe").status_code == 404
    assert client.post("/feedback/no-existe", json=rating(record)).status_code == 404


def test_records_summary_averages_by_therapist(client):
    for value in (5, 3):
        record = served(client, therapists=("braulio",))
        body = rating(record, therapistRatings=[{"therapistId": "braulio", "rating": value}])
        assert client.post(f"/feedback/{record['id']}", json=body).status_code == 201
    ratings = client.get("/admin/records", params={"from": DAY, "days": 1}).json()["summary"]["ratings"]
    assert ratings["count"] >= 2
    braulio = next(entry for entry in ratings["byTherapist"] if entry["therapistId"] == "braulio")
    assert braulio["therapistName"] == "Braulio" and braulio["count"] >= 2 and 1 <= braulio["average"] <= 5
