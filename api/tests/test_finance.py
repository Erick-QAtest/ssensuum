import uuid
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.domain.finance import Entry, balance_sheet, cash_flow, income_statement, movement_entry
from app.domain.rules import TZ
from app.main import app
from app.models import TherapistPayout


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_statements_from_entries():
    day = date(2031, 3, 2)
    entries = [
        movement_entry(date(2031, 3, 1), "saldo_inicial", 10_000, "caja", None, None, "Caja inicial"),
        Entry(day, "Servicio", ("operacion", "Cobros por servicios")).debit("banco", 1500).credit("ingresos_servicios", 1500),
        Entry(day, "Honorarios", ("operacion", "Honorarios devengados")).debit("honorarios", 500).credit("honorarios_por_pagar", 500),
        movement_entry(day, "gasto", 300, "caja", "insumos", None, "Aceites"),
        movement_entry(day, "traspaso", 2000, "caja", None, "banco", "Depósito"),
        movement_entry(day, "activo", 4000, "banco", None, None, "Camilla"),
    ]
    pnl = income_statement(entries)
    assert (pnl["revenue"], pnl["costOfServices"], pnl["operatingExpenses"], pnl["netIncome"]) == (1500, 500, 300, 700)

    flow = cash_flow(entries[:1], entries[1:])
    assert (flow["opening"], flow["netChange"], flow["closing"]) == (10_000, -2800, 7200)
    assert {row["section"]: row["total"] for row in flow["sections"]} == {"operacion": 1200, "inversion": -4000}

    sheet = balance_sheet(entries)
    assert sheet["balanced"]
    assert (sheet["totalAssets"], sheet["totalLiabilities"], sheet["totalEquity"]) == (11_200, 500, 10_700)


def test_movement_validation(client):
    base = {"day": "2031-01-02", "kind": "gasto", "category": "renta", "description": "Renta", "amount": 100, "account": "banco"}
    assert client.post("/admin/finanzas/movements", json={**base, "category": "viajes"}).status_code == 422
    assert client.post("/admin/finanzas/movements", json={**base, "account": "cofre"}).status_code == 422
    assert client.post("/admin/finanzas/movements", json={**base, "amount": 0}).status_code == 422
    assert client.post("/admin/finanzas/movements", json={**base, "kind": "traspaso", "toAccount": "banco"}).status_code == 422
    created = client.post("/admin/finanzas/movements", json=base)
    assert created.status_code == 201
    assert created.json()["categoryLabel"] == "Renta"
    assert client.delete(f"/admin/finanzas/movements/{created.json()['id']}").status_code == 204
    assert client.delete(f"/admin/finanzas/movements/{created.json()['id']}").status_code == 404


def test_statements_follow_services_payouts_and_movements(client):
    a, b = [row["id"] for row in client.get("/therapists").json()][5:7]
    files = {"file": ("autorizacion.pdf", b"%PDF firmado", "application/pdf")}
    assert client.post("/admin/rh/documents", data={"category": "autorizacion_descuento", "therapistId": a}, files=files).status_code == 201

    def statements(start, end):
        response = client.get("/admin/finanzas/statements", params={"from": start, "to": end})
        assert response.status_code == 200
        return response.json()

    before = statements("2031-01-05", "2031-01-05")
    movement = {"kind": "saldo_inicial", "description": "Efectivo en caja", "amount": 10_000, "account": "caja", "day": "2031-01-05"}
    assert client.post("/admin/finanzas/movements", json=movement).status_code == 201

    record = client.post("/admin/records", json={
        "customerName": "Cliente Finanzas",
        "customerPhone": "35" + str(uuid.uuid4().int)[:8],
        "serviceId": "four-hands",
        "therapistIds": [a, b],
        "paidAt": "2031-01-06T10:00:00-06:00",
        "amount": 3000,
        "paymentMethod": "tarjeta",
        "tips": [{"therapistId": a, "amount": 200}],
        "tipMethod": "efectivo",
    }).json()
    rent = {"kind": "gasto", "category": "renta", "description": "Renta de enero", "amount": 5000, "account": "banco", "day": "2031-01-07"}
    assert client.post("/admin/finanzas/movements", json=rent).status_code == 201
    # Pago de honorarios y propina a "a" un día después del servicio.
    with SessionLocal() as db:
        db.add(TherapistPayout(record_id=record["id"], therapist_id=a, amount=600, paid_at=datetime(2031, 1, 7, 12, tzinfo=TZ)))
        db.commit()

    week = statements("2031-01-06", "2031-01-12")
    pnl = week["incomeStatement"]
    assert (pnl["revenue"], pnl["costOfServices"], pnl["grossProfit"]) == (3000, 1000, 2000)
    assert pnl["operatingExpenses"] == 5000
    assert pnl["otherIncomeTotal"] == 100  # limpieza compensada de "a"
    assert pnl["netIncome"] == -2900

    flow = week["cashFlow"]
    assert flow["netChange"] == 3000 + 200 - 5000 - 400 - 200
    assert flow["closing"] - flow["opening"] == flow["netChange"]
    accounts = {row["account"]: row for row in flow["accounts"]}
    assert accounts["caja"]["closing"] - accounts["caja"]["opening"] == 200

    sheet, previous = week["balanceSheet"], before["balanceSheet"]
    assert sheet["balanced"] and previous["balanced"]
    liabilities = {row["account"]: row["amount"] for row in sheet["liabilities"]}
    previous_liabilities = {row["account"]: row["amount"] for row in previous["liabilities"]}
    assert liabilities.get("honorarios_por_pagar", 0) - previous_liabilities.get("honorarios_por_pagar", 0) == 500  # falta pagar a "b"
    assert sheet["totalAssets"] - previous["totalAssets"] == 10_000 - 2400

    assert client.get("/admin/finanzas/statements", params={"from": "2031-01-12", "to": "2031-01-06"}).status_code == 422
    excel = client.get("/admin/finanzas/statements/export", params={"from": "2031-01-06", "to": "2031-01-12"})
    assert excel.status_code == 200
    assert excel.headers["content-type"].startswith("application/vnd.openxmlformats")


def test_dashboard_series_and_breakdowns(client):
    record = {
        "customerName": "Cliente Tablero",
        "customerPhone": "36" + str(uuid.uuid4().int)[:8],
        "serviceId": "massage-special",
        "therapistIds": [client.get("/therapists").json()[7]["id"]],
        "paidAt": "2032-05-04T10:00:00-06:00",
        "amount": 1500,
        "paymentMethod": "mercadopago",
        "tips": [],
    }
    assert client.post("/admin/records", json=record).status_code == 201
    expense = {"kind": "gasto", "category": "publicidad", "description": "Anuncios", "amount": 700, "account": "banco", "day": "2032-05-05"}
    assert client.post("/admin/finanzas/movements", json=expense).status_code == 201

    week = client.get("/admin/finanzas/dashboard", params={"from": "2032-05-03", "to": "2032-05-09"}).json()
    assert week["granularity"] == "day" and len(week["series"]) == 7
    days = {row["start"]: row for row in week["series"]}
    assert days["2032-05-04"]["revenue"] == 1500 and days["2032-05-04"]["outflows"] == 500
    assert days["2032-05-05"]["operatingExpenses"] == 700
    assert days["2032-05-05"]["cash"] - days["2032-05-03"]["cash"] == 1500 - 700
    assert week["kpis"]["revenue"] == 1500 and week["kpis"]["netIncome"] == 300
    assert (week["previousFrom"], week["previousTo"]) == ("2032-04-26", "2032-05-02")
    assert {row["label"] for row in week["costBreakdown"]} == {"Honorarios de masajistas", "Publicidad y marketing"}
    assert week["revenueByService"][0]["count"] == 1
    assert week["revenueByAccount"] == [{"label": "Mercado Pago", "amount": 1500, "count": 1}]

    year = client.get("/admin/finanzas/dashboard", params={"from": "2032-01-01", "to": "2032-12-31"}).json()
    assert year["granularity"] == "month" and len(year["series"]) == 12
    quarter = client.get("/admin/finanzas/dashboard", params={"from": "2032-04-01", "to": "2032-06-30"}).json()
    assert quarter["granularity"] == "week" and quarter["series"][0]["start"] == "2032-04-01"


def test_monthly_dates_use_last_day_in_short_months():
    from app.domain.finance import monthly_dates

    days = monthly_dates(31, "2033-01", None, date(2033, 1, 1), date(2033, 4, 30))
    assert days == [date(2033, 1, 31), date(2033, 2, 28), date(2033, 3, 31), date(2033, 4, 30)]
    assert monthly_dates(5, "2033-02", "2033-03", date(2033, 1, 1), date(2033, 12, 31)) == [date(2033, 2, 5), date(2033, 3, 5)]


def test_recurring_expense_posts_every_month(client):
    rent = {"description": "Renta del local", "category": "renta", "amount": 5000, "account": "caja", "dayOfMonth": 5, "startMonth": "2034-02"}
    assert client.post("/admin/finanzas/recurring", json={**rent, "category": "viajes"}).status_code == 422
    assert client.post("/admin/finanzas/recurring", json={**rent, "startMonth": "2034-13"}).status_code == 422
    created = client.post("/admin/finanzas/recurring", json=rent)
    assert created.status_code == 201
    recurring = created.json()
    assert recurring["accountLabel"] == "Caja (efectivo)" and recurring["endMonth"] is None

    def expenses(start, end):
        return client.get("/admin/finanzas/statements", params={"from": start, "to": end}).json()["incomeStatement"]["operatingExpenses"]

    assert expenses("2034-01-01", "2034-01-31") == 0
    assert expenses("2034-02-01", "2034-02-04") == 0
    assert expenses("2034-02-05", "2034-02-05") == 5000
    assert expenses("2034-02-01", "2034-04-30") == 15_000

    listed = client.get("/admin/finanzas/movements", params={"from": "2034-03-01", "to": "2034-03-31"}).json()
    assert [(row["day"], row["kindLabel"], row["amount"]) for row in listed] == [("2034-03-05", "Gasto fijo", 5000)]

    ended = client.post(f"/admin/finanzas/recurring/{recurring['id']}/end", params={"lastMonth": "2034-03"})
    assert ended.json()["endMonth"] == "2034-03"
    assert expenses("2034-02-01", "2034-06-30") == 10_000  # febrero y marzo se conservan; abril en adelante ya no
    assert client.post("/admin/finanzas/recurring/nada/end", params={"lastMonth": "2034-03"}).status_code == 404
