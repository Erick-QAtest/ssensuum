import json
from datetime import datetime
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..domain.rules import TZ
from ..models import Reservation

INACTIVE_STATUSES = ["CANCELLED", "RESCHEDULED"]


def therapist_ids(reservation: Reservation) -> list[str]:
    return json.loads(reservation.therapist_ids_json)


def get(db: Session, reservation_id: str) -> Optional[Reservation]:
    return db.get(Reservation, reservation_id)


def list_ordered(db: Session) -> list[Reservation]:
    return list(db.scalars(select(Reservation).order_by(Reservation.starts_at)).all())


def list_active_starting_between(db: Session, start: datetime, end: datetime) -> list[Reservation]:
    return list(
        db.scalars(
            select(Reservation).where(
                Reservation.starts_at >= start,
                Reservation.starts_at < end,
                Reservation.status.not_in(INACTIVE_STATUSES),
                or_(
                    Reservation.status != "PENDING_PAYMENT",
                    Reservation.hold_expires_at.is_(None),
                    Reservation.hold_expires_at > datetime.now(TZ),
                ),
            )
        ).all()
    )


def list_for_customers(db: Session, customer_ids: list[str]) -> list[Reservation]:
    statement = select(Reservation).where(Reservation.customer_id.in_(customer_ids)).order_by(Reservation.starts_at)
    return list(db.scalars(statement).all())


def save(db: Session, reservation: Reservation) -> Reservation:
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation
