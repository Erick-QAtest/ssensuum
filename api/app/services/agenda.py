import uuid
from datetime import date as date_type
from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from ..domain.errors import NotFoundError, ValidationError
from ..domain.rules import TZ, ensure_tz, parse_iso_datetime
from ..models import Reservation, ScheduleBlock
from ..repositories import blocks as blocks_repo
from ..repositories import catalog as catalog_repo
from ..repositories import customers as customers_repo
from ..repositories import reservations as reservations_repo
from ..schemas import ScheduleBlockCreate


def agenda_for(db: Session, requested_date: date_type) -> list[Reservation]:
    rows = reservations_repo.list_ordered(db)
    return [row for row in rows if ensure_tz(row.starts_at).date() == requested_date]


def create_block(db: Session, payload: ScheduleBlockCreate) -> ScheduleBlock:
    starts_at = parse_iso_datetime(payload.starts_at)
    ends_at = parse_iso_datetime(payload.ends_at)
    if ends_at <= starts_at:
        raise ValidationError("El fin debe ser posterior al inicio")
    block = ScheduleBlock(
        id=str(uuid.uuid4()),
        therapist_id=payload.therapist_id,
        cabin_id=payload.cabin_id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=payload.reason,
    )
    return blocks_repo.save(db, block)


def delete_block(db: Session, block_id: str) -> None:
    block = blocks_repo.get(db, block_id)
    if not block:
        raise NotFoundError("Bloqueo no encontrado")
    blocks_repo.delete(db, block)


def reservations_overview(db: Session, start_date: date_type, days: int) -> list[dict]:
    """Reservas vigentes (pagadas, por pagar o por resolver) con los datos que necesita recepción."""
    start = datetime.combine(start_date, time.min, tzinfo=TZ)
    rows = sorted(
        reservations_repo.list_active_starting_between(db, start, start + timedelta(days=days)),
        key=lambda row: ensure_tz(row.starts_at),
    )
    therapists = {row.id: row.name for row in catalog_repo.list_active_therapists(db)}
    items = []
    for reservation in rows:
        service = catalog_repo.get_service(db, reservation.service_id)
        customer = customers_repo.get(db, reservation.customer_id) if reservation.customer_id else None
        items.append({
            "reservation": reservation,
            "serviceName": service.name if service else reservation.service_id,
            "therapistNames": [therapists.get(tid, tid) for tid in reservations_repo.therapist_ids(reservation)],
            "customer": customer,
        })
    return items
