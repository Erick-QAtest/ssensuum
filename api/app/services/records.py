import json
import uuid
from datetime import date as date_type
from datetime import datetime, time, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..domain.customers import normalize_phone
from ..domain.marketing import clean_source
from ..domain.errors import NotFoundError, ValidationError
from ..domain.rules import TZ, parse_iso_datetime
from ..models import Customer, ServiceRecord
from ..repositories import catalog as catalog_repo
from ..repositories import customers as customers_repo
from ..repositories import records as records_repo
from ..schemas import ServiceRecordCreate
from .customers import set_source_if_missing

PAYMENT_METHODS = {"efectivo", "tarjeta", "transferencia", "mercadopago"}


def _clean_method(value: Optional[str], label: str) -> str:
    method = (value or "").strip().lower()
    if method not in PAYMENT_METHODS:
        raise ValidationError(f"{label}: elige efectivo, tarjeta, transferencia o Mercado Pago")
    return method


def _split_name(full_name: str) -> tuple[str, str]:
    first, _, last = full_name.partition(" ")
    return first, last.strip()


def _link_customer(db: Session, name: str, phone: str, source: Optional[str]) -> str:
    """Asocia el registro al cliente con ese teléfono; si no existe, lo da de alta."""
    customer = customers_repo.get_by_phone(db, phone)
    if not customer:
        first, last = _split_name(name)
        customer = Customer(id=str(uuid.uuid4()), phone=phone, first_name=first, last_name=last)
    elif not source or customer.acquisition_source:
        return customer.id
    set_source_if_missing(customer, source)
    return customers_repo.save(db, customer).id


def _apply(db: Session, record: ServiceRecord, payload: ServiceRecordCreate) -> ServiceRecord:
    name = " ".join(payload.customer_name.split())
    if not name:
        raise ValidationError("El nombre es obligatorio")
    phone = normalize_phone(payload.customer_phone)
    if not phone:
        raise ValidationError("El teléfono debe tener 10 dígitos")

    service = catalog_repo.get_service(db, payload.service_id)
    if not service:
        raise ValidationError("Servicio no encontrado")

    therapist_ids = list(dict.fromkeys(payload.therapist_ids))
    if not therapist_ids:
        raise ValidationError("Elige al menos un terapeuta")
    for therapist_id in therapist_ids:
        if not catalog_repo.therapist_exists(db, therapist_id):
            raise ValidationError("Terapeuta no encontrado")

    tips = []
    for tip in payload.tips:
        if tip.therapist_id not in therapist_ids:
            raise ValidationError("La propina debe ser para un terapeuta que atendió el servicio")
        if tip.amount > 0:
            tips.append({"therapistId": tip.therapist_id, "amount": tip.amount})
    payment_method = _clean_method(payload.payment_method, "Forma de pago")
    tip_method = _clean_method(payload.tip_method, "Forma de pago de la propina") if tips else None
    try:
        paid_at = parse_iso_datetime(payload.paid_at)
    except ValueError:
        raise ValidationError("La fecha de cobro no es válida")

    record.customer_name = name
    record.customer_phone = phone
    source = clean_source(payload.customer_source)
    if payload.customer_source and payload.customer_source.strip() and not source:
        raise ValidationError("Origen no reconocido")
    record.customer_id = _link_customer(db, name, phone, source)
    record.service_id = service.id
    record.service_name = service.name
    record.therapist_ids_json = json.dumps(therapist_ids)
    record.paid_at = paid_at
    record.amount = payload.amount
    record.payment_method = payment_method
    record.tips_json = json.dumps(tips)
    record.tip_method = tip_method
    record.notes = (payload.notes or "").strip() or None
    return records_repo.save(db, record)


def get_record(db: Session, record_id: str) -> ServiceRecord:
    record = records_repo.get(db, record_id)
    if not record:
        raise NotFoundError("Registro no encontrado")
    return record


def create_record(db: Session, payload: ServiceRecordCreate) -> ServiceRecord:
    return _apply(db, ServiceRecord(id=str(uuid.uuid4())), payload)


def update_record(db: Session, record_id: str, payload: ServiceRecordCreate) -> ServiceRecord:
    return _apply(db, get_record(db, record_id), payload)


def delete_record(db: Session, record_id: str) -> None:
    records_repo.delete(db, get_record(db, record_id))


def records_overview(db: Session, start_date: date_type, days: int) -> dict:
    start = datetime.combine(start_date, time.min, tzinfo=TZ)
    rows = records_repo.list_paid_between(db, start, start + timedelta(days=days))
    therapists = {row.id: row.name for row in catalog_repo.list_active_therapists(db)}

    by_method: dict[str, int] = {}
    tips_by_therapist: dict[str, dict] = {}
    for record in rows:
        by_method[record.payment_method] = by_method.get(record.payment_method, 0) + record.amount
        for tip in records_repo.tips(record):
            entry = tips_by_therapist.setdefault(tip["therapistId"], {
                "therapistId": tip["therapistId"],
                "therapistName": therapists.get(tip["therapistId"], tip["therapistId"]),
                "amount": 0,
                "count": 0,
            })
            entry["amount"] += tip["amount"]
            entry["count"] += 1

    return {
        "rows": rows,
        "therapists": therapists,
        "summary": {
            "count": len(rows),
            "amount": sum(record.amount for record in rows),
            "tips": sum(entry["amount"] for entry in tips_by_therapist.values()),
            "byPaymentMethod": by_method,
            "tipsByTherapist": sorted(tips_by_therapist.values(), key=lambda entry: -entry["amount"]),
        },
    }
