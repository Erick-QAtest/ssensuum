import uuid
from datetime import date as date_type

from sqlalchemy.orm import Session

from ..domain.errors import NotFoundError, ValidationError
from ..domain.rules import ensure_tz, parse_iso_datetime
from ..models import Reservation, ScheduleBlock
from ..repositories import blocks as blocks_repo
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
