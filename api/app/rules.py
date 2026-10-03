import json
from datetime import date as date_type
from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Reservation, ScheduleBlock, Service, Therapist

TZ = ZoneInfo("America/Mexico_City")
OPEN_TIME = time(9, 0)
LAST_ONE_HOUR_START = time(19, 30)
SLOT_STEP_MINUTES = 30


def ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def parse_iso_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_tz(dt)


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def reservation_therapists(reservation: Reservation) -> list[str]:
    return json.loads(reservation.therapist_ids_json)


def validate_minimum_lead_time(starts_at: datetime, now: Optional[datetime] = None) -> bool:
    current = ensure_tz(now or datetime.now(TZ))
    return ensure_tz(starts_at) >= current + timedelta(hours=3)


def validate_opening_hours(starts_at: datetime, duration_minutes: int) -> bool:
    local = ensure_tz(starts_at)
    day_open = datetime.combine(local.date(), OPEN_TIME, tzinfo=TZ)
    day_close = datetime.combine(local.date(), time(20, 30), tzinfo=TZ)
    return local >= day_open and local + timedelta(minutes=duration_minutes) <= day_close


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
    reservations = db.scalars(
        select(Reservation).where(
            Reservation.starts_at >= day_start,
            Reservation.starts_at < day_end,
            Reservation.status.not_in(["CANCELLED", "RESCHEDULED"]),
        )
    ).all()

    for reservation in reservations:
        if exclude_reservation_id and reservation.id == exclude_reservation_id:
            continue
        if not overlaps(starts_at, ends_at, ensure_tz(reservation.starts_at), ensure_tz(reservation.ends_at)):
            continue
        same_cabin = reservation.cabin_id == cabin_id
        same_therapist = bool(set(therapist_ids) & set(reservation_therapists(reservation)))
        if same_cabin or same_therapist:
            return True

    blocks = db.scalars(
        select(ScheduleBlock).where(
            ScheduleBlock.starts_at < ends_at,
            ScheduleBlock.ends_at > starts_at,
        )
    ).all()
    for block in blocks:
        if block.cabin_id and block.cabin_id == cabin_id:
            return True
        if block.therapist_id and block.therapist_id in therapist_ids:
            return True

    return False


def therapist_exists(db: Session, therapist_id: str) -> bool:
    return db.get(Therapist, therapist_id) is not None


def build_slots(
    db: Session,
    service: Service,
    requested_date: date_type,
    therapist_id: Optional[str],
) -> list[str]:
    therapists = [therapist_id] if therapist_id else [row.id for row in db.scalars(select(Therapist).where(Therapist.active.is_(True))).all()]
    if not therapists:
        return []

    day_start = datetime.combine(requested_date, OPEN_TIME, tzinfo=TZ)
    final_start = datetime.combine(requested_date, LAST_ONE_HOUR_START, tzinfo=TZ)
    slots: list[str] = []
    cursor = day_start

    while cursor <= final_start:
        end = cursor + timedelta(minutes=service.duration_minutes)
        if validate_minimum_lead_time(cursor):
            if service.therapists_required == 1:
                available = any(not has_conflict(db, cursor, end, [tid], "cabin-1") for tid in therapists)
            else:
                available = False
                for i, first in enumerate(therapists):
                    for second in therapists[i + 1 :]:
                        if not has_conflict(db, cursor, end, [first, second], "cabin-1"):
                            available = True
                            break
                    if available:
                        break
            if available:
                slots.append(cursor.strftime("%H:%M"))
        cursor += timedelta(minutes=SLOT_STEP_MINUTES)

    return slots
