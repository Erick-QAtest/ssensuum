import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.domain.customer_profile import (
    Visit,
    clean_quiz_answers,
    funnel_stage,
    preferences,
    recurrence,
    recurrence_status,
)
from app.domain.rules import TZ
from app.main import app
from app.services import mercadopago

TODAY = date(2026, 10, 28)


def visit(days_ago: int, service: str = "Sueco", therapists: tuple = ("mazer",), hour: int = 18, amount: int = 1500, tip: int = 0) -> Visit:
    day = TODAY - timedelta(days=days_ago)
    return Visit(at=datetime(day.year, day.month, day.day, hour, tzinfo=TZ), service_name=service, therapist_ids=list(therapists), amount=amount, tip=tip)


# --- Reglas de dominio ---


def test_lead_without_visits_or_booking():
    assert funnel_stage([], has_upcoming=False, is_member=False, today=TODAY) == "lead"


def test_first_booking_before_first_visit():
    assert funnel_stage([], has_upcoming=True, is_member=False, today=TODAY) == "primera_reserva"


def test_first_visit_then_recurrent():
    assert funnel_stage([visit(5)], False, False, TODAY) == "primera_visita"
    assert funnel_stage([visit(40), visit(5)], False, False, TODAY) == "recurrente"


def test_two_services_same_day_are_one_visit():
    assert funnel_stage([visit(5), visit(5, service="Piedras")], False, False, TODAY) == "primera_visita"


def test_member_while_up_to_date():
    assert funnel_stage([visit(10)], False, True, TODAY) == "miembro"
    assert funnel_stage([], False, True, TODAY) == "miembro"


def test_overdue_is_at_risk_even_for_members():
    # Viene cada 14 días: a los 30 sin volver ya se tardó más de lo normal.
    visits = [visit(58), visit(44), visit(30)]
    assert funnel_stage(visits, False, False, TODAY) == "en_riesgo"
    assert funnel_stage(visits, False, True, TODAY) == "en_riesgo"


def test_upcoming_booking_rescues_overdue_customer():
    visits = [visit(58), visit(44), visit(30)]
    assert funnel_stage(visits, True, False, TODAY) == "recurrente"
    assert funnel_stage(visits, True, True, TODAY) == "miembro"


def test_inactive_after_long_absence():
    assert funnel_stage([visit(140)], False, False, TODAY) == "inactivo"
    # Una sola visita espera 45 días: a los 70 está en riesgo, aún no inactivo.
    assert funnel_stage([visit(70)], False, False, TODAY) == "en_riesgo"


@pytest.mark.parametrize(
    "since,gap,expected",
    [
        (10, 7, "al_corriente"),
        (20, 7, "al_corriente"),  # nunca en riesgo antes de 21 días
        (22, 7, "atrasado"),
        (89, 7, "atrasado"),  # nunca inactivo antes de 90 días
        (91, 7, "inactivo"),
        (60, 45, "al_corriente"),
        (68, 45, "atrasado"),
        (136, 45, "inactivo"),
    ],
)
def test_recurrence_status_thresholds(since, gap, expected):
    assert recurrence_status(since, gap) == expected


def test_recurrence_summary():
    summary = recurrence([visit(30), visit(60), visit(10)], TODAY)
    assert summary["visits"] == 3
    assert summary["firstVisit"] == (TODAY - timedelta(days=60)).isoformat()
    assert summary["lastVisit"] == (TODAY - timedelta(days=10)).isoformat()
    assert summary["averageGapDays"] == 25
    assert summary["daysSinceLastVisit"] == 10
    assert summary["nextExpectedVisit"] == (TODAY + timedelta(days=15)).isoformat()
    assert summary["status"] == "al_corriente"
    assert recurrence([], TODAY)["visits"] == 0


def test_preferences():
    visits = [
        visit(21, service="Sueco", therapists=("mazer",), hour=10, amount=1200, tip=100),
        visit(14, service="Deep tissue", therapists=("borja",), hour=18, amount=1500),
        visit(7, service="Sueco", therapists=("mazer", "borja"), hour=19, amount=1200, tip=200),
    ]
    prefs = preferences(visits)
    assert prefs["service"] == {"value": "Sueco", "count": 2}
    assert prefs["therapistId"]["count"] == 2
    assert prefs["weekday"] == {"value": "miércoles", "count": 3}
    assert prefs["timeWindow"] == {"value": "noche", "count": 2}
    assert prefs["totalSpent"] == 3900
    assert prefs["averageTicket"] == 1300
    assert prefs["totalTips"] == 300
    assert preferences([])["service"] is None


def test_clean_quiz_answers_keeps_only_known_questions():
    assert clean_quiz_answers({"presion": "firme", "zona": "espalda", "otra": "x", "trato": "<script>"}) == {"presion": "firme", "zona": "espalda"}
    assert clean_quiz_answers(None) == {}
    assert clean_quiz_answers("firme") == {}


# --- API ---


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def unique_phone() -> str:
    return "33" + str(uuid.uuid4().int)[:8]


def add_record(client, phone: str, days_ago: int) -> None:
    therapist = client.get("/therapists").json()[0]["id"]
    paid_at = (datetime.now(TZ) - timedelta(days=days_ago)).replace(hour=18, minute=0, second=0, microsecond=0)
    response = client.post("/admin/records", json={
        "customerName": "Luis Pérez",
        "customerPhone": phone,
        "serviceId": "massage-special",
        "therapistIds": [therapist],
        "paidAt": paid_at.isoformat(),
        "amount": 1500,
        "paymentMethod": "efectivo",
        "tips": [{"therapistId": therapist, "amount": 100}],
        "tipMethod": "efectivo",
    })
    assert response.status_code == 201, response.text


def find(client, phone: str) -> dict:
    return client.get("/customers", params={"q": phone}).json()[0]


def test_customer_list_profile_and_funnel(client):
    phone = unique_phone()
    lead = client.post("/customers", json={"phone": unique_phone(), "firstName": "Lía"}).json()
    add_record(client, phone, 40)
    add_record(client, phone, 12)

    row = find(client, phone)
    assert row["stage"] == "recurrente"
    assert row["visits"] == 2
    assert find(client, lead["phone"])["stage"] == "lead"

    recurrent = client.get("/customers", params={"stage": "recurrente", "limit": 200}).json()
    assert phone in [item["phone"] for item in recurrent]
    assert all(item["stage"] == "recurrente" for item in recurrent)
    assert client.get("/customers", params={"stage": "otra"}).status_code == 422

    profile = client.get(f"/customers/{row['id']}/profile").json()
    assert profile["stage"] == "recurrente"
    assert profile["recurrence"]["averageGapDays"] == 28
    assert profile["recurrence"]["status"] == "al_corriente"
    assert profile["preferences"]["totalTips"] == 200
    assert profile["preferences"]["therapistId"]["label"]
    assert len(profile["history"]) == 2

    funnel = client.get("/customers/funnel").json()
    counts = {entry["stage"]: entry["count"] for entry in funnel["stages"]}
    assert list(counts) == ["lead", "primera_reserva", "primera_visita", "recurrente", "miembro", "en_riesgo", "inactivo"]
    assert counts["recurrente"] >= 1 and counts["lead"] >= 1
    assert funnel["total"] == sum(counts.values())


def test_checkout_saves_quiz_answers(client, monkeypatch):
    monkeypatch.setattr(settings, "mp_access_token", "TEST-token")
    monkeypatch.setattr(mercadopago, "create_preference", lambda **kwargs: {"init_point": "x", "sandbox_init_point": "x"})
    phone = unique_phone()
    starts = (datetime.now(TZ) + timedelta(days=6)).date().isoformat()
    response = client.post("/checkout", json={
        "serviceId": "massage-special",
        "therapistIds": [],
        "startsAt": f"{starts}T12:00:00-06:00",
        "firstName": "Sofía",
        "phone": phone,
        "quiz": {"objetivo": "tension", "presion": "firme", "zona": "espalda", "trato": "directo", "horario": "tarde"},
    })
    assert response.status_code == 201, response.text

    customer = find(client, phone)
    profile = client.get(f"/customers/{customer['id']}/profile").json()
    assert profile["quiz"]["presion"] == "firme"
    assert profile["quizAt"]
    # El apartado en espera de pago cuenta como primera reserva mientras siga vigente.
    assert profile["stage"] == "primera_reserva"
