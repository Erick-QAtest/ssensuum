import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def unique_phone() -> str:
    return "33" + str(uuid.uuid4().int)[:8]


def therapists(client) -> list[str]:
    return [row["id"] for row in client.get("/therapists").json()]


def record_body(client, phone: str, **overrides) -> dict:
    ids = therapists(client)[:2]
    body = {
        "customerName": " Ana   López ",
        "customerPhone": f"+52 {phone}",
        "serviceId": "four-hands",
        "therapistIds": ids,
        "paidAt": "2026-03-10T18:30:00-06:00",
        "amount": 3000,
        "paymentMethod": "Tarjeta",
        "tips": [{"therapistId": ids[0], "amount": 200}, {"therapistId": ids[1], "amount": 150}],
        "tipMethod": "efectivo",
    }
    body.update(overrides)
    return body


def test_create_record_links_customer_and_summarizes_tips(client):
    phone = unique_phone()
    created = client.post("/admin/records", json=record_body(client, phone))
    assert created.status_code == 201
    record = created.json()
    assert record["customerName"] == "Ana López"
    assert record["customerPhone"] == phone
    assert record["serviceName"] == "Masaje a 4 manos"
    assert record["paymentMethod"] == "tarjeta"
    assert record["tipTotal"] == 350
    assert len(record["therapistNames"]) == 2

    customer = client.get(f"/customers/{record['customerId']}").json()
    assert customer["phone"] == phone
    assert customer["firstName"] == "Ana"

    listed = client.get("/admin/records", params={"from": "2026-03-10", "days": 1}).json()
    assert record["id"] in [item["id"] for item in listed["items"]]
    assert listed["summary"]["tips"] >= 350
    assert listed["summary"]["byPaymentMethod"]["tarjeta"] >= 3000
    assert {entry["therapistId"] for entry in listed["summary"]["tipsByTherapist"]} >= set(record["therapistIds"])

    other_day = client.get("/admin/records", params={"from": "2026-03-11", "days": 1}).json()
    assert record["id"] not in [item["id"] for item in other_day["items"]]


def test_reuses_existing_customer(client):
    phone = unique_phone()
    existing = client.post("/customers", json={"phone": phone, "firstName": "Luis"}).json()
    record = client.post("/admin/records", json=record_body(client, phone, tips=[])).json()
    assert record["customerId"] == existing["id"]
    assert record["tipMethod"] is None


def test_update_and_delete_record(client):
    record = client.post("/admin/records", json=record_body(client, unique_phone())).json()
    updated = client.put(f"/admin/records/{record['id']}", json=record_body(client, record["customerPhone"], amount=2400, tips=[]))
    assert updated.status_code == 200
    assert updated.json()["amount"] == 2400
    assert updated.json()["tipTotal"] == 0

    assert client.delete(f"/admin/records/{record['id']}").status_code == 204
    assert client.delete(f"/admin/records/{record['id']}").status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"customerPhone": "123"},
        {"customerName": "  "},
        {"serviceId": "nope"},
        {"therapistIds": []},
        {"paymentMethod": "cheque"},
        {"amount": -1},
        {"paidAt": "ayer"},
        {"tips": [{"therapistId": "nadie", "amount": 100}]},
    ],
)
def test_rejects_invalid_records(client, overrides):
    assert client.post("/admin/records", json=record_body(client, unique_phone(), **overrides)).status_code == 422
