import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Reservation
from app.services import mercadopago

TZ = ZoneInfo("America/Mexico_City")


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def mp(monkeypatch):
    """Simula Mercado Pago: guarda las preferencias creadas y responde los pagos registrados."""
    state = {"preferences": [], "payments": {}}
    monkeypatch.setattr(settings, "mp_access_token", "TEST-token")

    def create_preference(**kwargs):
        state["preferences"].append(kwargs)
        return {"init_point": "https://mp.example/live", "sandbox_init_point": "https://mp.example/sandbox"}

    monkeypatch.setattr(mercadopago, "create_preference", create_preference)
    monkeypatch.setattr(mercadopago, "get_payment", lambda payment_id: state["payments"][payment_id])
    return state


def day(offset: int) -> str:
    return (datetime.now(TZ) + timedelta(days=offset)).date().isoformat()


def checkout_body(date: str, hour: str, **overrides) -> dict:
    body = {
        "serviceId": "massage-special",
        "therapistIds": [],
        "startsAt": f"{date}T{hour}:00-06:00",
        "firstName": "Ana",
        "phone": "33" + str(uuid.uuid4().int)[:8],
    }
    body.update(overrides)
    return body


def approved(reservation_id: str, amount: float = 300) -> dict:
    return {"status": "approved", "currency_id": "MXN", "transaction_amount": amount, "external_reference": reservation_id}


def test_checkout_unavailable_without_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "mp_access_token", "")
    response = client.post("/checkout", json=checkout_body(day(3), "10:00"))
    assert response.status_code == 503


def test_checkout_holds_slot_and_assigns_therapist(client, mp):
    date = day(4)
    response = client.post("/checkout", json=checkout_body(date, "11:00"))
    assert response.status_code == 201
    body = response.json()
    assert body["checkoutUrl"] == "https://mp.example/sandbox"
    reservation = body["reservation"]
    assert reservation["status"] == "PENDING_PAYMENT"
    assert len(reservation["therapistIds"]) == 1
    assert reservation["holdExpiresAt"]
    assert mp["preferences"][0]["amount"] == 300

    slots = client.get("/availability", params={"serviceId": "massage-special", "date": date}).json()["slots"]
    assert "11:00" not in slots


def test_approved_payment_confirms_reservation(client, mp):
    reservation_id = client.post("/checkout", json=checkout_body(day(5), "12:00")).json()["reservation"]["id"]
    mp["payments"]["111"] = approved(reservation_id)

    response = client.post("/payments/111/sync")
    assert response.json()["reservation"]["status"] == "CONFIRMED"
    assert client.get(f"/reservations/{reservation_id}").json()["holdExpiresAt"] is None


def test_partial_payment_does_not_confirm(client, mp):
    reservation_id = client.post("/checkout", json=checkout_body(day(5), "15:00")).json()["reservation"]["id"]
    mp["payments"]["222"] = approved(reservation_id, amount=100)

    assert client.post("/payments/222/sync").json()["reservation"]["status"] == "PENDING_PAYMENT"


def expire_hold(reservation_id: str) -> None:
    with SessionLocal() as db:
        reservation = db.get(Reservation, reservation_id)
        reservation.hold_expires_at = datetime.now(TZ) - timedelta(minutes=1)
        db.commit()


def test_expired_hold_releases_slot(client, mp):
    date = day(6)
    reservation_id = client.post("/checkout", json=checkout_body(date, "13:00")).json()["reservation"]["id"]
    expire_hold(reservation_id)

    assert client.get(f"/reservations/{reservation_id}").json()["status"] == "EXPIRED"
    slots = client.get("/availability", params={"serviceId": "massage-special", "date": date}).json()["slots"]
    assert "13:00" in slots


def test_late_payment_on_taken_slot_needs_attention(client, mp):
    date = day(7)
    late_id = client.post("/checkout", json=checkout_body(date, "14:00")).json()["reservation"]["id"]
    expire_hold(late_id)
    assert client.post("/checkout", json=checkout_body(date, "14:00")).status_code == 201

    mp["payments"]["333"] = approved(late_id)
    assert client.post("/payments/333/sync").json()["reservation"]["status"] == "NEEDS_ATTENTION"


def test_webhook_syncs_only_payment_events(client, mp):
    reservation_id = client.post("/checkout", json=checkout_body(day(8), "16:00")).json()["reservation"]["id"]
    mp["payments"]["444"] = approved(reservation_id)

    assert client.post("/payments/webhook", params={"type": "merchant_order", "data.id": "444"}).status_code == 200
    assert client.get(f"/reservations/{reservation_id}").json()["status"] == "PENDING_PAYMENT"

    assert client.post("/payments/webhook", json={"type": "payment", "data": {"id": "444"}}).status_code == 200
    assert client.get(f"/reservations/{reservation_id}").json()["status"] == "CONFIRMED"


def test_checkout_rejects_invalid_phone(client, mp):
    response = client.post("/checkout", json=checkout_body(day(9), "10:00", phone="123"))
    assert response.status_code == 422


def test_payments_status_reflects_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "mp_access_token", "")
    assert client.get("/payments/status").json() == {"enabled": False}
    monkeypatch.setattr(settings, "mp_access_token", "TEST-token")
    assert client.get("/payments/status").json() == {"enabled": True}


def test_retry_reuses_hold_after_rejected_payment(client, mp):
    reservation_id = client.post("/checkout", json=checkout_body(day(10), "11:00")).json()["reservation"]["id"]

    retry = client.post(f"/checkout/{reservation_id}/retry")
    assert retry.status_code == 200
    assert retry.json()["checkoutUrl"] == "https://mp.example/sandbox"
    assert len(mp["preferences"]) == 2


def test_retry_refused_once_hold_expired(client, mp):
    reservation_id = client.post("/checkout", json=checkout_body(day(10), "13:00")).json()["reservation"]["id"]
    expire_hold(reservation_id)

    assert client.post(f"/checkout/{reservation_id}/retry").status_code == 409


def test_admin_reservations_lists_paid_and_pending_with_customer(client, mp):
    date = day(11)
    body = checkout_body(date, "10:00", firstName="Lucía")
    paid_id = client.post("/checkout", json=body).json()["reservation"]["id"]
    mp["payments"]["555"] = approved(paid_id)
    client.post("/payments/555/sync")
    expired_id = client.post("/checkout", json=checkout_body(date, "12:00")).json()["reservation"]["id"]
    expire_hold(expired_id)

    items = client.get("/admin/reservations", params={"from": date, "days": 1}).json()["items"]
    by_id = {item["id"]: item for item in items}
    assert by_id[paid_id]["status"] == "CONFIRMED"
    assert by_id[paid_id]["paymentId"] == "555"
    assert by_id[paid_id]["customer"]["firstName"] == "Lucía"
    assert by_id[paid_id]["serviceName"] == "Masaje especial SSENSUUM"
    assert by_id[paid_id]["therapistNames"]
    assert expired_id not in by_id
