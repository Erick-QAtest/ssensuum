from datetime import date as date_type
from datetime import datetime, time, timedelta
from itertools import combinations
from typing import Optional

from sqlalchemy.orm import Session

from ..domain.errors import NotFoundError
from ..domain.rules import (
    DEFAULT_CABIN_ID,
    LAST_ONE_HOUR_START,
    OPEN_TIME,
    SLOT_STEP_MINUTES,
    TZ,
    ensure_tz,
    overlaps,
    validate_minimum_lead_time,
)
from ..models import Service
from ..repositories import blocks as blocks_repo
from ..repositories import catalog as catalog_repo
from ..repositories import reservations as reservations_repo


def has_conflict(
    db: Session,
    starts_at: datetime,
    ends_at: datetime,
    therapist_ids: list[str],
    cabin_id: str,
    exclude_reservation_id: Optional[str] = None,
) -> bool:
    day_start = datetime.combine(ensure_tz(starts_at).date(), time.min, tzinfo=TZ)
    day_end = day_start + timedelta(days=1)

    for reservation in reservations_repo.list_active_starting_between(db, day_start, day_end):
        if exclude_reservation_id and reservation.id == exclude_reservation_id:
            continue
        if not overlaps(starts_at, ends_at, ensure_tz(reservation.starts_at), ensure_tz(reservation.ends_at)):
            continue
        same_cabin = reservation.cabin_id == cabin_id
        same_therapist = bool(set(therapist_ids) & set(reservations_repo.therapist_ids(reservation)))
        if same_cabin or same_therapist:
            return True

    for block in blocks_repo.list_overlapping(db, starts_at, ends_at):
        if block.cabin_id and block.cabin_id == cabin_id:
            return True
        if block.therapist_id and block.therapist_id in therapist_ids:
            return True

    return False


def free_therapists(
    db: Session,
    candidates: list[str],
    required: int,
    starts_at: datetime,
    ends_at: datetime,
) -> Optional[list[str]]:
    """Primer grupo de `required` terapeutas libres en ese horario, o None."""
    for group in combinations(candidates, required):
        if not has_conflict(db, starts_at, ends_at, list(group), DEFAULT_CABIN_ID):
            return list(group)
    return None


def least_busy_first(db: Session, candidates: list[str], day: date_type) -> list[str]:
    """Ordena a los terapeutas por cuántas reservas tienen ese día, para repartir "sin preferencia"."""
    day_start = datetime.combine(day, time.min, tzinfo=TZ)
    load = {therapist_id: 0 for therapist_id in candidates}
    for reservation in reservations_repo.list_active_starting_between(db, day_start, day_start + timedelta(days=1)):
        for therapist_id in reservations_repo.therapist_ids(reservation):
            if therapist_id in load:
                load[therapist_id] += 1
    return sorted(candidates, key=lambda therapist_id: load[therapist_id])


def build_slots(
    db: Session,
    service: Service,
    requested_date: date_type,
    therapist_id: Optional[str],
) -> list[str]:
    therapists = [therapist_id] if therapist_id else catalog_repo.active_therapist_ids(db)
    if not therapists:
        return []

    day_start = datetime.combine(requested_date, OPEN_TIME, tzinfo=TZ)
    final_start = datetime.combine(requested_date, LAST_ONE_HOUR_START, tzinfo=TZ)
    slots: list[str] = []
    cursor = day_start

    while cursor <= final_start:
        end = cursor + timedelta(minutes=service.duration_minutes)
        if validate_minimum_lead_time(cursor) and free_therapists(db, therapists, service.therapists_required, cursor, end):
            slots.append(cursor.strftime("%H:%M"))
        cursor += timedelta(minutes=SLOT_STEP_MINUTES)

    return slots


def slots_for(db: Session, service_id: str, requested_date: date_type, therapist_id: Optional[str]) -> list[str]:
    service = catalog_repo.get_service(db, service_id)
    if not service or not service.active:
        raise NotFoundError("Servicio no encontrado")
    if therapist_id and not catalog_repo.therapist_exists(db, therapist_id):
        raise NotFoundError("Terapeuta no encontrado")
    return build_slots(db, service, requested_date, therapist_id)
