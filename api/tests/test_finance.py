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
