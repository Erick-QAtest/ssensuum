import io
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.domain.customer_import import map_columns, parse_birthday
from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def unique_phone() -> str:
    return "33" + str(uuid.uuid4().int)[:8]


def xlsx(rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def upload(client, content: bytes, name: str = "clientes.xlsx", dry_run=None):
    params = {} if dry_run is None else {"dryRun": str(dry_run).lower()}
    return client.post("/customers/import", params=params, files={"file": (name, content)})


def test_map_columns_accepts_common_headers():
    assert map_columns(["Nombre", "Apellidos", "Teléfono celular", "Correo electrónico", "Fecha de nacimiento", "Notas"]) == {
        "first_name": 0,
        "last_name": 1,
        "phone": 2,
        "email": 3,
        "birthday": 4,
        "notes": 5,
    }


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1990-05-17", "1990-05-17"),
        ("17/05/1990", "1990-05-17"),
        ("17-05-1990", "1990-05-17"),
        (datetime(1990, 5, 17), "1990-05-17"),
        ("mayo", None),
        ("17/05/2999", None),
        ("01/01/1800", None),
    ],
)
def test_parse_birthday(raw, expected):
    parsed = parse_birthday(raw)
    assert (parsed.isoformat() if parsed else None) == expected


def test_dry_run_is_default_and_does_not_write(client):
    phone = unique_phone()
    content = xlsx([["Nombre", "Celular"], ["Ana", phone]])

    response = upload(client, content)
    assert response.status_code == 200
    body = response.json()
    assert body["dryRun"] is True
    assert body["valid"] == 1
    assert body["created"] == 0
    assert body["preview"][0]["phone"] == phone
    assert client.get("/customers", params={"q": phone}).json() == []


def test_import_xlsx_reports_every_kind_of_row(client):
    existing = unique_phone()
    client.post("/customers", json={"phone": existing, "firstName": "Ya registrada"})
    good, numeric, warned = unique_phone(), unique_phone(), unique_phone()
    content = xlsx(
        [
            ["Nombre", "Apellidos", "Teléfono", "Correo", "Cumpleaños"],
            ["Ana", "López", f"+52 {good}", "Ana@Example.com", datetime(1990, 5, 17)],
            ["Luis", "Ruiz", float(numeric), None, "03/11/1985"],
            [None, None, None, None, None],
            ["Eva", "", warned, "sin-arroba", "algún día"],
            ["Repetida", "", good, None, None],
            ["Existente", "", existing, None, None],
            ["Sin teléfono", "", "", None, None],
            ["", "", "12345", None, None],
        ]
    )

    body = upload(client, content, dry_run=False).json()
    assert body["columns"] == {"firstName": "Nombre", "lastName": "Apellidos", "phone": "Teléfono", "email": "Correo", "birthday": "Cumpleaños"}
    assert (body["totalRows"], body["valid"], body["created"]) == (7, 3, 3)
    assert (body["duplicates"], body["invalid"], body["warnings"]) == (2, 2, 1)
    assert body["issuesTruncated"] is False

    issues = {issue["row"]: issue for issue in body["issues"]}
    assert issues[5]["status"] == "warning" and len(issues[5]["messages"]) == 2
    assert issues[6]["messages"] == ["Teléfono repetido en el archivo"]
    assert issues[7]["messages"] == ["Ya existe un cliente con ese teléfono"]
    assert issues[8]["messages"] == ["Teléfono vacío"]
    assert issues[9]["messages"] == ["El teléfono debe tener 10 dígitos", "Falta el nombre"]

    ana = client.get("/customers", params={"q": good}).json()[0]
    assert (ana["firstName"], ana["lastName"], ana["email"], ana["birthday"]) == ("Ana", "López", "ana@example.com", "1990-05-17")
    luis = client.get("/customers", params={"q": numeric}).json()[0]
    assert luis["birthday"] == "1985-11-03"
    eva = client.get("/customers", params={"q": warned}).json()[0]
    assert (eva["email"], eva["birthday"]) == (None, None)

    again = upload(client, content, dry_run=False).json()
    assert (again["created"], again["duplicates"]) == (0, 5)


def test_import_csv_with_semicolons_and_latin1(client):
    phone = unique_phone()
    content = f"Cliente;WhatsApp;Email\nJosé Peña;{phone};jose@example.com\n".encode("latin-1")
    body = upload(client, content, name="clientes.csv", dry_run=False).json()
    assert body["created"] == 1
    assert client.get("/customers", params={"q": phone}).json()[0]["firstName"] == "José Peña"


@pytest.mark.parametrize(
    "name,content,detail",
    [
        ("clientes.xls", b"x", "Formato no soportado. Sube un archivo .xlsx o .csv"),
        ("clientes.xlsx", b"esto no es excel", "No se pudo leer el archivo de Excel"),
        ("clientes.csv", b"\n\n", "El archivo está vacío"),
        ("clientes.csv", b"Nombre,Correo\nAna,a@b.co\n", "No se encontró una columna de teléfono (por ejemplo: Teléfono, Celular, WhatsApp)"),
        ("clientes.csv", b"Celular,Correo\n3310000001,a@b.co\n", "No se encontró una columna de nombre (por ejemplo: Nombre, Cliente)"),
        ("clientes.csv", b"x" * (5 * 1024 * 1024 + 1), "El archivo supera el límite de 5 MB"),
    ],
)
def test_import_rejects_bad_files(client, name, content, detail):
    response = upload(client, content, name=name)
    assert response.status_code == 422
    assert response.json()["detail"] == detail


def test_import_requires_file(client):
    assert client.post("/customers/import").status_code == 422


def test_import_reads_membership_expiry_and_notes(client):
    phone = unique_phone()
    content = xlsx([
        ["Nombre", "Apellido", "Teléfono", "Membresía vence", "Notas"],
        ["José", "Ceballos", phone, datetime(2026, 12, 12), "Cancelado"],
    ])
    body = upload(client, content, dry_run=False).json()
    assert body["created"] == 1
    assert body["columns"]["membershipExpiresOn"] == "Membresía vence"

    customer = client.get("/customers", params={"q": phone}).json()[0]
    assert customer["membershipExpiresOn"] == "2026-12-12"
    assert customer["notes"] == "Cancelado"
