import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ServiceRecord


def therapist_ids(record: ServiceRecord) -> list[str]:
    return json.loads(record.therapist_ids_json)


def tips(record: ServiceRecord) -> list[dict]:
    return json.loads(record.tips_json or "[]")


def get(db: Session, record_id: str) -> Optional[ServiceRecord]:
    return db.get(ServiceRecord, record_id)


def list_paid_between(db: Session, start: datetime, end: datetime) -> list[ServiceRecord]:
    statement = (
        select(ServiceRecord)
        .where(ServiceRecord.paid_at >= start, ServiceRecord.paid_at < end)
        .order_by(ServiceRecord.paid_at.desc())
    )
    return list(db.scalars(statement).all())


def list_for_customers(db: Session, customer_ids: list[str]) -> list[ServiceRecord]:
    statement = select(ServiceRecord).where(ServiceRecord.customer_id.in_(customer_ids)).order_by(ServiceRecord.paid_at)
    return list(db.scalars(statement).all())


def save(db: Session, record: ServiceRecord) -> ServiceRecord:
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete(db: Session, record: ServiceRecord) -> None:
    db.delete(record)
    db.commit()
