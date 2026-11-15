import json
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..domain.customers import normalize_email
from ..domain.errors import ConflictError, NotFoundError, ValidationError
from ..domain.marketing import SOURCES, clean_source
from ..domain.rules import TZ, ensure_tz
from ..models import Customer, ServiceRecord, VisitFeedback
from ..repositories import catalog as catalog_repo
from ..repositories import customers as customers_repo
from ..repositories import records as records_repo
from ..schemas import FeedbackCreate

# La home abre el pop up de calificación con este parámetro: /?calificar=<id del servicio registrado>.
FEEDBACK_PARAM = "calificar"


def _record(db: Session, record_id: str) -> ServiceRecord:
    record = db.get(ServiceRecord, record_id)
    if not record:
        raise NotFoundError("No encontramos esa visita")
    return record


def first_name(db: Session, record: ServiceRecord) -> str:
    customer = customers_repo.get(db, record.customer_id) if record.customer_id else None
    if customer and customer.first_name:
        return customer.first_name
    return (record.customer_name or "").split(" ")[0]


def feedback_url(record_id: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/?{FEEDBACK_PARAM}={record_id}"


def request_message(name: str, record_id: str) -> str:
    greeting = f"Hola {name}, gracias" if name else "Gracias"
    return (
        f"{greeting} por visitarnos en SSENSUUM. ¿Nos ayudas a mejorar? "
        f"Califica tu masaje en menos de un minuto: {feedback_url(record_id)}\n"
        "Y si algo no fue como esperabas, respóndenos aquí y lo resolvemos."
    )


def whatsapp_link(phone: Optional[str], text: str) -> Optional[str]:
    """Abre WhatsApp con el mensaje listo para un celular de México (10 dígitos); None si no hay teléfono."""
    if not phone:
        return None
    return f"https://wa.me/52{phone}?text={quote(text)}"


def feedback_request(db: Session, record: ServiceRecord) -> dict:
    text = request_message(first_name(db, record), record.id)
    return {"href": whatsapp_link(record.customer_phone, text), "text": text}


def feedback_by_record(db: Session, record_ids: list[str]) -> dict[str, VisitFeedback]:
    if not record_ids:
        return {}
    rows = db.scalars(select(VisitFeedback).where(VisitFeedback.record_id.in_(record_ids)))
    return {row.record_id: row for row in rows}


def _customer(db: Session, record: ServiceRecord) -> Optional[Customer]:
    return customers_repo.get(db, record.customer_id) if record.customer_id else None


def _therapists(db: Session, record: ServiceRecord) -> list[dict]:
    rows = []
    for therapist_id in records_repo.therapist_ids(record):
        therapist = catalog_repo.get_therapist(db, therapist_id)
        rows.append({"id": therapist_id, "name": therapist.name if therapist else therapist_id})
    return rows


def therapist_ratings(row: VisitFeedback) -> list[dict]:
    return json.loads(row.therapist_ratings_json or "[]")


def feedback_context(db: Session, record_id: str) -> dict:
    """Lo que el pop up necesita para saludar al cliente. Sin teléfono, montos ni datos que ya tenemos.

    De los datos del cliente solo se dice cuáles faltan, para preguntar solo esos.
    """
    record = _record(db, record_id)
    customer = _customer(db, record)
    therapists = _therapists(db, record)
    asks = {
        "email": bool(customer) and not customer.email,
        "birthday": bool(customer) and not customer.birthday,
        "source": bool(customer) and not customer.acquisition_source,
    }
    return {
        "visitId": record.id,
        "firstName": first_name(db, record),
        "serviceId": record.service_id,
        "serviceName": record.service_name,
        # Para calificar a cada masajista y para "reservar de nuevo" con el mismo.
        "therapistIds": [row["id"] for row in therapists],
        "therapistNames": [row["name"] for row in therapists],
        "visitedAt": ensure_tz(record.paid_at).isoformat(),
        "answered": db.get(VisitFeedback, record.id) is not None,
        "asks": asks,
        "sourceOptions": [{"id": key, "label": label} for key, label in SOURCES.items()] if asks["source"] else [],
    }


def _update_customer(customer: Optional[Customer], payload: FeedbackCreate) -> None:
    """Completa lo que falta del cliente y guarda su permiso de promociones por WhatsApp."""
    if not customer:
        return
    email = (payload.email or "").strip()
    if email and not customer.email:
        clean = normalize_email(email)
        if not clean:
            raise ValidationError("El correo no es válido")
        customer.email = clean
    if payload.birthday and not customer.birthday:
        if payload.birthday >= datetime.now(TZ).date():
            raise ValidationError("La fecha de cumpleaños no es válida")
        customer.birthday = payload.birthday.isoformat()
    if payload.source and not customer.acquisition_source:
        source = clean_source(payload.source)
        if source not in SOURCES:
            raise ValidationError("Origen no reconocido")
        customer.acquisition_source = source
    customer.whatsapp_opt_in = payload.whatsapp_opt_in
    customer.whatsapp_opt_in_at = datetime.now(TZ)


def submit_feedback(db: Session, record_id: str, payload: FeedbackCreate) -> VisitFeedback:
    record = _record(db, record_id)
    if db.get(VisitFeedback, record.id):
        raise ConflictError("Ya calificaste esta visita. ¡Gracias!")
    expected = records_repo.therapist_ids(record)
    given = {row.therapist_id: row.rating for row in payload.therapist_ratings}
    if set(given) != set(expected) or len(payload.therapist_ratings) != len(expected):
        raise ValidationError("Califica a cada masajista que te atendió")
    _update_customer(_customer(db, record), payload)
    row = VisitFeedback(
        record_id=record.id,
        massage_rating=payload.massage_rating,
        cleanliness_rating=payload.cleanliness_rating,
        therapist_ratings_json=json.dumps([{"therapistId": tid, "rating": given[tid]} for tid in expected]),
        comment=(payload.comment or "").strip() or None,
        created_at=datetime.now(TZ),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def mark_requested(db: Session, record_id: str) -> ServiceRecord:
    record = _record(db, record_id)
    if not record.feedback_requested_at:
        record.feedback_requested_at = datetime.now(TZ)
        db.commit()
        db.refresh(record)
    return record


def _average(values: list[int]) -> Optional[float]:
    return round(sum(values) / len(values), 1) if values else None


def ratings_summary(rows: list[VisitFeedback], therapist_names: dict[str, str]) -> dict:
    by_therapist: dict[str, list[int]] = {}
    for row in rows:
        for entry in therapist_ratings(row):
            by_therapist.setdefault(entry["therapistId"], []).append(entry["rating"])
    return {
        "count": len(rows),
        "massage": _average([row.massage_rating for row in rows]),
        "cleanliness": _average([row.cleanliness_rating for row in rows]),
        "byTherapist": sorted(
            (
                {"therapistId": tid, "therapistName": therapist_names.get(tid, tid), "average": _average(values), "count": len(values)}
                for tid, values in by_therapist.items()
            ),
            key=lambda entry: (-entry["average"], entry["therapistName"]),
        ),
    }
