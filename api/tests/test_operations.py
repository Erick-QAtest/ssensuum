from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain import operations as ops
from app.main import app
from app.services import operations as ops_service

SUNDAY_A = date(2026, 11, 15)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def upload(client, task_key, zone_id, point_id=None, day=SUNDAY_A):
    data = {"taskKey": task_key, "zoneId": zone_id, "pointId": point_id or ""}
    response = client.post(f"/admin/ops/days/{day}/evidence", data=data, files={"photo": ("e.png", PNG, "image/png")})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(ops_service, "today", lambda: SUNDAY_A)
    with TestClient(app) as test_client:
        yield test_client


def test_cycle_is_balanced():
    week_a = [SUNDAY_A - timedelta(days=6 - offset) for offset in range(7)]
    totals = [sum(task.minutes for task in ops.tasks_for(day, day.weekday() in (0, 2, 4, 6))) for day in week_a]
    assert totals == [370, 375, 375, 360, 371, 380, 378]
    sunday_b = SUNDAY_A + timedelta(days=7)
    assert sum(task.minutes for task in ops.tasks_for(sunday_b, True)) == 348
    assert ops.cycle_week(sunday_b) == "B"
    assert "compra-urgente" not in [task.key for task in ops.tasks_for(sunday_b, True)]
    assert "compra-urgente" in [task.key for task in ops.tasks_for(sunday_b, True, True)]


def test_supply_is_ordered_before_it_runs_out():
    thursday = date(2026, 11, 12)  # el siguiente pedido es el miércoles 18 y llega el viernes 20
    # 1 rack por semana: con 3 racks alcanza hasta después del pedido de la otra semana.
    assert ops.supply_plan(3, 1 / 7, 2, 3, 1, thursday)["status"] == "bien"
    # Con 2 racks, al llegar el pedido del 25 + 2 días quedaría por debajo del margen: se pide el miércoles 18.
    plan = ops.supply_plan(2, 1 / 7, 2, 3, 1, thursday)
    assert plan["status"] == "pedir" and plan["orderOn"] == "2026-11-18" and plan["quantity"] >= 1
    # Con medio rack ni el pedido del 18 llega a tiempo: compra hoy.
    assert ops.supply_plan(0.5, 1 / 7, 2, 3, 1, thursday)["status"] == "urgente"
    assert ops.supply_plan(None, 1 / 7, 2, 3, 1, thursday)["status"] == "sin_contar"
    # El consumo se corrige con lo observado.
    assert ops.smoothed_use(1.0, 2.0) == 1.5


def test_day_closes_only_when_everything_is_marked(client):
    zones = {zone["id"]: zone for zone in client.get("/admin/ops/zones").json()}
    assert {"bano-1", "cocina", "sala"} <= set(zones)

    assert client.put("/admin/ops/zones/bano-1/photo", files={"photo": ("b.png", PNG, "image/png")}).status_code == 200
    assert client.put("/admin/ops/zones/bano-1/photo", files={"photo": ("b.txt", b"hola", "text/plain")}).status_code == 422
    client.post("/admin/ops/zones/bano-1/points", json={"x": 0.5, "y": 0.4, "kind": "rellenar", "label": "Jabón"})
    zones = client.post("/admin/ops/zones/bano-1/points", json={"x": 0.3, "y": 0.6, "kind": "limpiar", "label": "Lavabo"}).json()
    bano = next(zone for zone in zones if zone["id"] == "bano-1")
    assert bano["photoUrl"].startswith("/admin/ops/zones/bano-1/photo?v=")
    assert client.get("/admin/ops/zones/bano-1/photo").content == PNG
    soap, sink = sorted(bano["points"], key=lambda point: point["label"])

    day = client.get(f"/admin/ops/days/{SUNDAY_A}").json()
    keys = [task["key"] for task in day["tasks"]]
    assert "aseo-banos" in keys and "lavanderia" in keys and "aseo-cocina" not in keys
    assert day["canClose"] is False
    deep = next(task for task in day["tasks"] if task["key"] == "aseo-banos")
    assert [point["label"] for zone in deep["zones"] for point in zone["points"]] == ["Jabón", "Lavabo"]
    assert deep["zonesWithoutPoints"] == ["Baño 2", "Baño 3"]
    # La ronda diaria solo revisa rellenos y bolsas.
    round_task = next(task for task in day["tasks"] if task["key"] == "ronda-tarde")
    assert [point["label"] for zone in round_task["zones"] for point in zone["points"]] == ["Jabón"]

    url = f"/admin/ops/days/{SUNDAY_A}/checks"
    assert client.post(url, json={"itemKey": "aseo-cocina", "status": "hecho"}).status_code == 422
    assert client.post(url, json={"itemKey": f"aseo-banos@{soap['id']}", "status": "no_se_pudo"}).status_code == 422
    client.post(url, json={"itemKey": f"aseo-banos@{soap['id']}", "status": "no_se_pudo", "reason": "Sin jabón en bodega"})
    day = client.post(url, json={"itemKey": f"aseo-banos@{sink['id']}", "status": "hecho"}).json()
    assert next(task for task in day["tasks"] if task["key"] == "aseo-banos")["status"] == "pendiente"
    day = client.post(url, json={"itemKey": "aseo-banos", "status": "hecho"}).json()
    deep = next(task for task in day["tasks"] if task["key"] == "aseo-banos")
    # Todo marcado, pero falta la foto del después del Baño 1 (la única zona con foto de referencia).
    assert deep["status"] == "pendiente" and [row["zoneId"] for row in deep["evidence"]] == ["bano-1"]
    day = upload(client, "aseo-banos", "bano-1")
    assert next(task for task in day["tasks"] if task["key"] == "aseo-banos")["status"] == "hecho"

    assert client.post(f"/admin/ops/days/{SUNDAY_A}/close").status_code == 422
    for task in day["tasks"]:
        if task["status"] != "pendiente":
            continue
        for zone in task["zones"]:
            for point in zone["points"]:
                client.post(url, json={"itemKey": f"{task['key']}@{point['id']}", "status": "hecho"})
        for row in task["evidence"]:
            upload(client, task["key"], row["zoneId"], row["pointId"])
        day = client.post(url, json={"itemKey": task["key"], "status": "hecho"}).json()
    assert day["pending"] == 0 and day["canClose"] is True

    closed = client.post(f"/admin/ops/days/{SUNDAY_A}/close").json()
    assert closed["closed"] is True
    assert client.post(url, json={"itemKey": "abrir", "status": "hecho"}).status_code == 409
    assert client.post(f"/admin/ops/days/{SUNDAY_A}/reopen").json()["closed"] is False

    tomorrow = SUNDAY_A + timedelta(days=1)
    assert client.post(f"/admin/ops/days/{tomorrow}/checks", json={"itemKey": "abrir", "status": "hecho"}).status_code == 422
    assert client.get(f"/admin/ops/days/{tomorrow}").json()["canClose"] is False


def test_counts_learn_consumption_and_drive_the_order(client, monkeypatch):
    supplies = {row["id"]: row for row in client.get("/admin/ops/supplies").json()}
    assert supplies["agua"]["status"] == "sin_contar"
    assert client.post("/admin/ops/supplies/agua/receive", json={"quantity": 1}).status_code == 422

    # Domingo 15: hay 2 racks. Miércoles 18 quedan 1 (se gastó 1 en 3 días, no 3/7 como se estimaba).
    client.post("/admin/ops/supplies/count", json={"counts": {"agua": 2}})
    monkeypatch.setattr(ops_service, "today", lambda: date(2026, 11, 18))
    rows = {row["id"]: row for row in client.post("/admin/ops/supplies/count", json={"counts": {"agua": 1}}).json()}
    assert rows["agua"]["dailyUse"] == pytest.approx(0.5 * (1 / 7) + 0.5 * (1 / 3), abs=1e-3)
    assert rows["agua"]["status"] == "urgente"

    day = client.get("/admin/ops/days/2026-11-18").json()
    order = next(task for task in day["tasks"] if task["key"] == "pedido")
    urgent = next(task for task in day["tasks"] if task["key"] == "compra-urgente")
    assert "Agua embotellada para clientes" in [row["name"] for row in order["supplies"]]
    assert [row["name"] for row in urgent["supplies"]] == ["Agua embotellada para clientes"]

    rows = {row["id"]: row for row in client.post("/admin/ops/supplies/agua/receive", json={"quantity": 3}).json()}
    assert rows["agua"]["estimate"] == 4 and rows["agua"]["status"] != "urgente"


def test_evidence_is_required_and_reviewed(client):
    day = client.get(f"/admin/ops/days/{SUNDAY_A}").json()
    rounds = next(task for task in day["tasks"] if task["key"] == "ronda-tarde")
    # La ronda pide la foto de un solo punto, el mismo durante todo el día.
    assert len(rounds["evidence"]) == 1 and rounds["evidence"][0]["pointId"]
    again = client.get(f"/admin/ops/days/{SUNDAY_A}").json()
    assert next(task for task in again["tasks"] if task["key"] == "ronda-tarde")["evidence"] == rounds["evidence"]

    target = rounds["evidence"][0]
    bad = client.post(f"/admin/ops/days/{SUNDAY_A}/evidence", data={"taskKey": "ronda-tarde", "zoneId": "sala"}, files={"photo": ("e.png", PNG, "image/png")})
    assert bad.status_code == 422
    future = SUNDAY_A + timedelta(days=1)
    assert client.post(f"/admin/ops/days/{future}/evidence", data={"taskKey": "abrir", "zoneId": "sala"}, files={"photo": ("e.png", PNG, "image/png")}).status_code == 422

    day = upload(client, "ronda-tarde", target["zoneId"], target["pointId"])
    photo = next(task for task in day["tasks"] if task["key"] == "ronda-tarde")["evidence"][0]["photo"]
    assert photo["review"] == "pendiente" and client.get(photo["url"]).content == PNG
    assert photo["referenceUrl"].startswith(f"/admin/ops/zones/{target['zoneId']}/photo")

    listed = client.get("/admin/ops/evidence", params={"from": SUNDAY_A.isoformat(), "to": SUNDAY_A.isoformat()}).json()
    assert photo["id"] in [row["id"] for row in listed]
    assert client.post(f"/admin/ops/evidence/{photo['id']}/review", json={"review": "repetir"}).status_code == 422
    reviewed = client.post(f"/admin/ops/evidence/{photo['id']}/review", json={"review": "repetir", "note": "El jabón quedó vacío"}).json()
    assert reviewed["review"] == "repetir" and reviewed["taskLabel"] == "Ronda de baños"
    day = client.get(f"/admin/ops/days/{SUNDAY_A}").json()
    task = next(task for task in day["tasks"] if task["key"] == "ronda-tarde")
    assert task["evidence"][0]["photo"]["reviewNote"] == "El jabón quedó vacío" and task["status"] == "pendiente"
