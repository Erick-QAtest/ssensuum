from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import SiteEvent


def add(db: Session, event: SiteEvent) -> None:
    db.add(event)
    db.commit()


def counts_since(db: Session, since: datetime) -> list[tuple[str, str, int]]:
    statement = (
        select(SiteEvent.name, SiteEvent.label, func.count())
        .where(SiteEvent.created_at >= since)
        .group_by(SiteEvent.name, SiteEvent.label)
        .order_by(SiteEvent.name, func.count().desc())
    )
    return [(name, label, count) for name, label, count in db.execute(statement).all()]
