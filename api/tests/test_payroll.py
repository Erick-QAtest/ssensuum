import io
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.domain.payroll import settle, week_start
from app.domain.rules import TZ
from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_week_runs_monday_to_sunday():
    assert week_start(date(2026, 10, 19)) == date(2026, 10, 19)  # lunes
    assert week_start(date(2026, 10, 25)) == date(2026, 10, 19)  # domingo


def test_cleaning_comes_off_the_first_service_when_authorized():
    result = settle([{"tip": 0}, {"tip": 250}, {"tip": 0}], compensate_cleaning=True)
    assert [line["pay"] for line in result["lines"]] == [400, 750, 500]
    assert (result["gross"], result["cleaning"], result["cleaningToCollect"], result["total"]) == (1500, 100, 0, 1650)


def test_cleaning_is_collected_apart_without_authorization():
    result = settle([{"tip": 0}, {"tip": 0}], compensate_cleaning=False)
    assert [line["pay"] for line in result["lines"]] == [500, 500]
    assert (result["cleaning"], result["cleaningToCollect"], result["total"]) == (0, 100, 1000)


def test_no_services_no_cleaning():
    result = settle([], compensate_cleaning=True)
    assert (result["cleaning"], result["cleaningToCollect"], result["total"]) == (0, 0, 0)


def record(client, therapist_ids, paid_at, tips=(), service_id="massage-special"):
    body = {
        "customerName": "Cliente Prueba",
        "customerPhone": "34" + str(uuid.uuid4().int)[:8],
        "serviceId": service_id,
        "therapistIds": therapist_ids,
        "paidAt": paid_at,
        "amount": 1500,
        "paymentMethod": "efectivo",
        "tips": [{"therapistId": tid, "amount": amount} for tid, amount in tips],
        "tipMethod": "efectivo",
    }
    response = client.post("/admin/records", json=body)
    assert response.status_code == 201
    return response.json()


def authorize_discount(client, therapist_id):
    files = {"file": ("autorizacion.pdf", b"%PDF firmado", "application/pdf")}
    data = {"category": "autorizacion_descuento", "therapistId": therapist_id}
    assert client.post("/admin/rh/documents", data=data, files=files).status_code == 201


def test_weekly_payroll_per_therapist(client):
    a, b = [row["id"] for row in client.get("/therapists").json()][2:4]
    authorize_discount(client, a)
    # Semana del lunes 2 al domingo 8 de febrero de 2026; el lunes 9 ya es otra semana.
    second = record(client, [a], "2026-02-04T12:00:00-06:00", tips=[(a, 200)])
    first = record(client, [a, b], "2026-02-02T09:30:00-06:00", service_id="four-hands")
    record(client, [b], "2026-02-08T23:30:00-06:00")
    record(client, [a], "2026-02-09T10:00:00-06:00")

    payroll = client.get("/admin/rh/payroll", params={"week": "2026-02-05"}).json()
    assert (payroll["weekStart"], payroll["weekEnd"]) == ("2026-02-02", "2026-02-08")
    rows = {row["therapistId"]: row for row in payroll["staff"]}

    # a firmó la autorización: la limpieza sale de su primer servicio y la propina va con el servicio.
    assert [line["recordId"] for line in rows[a]["lines"]] == [first["id"], second["id"]]
    assert [line["pay"] for line in rows[a]["lines"]] == [400, 700]
    assert (rows[a]["cleaning"], rows[a]["cleaningToCollect"], rows[a]["total"]) == (100, 0, 1100)
    assert rows[a]["lines"][0]["dueAt"].startswith("2026-02-04T09:30")

    # b no la firmó: cobra completo y la limpieza queda por cobrar aparte.
    assert [line["pay"] for line in rows[b]["lines"]] == [500, 500]
    assert (rows[b]["cleaning"], rows[b]["cleaningToCollect"], rows[b]["total"]) == (0, 100, 1000)

    excel = client.get("/admin/rh/payroll/export", params={"week": "2026-02-05"})
    assert excel.status_code == 200
    book = load_workbook(io.BytesIO(excel.content))
    assert book["Liquidación"].cell(row=book["Liquidación"].max_row, column=7).value == payroll["totals"]["total"]
    assert book["Detalle"].max_row == 5


def test_payouts_within_48_hours(client, monkeypatch):
    # Los pendientes cuentan desde el inicio de los contratos; aquí se adelanta para no depender del día de hoy.
    monkeypatch.setattr("app.services.payroll.PAYOUTS_START", date.today() - timedelta(days=30))
    a = [row["id"] for row in client.get("/therapists").json()][4]
    now = datetime.now(TZ)
    late = record(client, [a], (now - timedelta(hours=50)).isoformat(), tips=[(a, 100)])
    recent = record(client, [a], (now - timedelta(hours=1)).isoformat())

    pending = {line["recordId"]: line for line in client.get("/admin/rh/payroll/pending").json()}
    assert pending[late["id"]]["overdue"] is True
    assert pending[recent["id"]]["overdue"] is False
    assert pending[late["id"]]["pay"] == pending[late["id"]]["gross"] - pending[late["id"]]["cleaning"] + 100

    body = {"recordId": late["id"], "therapistId": a, "paid": True}
    assert client.put("/admin/rh/payroll/payouts", json=body).status_code == 204
    assert client.put("/admin/rh/payroll/payouts", json=body).status_code == 204
    assert late["id"] not in [line["recordId"] for line in client.get("/admin/rh/payroll/pending").json()]

    week = client.get("/admin/rh/payroll", params={"week": late["paidAt"][:10]}).json()
    line = next(line for row in week["staff"] for line in row["lines"] if line["recordId"] == late["id"])
    assert line["payoutAt"] is not None

    assert client.put("/admin/rh/payroll/payouts", json={**body, "paid": False}).status_code == 204
    assert late["id"] in [line["recordId"] for line in client.get("/admin/rh/payroll/pending").json()]
    assert client.put("/admin/rh/payroll/payouts", json={**body, "therapistId": "nadie"}).status_code == 422
    assert client.put("/admin/rh/payroll/payouts", json={**body, "recordId": "nada"}).status_code == 404
