import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..domain.customer_import import cell_text, map_columns, parse_birthday, parse_date, read_table
from ..domain.customers import normalize_email, normalize_phone
from ..domain.errors import ConflictError, ValidationError
from ..models import Customer
from ..repositories import customers as customers_repo
from ..serializers import customer_payload

MAX_ISSUES = 500
PREVIEW_ROWS = 10
FIELD_LABELS = {
    "phone": "phone",
    "first_name": "firstName",
    "last_name": "lastName",
    "email": "email",
    "birthday": "birthday",
    "membership_expires_on": "membershipExpiresOn",
    "notes": "notes",
}


def import_customers(db: Session, filename: str, content: bytes, dry_run: bool) -> dict:
    headers, rows = read_table(filename, content)
    columns = map_columns(headers)
    if "phone" not in columns:
        raise ValidationError("No se encontró una columna de teléfono (por ejemplo: Teléfono, Celular, WhatsApp)")
    if "first_name" not in columns:
        raise ValidationError("No se encontró una columna de nombre (por ejemplo: Nombre, Cliente)")

    def value(cells: list[Any], field: str) -> Any:
        index = columns.get(field)
        return cells[index] if index is not None and index < len(cells) else None

    existing = customers_repo.existing_phones(db)
    seen: set[str] = set()
    customers: list[Customer] = []
    issues: list[dict] = []
    counts = {"duplicate": 0, "invalid": 0, "warning": 0}

    def report(row: int, status: str, phone: str, name: str, messages: list[str]) -> None:
        counts[status] += 1
        if len(issues) < MAX_ISSUES:
            issues.append({"row": row, "status": status, "phone": phone, "name": name, "messages": messages})

    for row_number, cells in rows:
        raw_phone = cell_text(value(cells, "phone"))
        first_name = cell_text(value(cells, "first_name"))
        last_name = cell_text(value(cells, "last_name"))
        name = f"{first_name} {last_name}".strip()

        phone = normalize_phone(raw_phone)
        errors = []
        if not phone:
            errors.append("Teléfono vacío" if not raw_phone else "El teléfono debe tener 10 dígitos")
        if not first_name:
            errors.append("Falta el nombre")
        if errors:
            report(row_number, "invalid", raw_phone, name, errors)
            continue

        if phone in existing:
            report(row_number, "duplicate", phone, name, ["Ya existe un cliente con ese teléfono"])
            continue
        if phone in seen:
            report(row_number, "duplicate", phone, name, ["Teléfono repetido en el archivo"])
            continue
        seen.add(phone)

        warnings = []
        email = None
        raw_email = cell_text(value(cells, "email"))
        if raw_email:
            email = normalize_email(raw_email)
            if not email:
                warnings.append(f"Correo no válido, se omite: {raw_email}")
        birthday = None
        raw_birthday = value(cells, "birthday")
        if cell_text(raw_birthday):
            birthday = parse_birthday(raw_birthday)
            if not birthday:
                warnings.append(f"Cumpleaños no reconocido, se omite: {cell_text(raw_birthday)}")
        membership = None
        raw_membership = value(cells, "membership_expires_on")
        if cell_text(raw_membership):
            membership = parse_date(raw_membership)
            if not membership:
                warnings.append(f"Vencimiento de membresía no reconocido, se omite: {cell_text(raw_membership)}")
        if warnings:
            report(row_number, "warning", phone, name, warnings)

        customers.append(
            Customer(
                id=str(uuid.uuid4()),
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                email=email,
                birthday=birthday.isoformat() if birthday else None,
                membership_expires_on=membership.isoformat() if membership else None,
                notes=cell_text(value(cells, "notes")) or None,
            )
        )

    preview = [
        {
            "phone": c.phone,
            "firstName": c.first_name,
            "lastName": c.last_name,
            "email": c.email,
            "birthday": c.birthday,
            "membershipExpiresOn": c.membership_expires_on,
            "notes": c.notes,
        }
        for c in customers[:PREVIEW_ROWS]
    ]
    created = 0
    if not dry_run and customers:
        try:
            customers_repo.save_all(db, customers)
        except IntegrityError:
            db.rollback()
            raise ConflictError("Otro proceso registró clientes con estos teléfonos. Revisa el archivo de nuevo")
        created = len(customers)
        preview = [customer_payload(c) for c in customers[:PREVIEW_ROWS]]

    return {
        "dryRun": dry_run,
        "fileName": filename,
        "columns": {FIELD_LABELS[field]: cell_text(headers[index]) for field, index in columns.items()},
        "totalRows": len(rows),
        "valid": len(customers),
        "created": created,
        "duplicates": counts["duplicate"],
        "invalid": counts["invalid"],
        "warnings": counts["warning"],
        "issues": issues,
        "issuesTruncated": sum(counts.values()) > len(issues),
        "preview": preview,
    }
