from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import HrDocument, StaffProfile, Therapist


def list_therapists(db: Session) -> list[Therapist]:
    """Todo el equipo, incluidas las bajas, para conservar su expediente."""
    return list(db.scalars(select(Therapist).order_by(Therapist.active.desc(), Therapist.name)).all())


def get_therapist(db: Session, therapist_id: str) -> Optional[Therapist]:
    return db.get(Therapist, therapist_id)


def profiles(db: Session) -> dict[str, StaffProfile]:
    return {row.therapist_id: row for row in db.scalars(select(StaffProfile)).all()}


def get_profile(db: Session, therapist_id: str) -> Optional[StaffProfile]:
    return db.get(StaffProfile, therapist_id)


def document_counts(db: Session) -> dict[Optional[str], int]:
    statement = select(HrDocument.therapist_id, func.count()).group_by(HrDocument.therapist_id)
    return {therapist_id: count for therapist_id, count in db.execute(statement).all()}


def categories_by_therapist(db: Session) -> dict[str, set[str]]:
    statement = select(HrDocument.therapist_id, HrDocument.category).where(HrDocument.therapist_id.is_not(None)).distinct()
    result: dict[str, set[str]] = {}
    for therapist_id, category in db.execute(statement).all():
        result.setdefault(therapist_id, set()).add(category)
    return result


def list_documents(
    db: Session,
    therapist_id: Optional[str] = None,
    general_only: bool = False,
    category: Optional[str] = None,
    exclude_category: Optional[str] = None,
) -> list[HrDocument]:
    statement = select(HrDocument)
    if category:
        statement = statement.where(HrDocument.category == category)
    if exclude_category:
        statement = statement.where(HrDocument.category != exclude_category)
    if general_only:
        statement = statement.where(HrDocument.therapist_id.is_(None))
    elif therapist_id:
        statement = statement.where(HrDocument.therapist_id == therapist_id)
    return list(db.scalars(statement.order_by(HrDocument.uploaded_at.desc())).all())


def get_document(db: Session, document_id: str) -> Optional[HrDocument]:
    return db.get(HrDocument, document_id)


def save(db: Session, row):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete(db: Session, row) -> None:
    db.delete(row)
    db.commit()
