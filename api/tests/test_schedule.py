from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain.errors import ValidationError
from app.domain.rules import TZ
from app.domain.schedule import normalize, works
from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def next_weekday(weekday: int) -> date:
    """El próximo día de la semana pedido, con al menos 2 días de margen para la anticipación mínima."""
    day = datetime.now(TZ).date() + timedelta(days=2)
    return day + timedelta(days=(weekday - day.weekday()) % 7)


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TZ)


MAZER = {"days": {"0": [["17:00", "20:30"]], "2": [["15:00", "16:00"]]}}


def test_session_must_fit_inside_a_window():
    monday, wednesday = next_weekday(0), next_weekday(2)
    assert works(MAZER, at(monday, 17), at(monday, 18))
    assert works(MAZER, at(monday, 19, 30), at(monday, 20, 30))
    assert not works(MAZER, at(monday, 16, 30), at(monday, 17, 30))
    assert works(MAZER, at(wednesday, 15), at(wednesday, 16))
    assert not works(MAZER, at(wednesday, 15, 30), at(wednesday, 16, 30))
    assert not works(MAZER, at(next_weekday(1), 17), at(next_weekday(1), 18))
    assert works({"always": True}, at(monday, 9), at(monday, 10))
    assert works(None, at(monday, 9), at(monday, 10))


def test_normalize_rejects_bad_schedules():
    assert normalize({"always": True, "days": {"0": [["01:00", "02:00"]]}}) == {"always": True}
    assert normalize({"days": {"1": [["15:00", "16:00"], ["09:00", "10:00"]], "2": []}}) == {"days": {"1": [["09:00", "10:00"], ["15:00", "16:00"]]}}
    for bad in ({"days": {}}, {"days": {"7": [["09:00", "10:00"]]}}, {"days": {"0": [["10:00", "09:00"]]}},
                {"days": {"0": [["9:00", "10:00"]]}}, {"days": {"0": [["09:00", "11:00"], ["10:00", "12:00"]]}}):
        with pytest.raises(ValidationError):
            normalize(bad)


def test_document_schedules_are_loaded(client):
    staff = {row["id"]: row for row in client.get("/admin/rh/staff").json()}
    assert staff["kevin"]["schedule"] == {"always": True}
    assert staff["braulio"]["schedule"] == {"always": True}
    assert staff["borja"]["schedule"]["days"]["4"] == [["09:00", "14:00"]]
    assert "3" not in staff["borja"]["schedule"]["days"]
    assert staff["aleman"]["schedule"] is None


def test_slots_follow_the_therapist_schedule(client):
    slots = client.get("/availability", params={"serviceId": "swedish", "date": next_weekday(2).isoformat(), "therapistId": "mazer"}).json()["slots"]
    assert slots == ["15:00"]
    thursday = client.get("/availability", params={"serviceId": "swedish", "date": next_weekday(3).isoformat(), "therapistId": "borja"}).json()["slots"]
    assert thursday == []


def test_cannot_book_outside_the_schedule(client):
    body = {"serviceId": "swedish", "therapistIds": ["borja"], "startsAt": at(next_weekday(3), 11).isoformat()}
    response = client.post("/reservations", json=body)
    assert response.status_code == 409 and "Borja no atiende" in response.json()["detail"]


def test_hr_edits_the_schedule(client):
    saved = client.put("/admin/rh/staff/paul/schedule", json={"days": {"5": [["10:00", "14:00"]]}})
    assert saved.status_code == 200 and saved.json()["schedule"] == {"days": {"5": [["10:00", "14:00"]]}}
    assert client.put("/admin/rh/staff/paul/schedule", json={"days": {}}).status_code == 422
    assert client.put("/admin/rh/staff/paul/schedule", json={"always": True}).json()["schedule"] == {"always": True}
