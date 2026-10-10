import json
import threading
import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from ..domain.errors import ConflictError, InconsistentDataError, NotFoundError, ValidationError
from ..domain.rules import (
    DEFAULT_CABIN_ID,
    can_reschedule,
    parse_iso_datetime,
    validate_minimum_lead_time,
    validate_opening_hours,
)
from ..models import Reservation
from ..repositories import catalog as catalog_repo
from ..repositories import reservations as reservations_repo
from ..schemas import ReservationCreate, ReservationReschedule
from .availability import has_conflict

reservation_lock = threading.Lock()


def get_reservation(db: Session, reservation_id: str) -> Reservation:
    reservation = reservations_repo.get(db, reservation_id)
    if not reservation:
        raise NotFoundError("Reserva no encontrada")
    return reservation


def create_reservation(db: Session, payload: ReservationCreate) -> Reservation:
    service = catalog_repo.get_service(db, payload.service_id)
    if not service:
        raise NotFoundError("Servicio no encontrado")

    if len(set(payload.therapist_ids)) != len(payload.therapist_ids):
        raise ValidationError("Los terapeutas deben ser distintos")
    if len(payload.therapist_ids) != service.therapists_required:
        raise ValidationError(f"Este servicio requiere {service.therapists_required} terapeuta(s)")
    if not all(catalog_repo.therapist_exists(db, therapist_id) for therapist_id in payload.therapist_ids):
        raise NotFoundError("Uno o más terapeutas no existen")

    starts_at = parse_iso_datetime(payload.starts_at)
    ends_at = starts_at + timedelta(minutes=service.duration_minutes)
    cabin_id = payload.cabin_id or DEFAULT_CABIN_ID

    if not validate_minimum_lead_time(starts_at):
        raise ValidationError("La cita debe reservarse con al menos 3 horas de anticipación")
    if not validate_opening_hours(starts_at, service.duration_minutes):
        raise ValidationError("El horario está fuera del horario del club")

    # MVP local: serializa check+insert para hacer visible la regla RF-055.
    # En producción debe reforzarse con locking/constraints transaccionales en PostgreSQL.
    with reservation_lock:
        if has_conflict(db, starts_at, ends_at, payload.therapist_ids, cabin_id):
            raise ConflictError("El terapeuta o la cabina ya están ocupados")

        reservation = Reservation(
            id=str(uuid.uuid4()),
            customer_id=payload.customer_id,
            service_id=service.id,
            therapist_ids_json=json.dumps(payload.therapist_ids),
            starts_at=starts_at,
            ends_at=ends_at,
            cabin_id=cabin_id,
            source=payload.source or "web",
            status="PENDING_PAYMENT",
            deposit_amount=service.deposit,
        )
        return reservations_repo.save(db, reservation)


def reschedule_reservation(db: Session, reservation_id: str, payload: ReservationReschedule) -> Reservation:
    reservation = get_reservation(db, reservation_id)

    if not can_reschedule(reservation.starts_at):
        raise ValidationError("Con menos de 5 horas el anticipo se pierde")

    service = catalog_repo.get_service(db, reservation.service_id)
    if not service:
        raise InconsistentDataError("Servicio de la reserva no existe")

    new_start = parse_iso_datetime(payload.starts_at)
    new_end = new_start + timedelta(minutes=service.duration_minutes)
    therapist_ids = reservations_repo.therapist_ids(reservation)

    if not validate_minimum_lead_time(new_start):
        raise ValidationError("La nueva cita debe tener al menos 3 horas de anticipación")
    if has_conflict(db, new_start, new_end, therapist_ids, reservation.cabin_id, reservation.id):
        raise ConflictError("El nuevo horario ya está ocupado")

    reservation.starts_at = new_start
    reservation.ends_at = new_end
    reservation.status = "PENDING_PAYMENT"
    return reservations_repo.save(db, reservation)
