from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ScheduleBlock


def get(db: Session, block_id: str) -> Optional[ScheduleBlock]:
    return db.get(ScheduleBlock, block_id)


def list_overlapping(db: Session, starts_at: datetime, ends_at: datetime) -> list[ScheduleBlock]:
    return list(
        db.scalars(
            select(ScheduleBlock).where(
                ScheduleBlock.starts_at < ends_at,
                ScheduleBlock.ends_at > starts_at,
            )
        ).all()
    )


def save(db: Session, block: ScheduleBlock) -> ScheduleBlock:
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def delete(db: Session, block: ScheduleBlock) -> None:
    db.delete(block)
    db.commit()
