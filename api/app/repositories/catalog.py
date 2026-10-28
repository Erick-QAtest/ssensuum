from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Service, Therapist


def list_active_services(db: Session) -> list[Service]:
    return list(db.scalars(select(Service).where(Service.active.is_(True)).order_by(Service.category, Service.name)).all())


def get_service(db: Session, service_id: str) -> Optional[Service]:
    return db.get(Service, service_id)


def list_active_therapists(db: Session) -> list[Therapist]:
    return list(db.scalars(select(Therapist).where(Therapist.active.is_(True)).order_by(Therapist.name)).all())


def active_therapist_ids(db: Session) -> list[str]:
    return [row.id for row in db.scalars(select(Therapist).where(Therapist.active.is_(True))).all()]


def get_therapist(db: Session, therapist_id: str) -> Optional[Therapist]:
    return db.get(Therapist, therapist_id)


def therapist_exists(db: Session, therapist_id: str) -> bool:
    return db.get(Therapist, therapist_id) is not None
