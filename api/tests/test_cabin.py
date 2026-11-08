"""El club tiene una sola cabina: dos citas nunca se cruzan, aunque sean con terapeutas
distintos, y entre una y otra quedan 15 minutos para preparar la cabina."""
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain.rules import TZ
from app.main import app

# Trabajan en cualquier horario del club (ver SCHEDULES en app/seed.py).
KEVIN, RICHY, JAIRO = "kevin", "richy", "jairo"


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def day() -> date:
    return datetime.now(TZ).date() + timedelta(days=12)


def at(day: date, hour: int, minute: int = 0) -> str:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TZ).isoformat()


def book(client, therapist_ids, starts_at, **extra):
    body = {"serviceId": "swedish", "therapistIds": therapist_ids, "startsAt": starts_at, **extra}
    return client.post("/reservations", json=body)


def test_same_time_with_another_therapist_is_rejected(client, day):
    assert book(client, [KEVIN], at(day, 12)).status_code == 201
    taken = book(client, [RICHY], at(day, 12))
    assert taken.status_code == 409
    assert "cabina" in taken.json()["detail"]
    assert book(client, [JAIRO], at(day, 11, 30)).status_code == 409
    assert book(client, [JAIRO], at(day, 12, 30)).status_code == 409


def test_next_session_waits_for_the_cabin_turnover(client, day):
    assert book(client, [KEVIN], at(day, 12)).status_code == 201
    # Termina 13:00: pegada o con menos de 15 min no hay tiempo de preparar la cabina.
    assert book(client, [RICHY], at(day, 13)).status_code == 409
    assert book(client, [RICHY], at(day, 13, 10)).status_code == 409
    assert book(client, [RICHY], at(day, 13, 15)).status_code == 201
    # Antes de las 12:00 aplica igual: la anterior debe terminar a las 11:45 o antes.
    assert book(client, [JAIRO], at(day, 10, 50)).status_code == 409
    assert book(client, [JAIRO], at(day, 10, 45)).status_code == 201


def test_another_cabin_id_cannot_skip_the_rule(client, day):
    assert book(client, [KEVIN], at(day, 12)).status_code == 201
    assert book(client, [RICHY], at(day, 12), cabinId="cabin-2").status_code == 409


def test_availability_shows_only_hours_when_the_cabin_is_free(client, day):
    assert book(client, [KEVIN], at(day, 12)).status_code == 201
    slots = client.get("/availability", params={"serviceId": "swedish", "date": day.isoformat()}).json()["slots"]
    # 11:00 acabaría a las 12:00 sin margen; 13:00 empezaría sin margen.
    for busy in ("11:00", "11:30", "12:00", "12:30", "13:00"):
        assert busy not in slots
    assert "10:30" in slots and "13:30" in slots


def test_rescheduling_respects_the_cabin(client, day):
    first = book(client, [KEVIN], at(day, 12)).json()
    assert book(client, [RICHY], at(day, 15)).status_code == 201
    moved = client.patch(f"/reservations/{first['id']}/reschedule", json={"startsAt": at(day, 15, 30)})
    assert moved.status_code == 409
    assert client.patch(f"/reservations/{first['id']}/reschedule", json={"startsAt": at(day, 16, 15)}).status_code == 200
