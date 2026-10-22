from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import FinanceMovement


def list_movements(db: Session, start: Optional[date] = None, end: Optional[date] = None) -> list[FinanceMovement]:
    statement = select(FinanceMovement)
    if start:
        statement = statement.where(FinanceMovement.day >= start.isoformat())
    if end:
        statement = statement.where(FinanceMovement.day <= end.isoformat())
    return list(db.scalars(statement.order_by(FinanceMovement.day.desc(), FinanceMovement.created_at.desc())).all())


def get(db: Session, movement_id: str) -> Optional[FinanceMovement]:
    return db.get(FinanceMovement, movement_id)


def save(db: Session, movement: FinanceMovement) -> FinanceMovement:
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def delete(db: Session, movement: FinanceMovement) -> None:
    db.delete(movement)
    db.commit()
