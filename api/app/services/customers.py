import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..domain import customer_profile as profile
from ..domain.customers import normalize_email, normalize_phone
from ..domain.marketing import SOURCES, clean_source
from ..domain.errors import ConflictError, NotFoundError, ValidationError
from ..domain.rules import TZ, ensure_tz, hold_expired
from ..models import Customer, Reservation, ServiceRecord
from ..repositories import catalog as catalog_repo
from ..repositories import customers as customers_repo
from ..repositories import records as records_repo
from ..repositories import reservations as reservations_repo
from ..schemas import CustomerCreate, CustomerUpdate

DUPLICATE_PHONE = "Ya existe un cliente con ese teléfono"


def _clean_phone(value: str) -> str:
    phone = normalize_phone(value)
    if not phone:
        raise ValidationError("El teléfono debe tener 10 dígitos")
    return phone


def _clean_email(value: Optional[str]) -> Optional[str]:
    if value is None or not value.strip():
        return None
    email = normalize_email(value)
    if not email:
        raise ValidationError("El correo no es válido")
    return email


def _clean_first_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ValidationError("El nombre es obligatorio")
    return name


def _clean_source(value: Optional[str]) -> Optional[str]:
    if value is None or not value.strip():
        return None
    source = clean_source(value)
    if not source:
        raise ValidationError("Origen no reconocido")
    return source


def _save(db: Session, customer: Customer) -> Customer:
    try:
        return customers_repo.save(db, customer)
    except IntegrityError:
        db.rollback()
        raise ConflictError(DUPLICATE_PHONE)


def get_customer(db: Session, customer_id: str) -> Customer:
    customer = customers_repo.get(db, customer_id)
    if not customer:
        raise NotFoundError("Cliente no encontrado")
    return customer


# "sin_origen" filtra a quien aún no tiene red de origen registrada.
NO_SOURCE = "sin_origen"


def _check_source_filter(source: Optional[str]) -> None:
    if source and source != NO_SOURCE and source not in SOURCES:
        raise ValidationError("Origen no reconocido")


def _matches_source(customer: Customer, source: Optional[str]) -> bool:
    if not source:
        return True
    return customer.acquisition_source is None if source == NO_SOURCE else customer.acquisition_source == source


def search_customers(
    db: Session, query: Optional[str], limit: int, offset: int, stage: Optional[str] = None, source: Optional[str] = None
) -> list[tuple[Customer, dict]]:
    """Clientes con su resumen de perfil; con etapa u origen, la paginación aplica después de filtrar."""
    if stage and stage not in profile.FUNNEL_STAGES:
        raise ValidationError("Etapa no reconocida")
    _check_source_filter(source)
    text = (query or "").strip()
    # Permite buscar por teléfono aunque venga con espacios, guiones o +52.
    phone = normalize_phone(text)
    if stage or source:
        customers = [row for row in customers_repo.search(db, phone or text or None) if _matches_source(row, source)]
        rows = [row for row in _with_summaries(db, customers) if not stage or row[1]["stage"] == stage]
        return rows[offset:offset + limit]
    return _with_summaries(db, customers_repo.search(db, phone or text or None, limit, offset))


def summaries(db: Session, customers: Optional[list[Customer]] = None) -> list[tuple[Customer, dict]]:
    return _with_summaries(db, customers if customers is not None else customers_repo.list_all(db))


def funnel_summary(db: Session, source: Optional[str] = None) -> dict:
    _check_source_filter(source)
    counts = {stage: 0 for stage in profile.FUNNEL_STAGES}
    customers = [row for row in customers_repo.list_all(db) if _matches_source(row, source)]
    for _, summary in _with_summaries(db, customers):
        counts[summary["stage"]] += 1
    return {
        "total": sum(counts.values()),
        "stages": [{"stage": stage, "label": label, "count": counts[stage]} for stage, label in profile.FUNNEL_STAGES.items()],
    }


def customer_profile(db: Session, customer_id: str) -> tuple[Customer, dict]:
    customer = get_customer(db, customer_id)
    records = records_repo.list_for_customers(db, [customer.id])
    reservations = reservations_repo.list_for_customers(db, [customer.id])
    now = datetime.now(TZ)
    therapists = {row.id: row.name for row in catalog_repo.list_therapists(db)}
    services = {row.id: row.name for row in catalog_repo.list_services(db)}
    visits = _visits(records, reservations, now, services)
    upcoming = _upcoming(reservations, now)
    member = profile.membership_active(customer.membership_expires_on, now.date())

    preferences = profile.preferences(visits)
    favorite = preferences["therapistId"]
    if favorite:
        favorite["label"] = therapists.get(favorite["value"], favorite["value"])
    return customer, {
        "stage": profile.funnel_stage(visits, bool(upcoming), member, now.date()),
        "member": member,
        "recurrence": profile.recurrence(visits, now.date()),
        "preferences": preferences,
        "quiz": profile.load_quiz(customer.quiz_json),
        "quizAt": ensure_tz(customer.quiz_at).isoformat() if customer.quiz_at else None,
        "upcoming": [
            {"startsAt": ensure_tz(row.starts_at).isoformat(), "serviceName": services.get(row.service_id, row.service_id), "status": row.status}
            for row in upcoming
        ],
        "history": [
            {
                "at": visit.at.isoformat(),
                "serviceName": visit.service_name,
                "therapistNames": [therapists.get(tid, tid) for tid in visit.therapist_ids],
                "amount": visit.amount,
                "tip": visit.tip,
            }
            for visit in sorted(visits, key=lambda visit: visit.at, reverse=True)
        ],
    }


# Reservas que cuentan como cita real (pagada o por resolver); las demás no llegaron a confirmarse.
_BOOKED_STATUSES = {"CONFIRMED", "NEEDS_ATTENTION"}


def _visits(records: list[ServiceRecord], reservations: list[Reservation], now: datetime, service_names: Optional[dict[str, str]] = None) -> list[profile.Visit]:
    """Cada servicio registrado es una visita; una reserva confirmada que ya pasó cuenta si ese día no hay registro."""
    visits = [
        profile.Visit(
            at=ensure_tz(record.paid_at),
            service_name=record.service_name,
            therapist_ids=records_repo.therapist_ids(record),
            amount=record.amount,
            tip=sum(tip["amount"] for tip in records_repo.tips(record)),
        )
        for record in records
    ]
    recorded_days = {visit.at.date() for visit in visits}
    for reservation in reservations:
        starts_at = ensure_tz(reservation.starts_at)
        if reservation.status in _BOOKED_STATUSES and starts_at <= now and starts_at.date() not in recorded_days:
            visits.append(profile.Visit(at=starts_at, service_name=(service_names or {}).get(reservation.service_id, reservation.service_id), therapist_ids=reservations_repo.therapist_ids(reservation)))
    return visits


def _upcoming(reservations: list[Reservation], now: datetime) -> list[Reservation]:
    return [
        row for row in reservations
        if ensure_tz(row.starts_at) > now and (
            row.status in _BOOKED_STATUSES or (row.status == "PENDING_PAYMENT" and not hold_expired(row.hold_expires_at))
        )
    ]


def _with_summaries(db: Session, customers: list[Customer]) -> list[tuple[Customer, dict]]:
    """Etapa, visitas y última visita de cada cliente, con dos consultas para toda la lista."""
    ids = [customer.id for customer in customers]
    records: dict[str, list[ServiceRecord]] = {}
    for record in records_repo.list_for_customers(db, ids) if ids else []:
        records.setdefault(record.customer_id, []).append(record)
    reservations: dict[str, list[Reservation]] = {}
    for reservation in reservations_repo.list_for_customers(db, ids) if ids else []:
        reservations.setdefault(reservation.customer_id, []).append(reservation)

    now = datetime.now(TZ)
    rows = []
    for customer in customers:
        own_reservations = reservations.get(customer.id, [])
        visits = _visits(records.get(customer.id, []), own_reservations, now)
        days = profile.visit_days(visits)
        member = profile.membership_active(customer.membership_expires_on, now.date())
        rows.append((customer, {
            "stage": profile.funnel_stage(visits, bool(_upcoming(own_reservations, now)), member, now.date()),
            "visits": len(days),
            "lastVisit": days[-1].isoformat() if days else None,
        }))
    return rows


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    phone = _clean_phone(payload.phone)
    if customers_repo.get_by_phone(db, phone):
        raise ConflictError(DUPLICATE_PHONE)
    customer = Customer(
        id=str(uuid.uuid4()),
        phone=phone,
        first_name=_clean_first_name(payload.first_name),
        last_name=payload.last_name.strip(),
        email=_clean_email(payload.email),
        birthday=payload.birthday.isoformat() if payload.birthday else None,
        membership_expires_on=payload.membership_expires_on.isoformat() if payload.membership_expires_on else None,
        notes=(payload.notes or "").strip() or None,
        acquisition_source=_clean_source(payload.acquisition_source),
    )
    return _save(db, customer)


def update_customer(db: Session, customer_id: str, payload: CustomerUpdate) -> Customer:
    customer = get_customer(db, customer_id)
    changes = payload.model_dump(exclude_unset=True)

    if "phone" in changes:
        if changes["phone"] is None:
            raise ValidationError("El teléfono debe tener 10 dígitos")
        phone = _clean_phone(changes["phone"])
        existing = customers_repo.get_by_phone(db, phone)
        if existing and existing.id != customer.id:
            raise ConflictError(DUPLICATE_PHONE)
        customer.phone = phone
    if "first_name" in changes:
        customer.first_name = _clean_first_name(changes["first_name"] or "")
    if "last_name" in changes:
        customer.last_name = (changes["last_name"] or "").strip()
    if "email" in changes:
        customer.email = _clean_email(changes["email"])
    if "birthday" in changes:
        customer.birthday = changes["birthday"].isoformat() if changes["birthday"] else None
    if "membership_expires_on" in changes:
        value = changes["membership_expires_on"]
        customer.membership_expires_on = value.isoformat() if value else None
    if "notes" in changes:
        customer.notes = (changes["notes"] or "").strip() or None
    if "acquisition_source" in changes:
        customer.acquisition_source = _clean_source(changes["acquisition_source"])

    return _save(db, customer)


def set_source_if_missing(customer: Customer, source: Optional[str]) -> None:
    """Guarda el primer origen conocido; uno posterior no lo reemplaza (eso se corrige a mano en la ficha)."""
    if source and not customer.acquisition_source:
        customer.acquisition_source = source
