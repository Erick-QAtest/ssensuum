from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..domain import notices
from ..domain.errors import ConflictError, NotFoundError
from ..domain.rules import TZ, ensure_tz
from ..models import ServiceRecord, VisitFeedback
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
    """SMS corto, sin á/í/ó/ú para que quepa en el alfabeto básico (como los recordatorios)."""
    greeting = f"Hola {name}, gracias" if name else "Gracias"
    return notices.sms_text(f"SSENSUUM: {greeting} por tu visita. Califica tu masaje en 1 minuto: {feedback_url(record_id)}")


def feedback_request(db: Session, record: ServiceRecord) -> dict:
    text = request_message(first_name(db, record), record.id)
    return {"href": notices.sms_link(record.customer_phone, text), "text": text}


def feedback_by_record(db: Session, record_ids: list[str]) -> dict[str, VisitFeedback]:
    if not record_ids:
        return {}
    rows = db.scalars(select(VisitFeedback).where(VisitFeedback.record_id.in_(record_ids)))
    return {row.record_id: row for row in rows}


def feedback_context(db: Session, record_id: str) -> dict:
    """Lo que el pop up necesita para saludar al cliente. Sin teléfono ni montos."""
    record = _record(db, record_id)
    therapist_ids = records_repo.therapist_ids(record)
    therapists = []
    for therapist_id in therapist_ids:
        therapist = catalog_repo.get_therapist(db, therapist_id)
        therapists.append(therapist.name if therapist else therapist_id)
    return {
        "visitId": record.id,
        "firstName": first_name(db, record),
        "serviceId": record.service_id,
        "serviceName": record.service_name,
        # Para el botón de "reservar de nuevo" con el mismo servicio y terapeuta.
        "therapistIds": therapist_ids,
        "therapistNames": therapists,
        "visitedAt": ensure_tz(record.paid_at).isoformat(),
        "answered": db.get(VisitFeedback, record.id) is not None,
    }


def submit_feedback(db: Session, record_id: str, payload: FeedbackCreate) -> VisitFeedback:
    record = _record(db, record_id)
    if db.get(VisitFeedback, record.id):
        raise ConflictError("Ya calificaste esta visita. ¡Gracias!")
    row = VisitFeedback(
        record_id=record.id,
        massage_rating=payload.massage_rating,
        cleanliness_rating=payload.cleanliness_rating,
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


def ratings_summary(rows: list[VisitFeedback]) -> dict:
    count = len(rows)
    average = lambda values: round(sum(values) / count, 1) if count else None  # noqa: E731
    return {
        "count": count,
        "massage": average([row.massage_rating for row in rows]),
        "cleanliness": average([row.cleanliness_rating for row in rows]),
    }
