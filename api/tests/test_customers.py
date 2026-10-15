import uuid

import pytest
from fastapi.testclient import TestClient

from app.domain.customers import normalize_phone
from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def unique_phone() -> str:
    return "33" + str(uuid.uuid4().int)[:8]


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("3310000001", "3310000001"),
        ("33 1000 0001", "3310000001"),
        ("(33) 1000-0001", "3310000001"),
        ("+52 33 1000 0001", "3310000001"),
        ("+52 1 33 1000 0001", "3310000001"),
        ("12345", None),
        ("331000000199", None),
        ("", None),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_create_and_get_customer(client):
    phone = unique_phone()
    created = client.post(
        "/customers",
        json={"phone": f"+52 {phone}", "firstName": " Ana ", "lastName": "López", "email": "Ana@Example.com", "birthday": "1990-05-17"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["phone"] == phone
    assert body["firstName"] == "Ana"
    assert body["lastName"] == "López"
    assert body["email"] == "ana@example.com"
    assert body["birthday"] == "1990-05-17"
    assert body["createdAt"]

    fetched = client.get(f"/customers/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_phone_is_unique_across_formats(client):
    phone = unique_phone()
    assert client.post("/customers", json={"phone": phone, "firstName": "Ana"}).status_code == 201
    duplicate = client.post("/customers", json={"phone": f"+52 {phone[:2]} {phone[2:6]} {phone[6:]}", "firstName": "Otra"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Ya existe un cliente con ese teléfono"


@pytest.mark.parametrize(
    "payload,detail",
    [
        ({"phone": "12345", "firstName": "Ana"}, "El teléfono debe tener 10 dígitos"),
        ({"phone": "3399990001", "firstName": "   "}, "El nombre es obligatorio"),
        ({"phone": "3399990002", "firstName": "Ana", "email": "no-es-correo"}, "El correo no es válido"),
    ],
)
def test_create_rejects_invalid_data(client, payload, detail):
    response = client.post("/customers", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == detail


def test_create_requires_phone_and_first_name(client):
    assert client.post("/customers", json={"firstName": "Ana"}).status_code == 422
    assert client.post("/customers", json={"phone": unique_phone()}).status_code == 422
    assert client.post("/customers", json={"phone": unique_phone(), "firstName": "Ana", "birthday": "17/05/1990"}).status_code == 422


def test_get_unknown_customer(client):
    response = client.get("/customers/nope")
    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente no encontrado"


def test_update_customer(client):
    customer = client.post("/customers", json={"phone": unique_phone(), "firstName": "Ana", "email": "ana@example.com"}).json()
    new_phone = unique_phone()

    updated = client.patch(f"/customers/{customer['id']}", json={"phone": new_phone, "lastName": "Ruiz", "email": None})
    assert updated.status_code == 200
    body = updated.json()
    assert body["phone"] == new_phone
    assert body["firstName"] == "Ana"
    assert body["lastName"] == "Ruiz"
    assert body["email"] is None

    same_phone = client.patch(f"/customers/{customer['id']}", json={"phone": new_phone})
    assert same_phone.status_code == 200

    assert client.patch(f"/customers/{customer['id']}", json={"firstName": ""}).status_code == 422
    assert client.patch("/customers/nope", json={"lastName": "X"}).status_code == 404


def test_update_cannot_take_another_customers_phone(client):
    first = client.post("/customers", json={"phone": unique_phone(), "firstName": "Ana"}).json()
    second = client.post("/customers", json={"phone": unique_phone(), "firstName": "Luis"}).json()
    response = client.patch(f"/customers/{second['id']}", json={"phone": first["phone"]})
    assert response.status_code == 409


def test_search_customers(client):
    tag = uuid.uuid4().hex[:8]
    phone = unique_phone()
    client.post("/customers", json={"phone": phone, "firstName": f"Zoe{tag}", "lastName": "Prueba"})
    client.post("/customers", json={"phone": unique_phone(), "firstName": "Otro", "lastName": f"Apellido{tag}"})

    by_name = client.get("/customers", params={"q": tag}).json()
    assert len(by_name) == 2

    by_phone = client.get("/customers", params={"q": f"+52 {phone}"}).json()
    assert [row["phone"] for row in by_phone] == [phone]

    assert len(client.get("/customers", params={"q": tag, "limit": 1}).json()) == 1
    assert client.get("/customers", params={"q": "sin-coincidencias-" + tag}).json() == []
    assert client.get("/customers", params={"limit": 0}).status_code == 422
