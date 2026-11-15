from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ServiceRecordCreate
from ..serializers import record_payload
from ..repositories import catalog as catalog_repo
from ..services import feedback as feedback_service
from ..services import records as records_service

# Bajo /admin para que nginx lo proteja con el usuario y contraseña de administración.
router = APIRouter(prefix="/admin/records", tags=["records"])


def _names(db: Session) -> dict[str, str]:
    return {row.id: row.name for row in catalog_repo.list_active_therapists(db)}


def _payload(db: Session, record, names: dict[str, str], feedback=None) -> dict:
    # Ya calificó: no hay nada que pedir. Si no, el SMS listo para enviarlo con un clic.
    request = None if feedback else feedback_service.feedback_request(db, record)
    return record_payload(record, names, feedback, request)


@router.get("")
def list_records(
    start: date = Query(alias="from"),
    days: int = Query(default=1, ge=1, le=366),
    db: Session = Depends(get_db),
) -> dict:
    overview = records_service.records_overview(db, start, days)
    feedback = feedback_service.feedback_by_record(db, [row.id for row in overview["rows"]])
    return {
        "from": start.isoformat(),
        "days": days,
        "summary": {**overview["summary"], "ratings": feedback_service.ratings_summary(list(feedback.values()), overview["therapists"])},
        "items": [_payload(db, row, overview["therapists"], feedback.get(row.id)) for row in overview["rows"]],
    }


@router.post("", status_code=201)
def create_record(payload: ServiceRecordCreate, db: Session = Depends(get_db)) -> dict:
    return _payload(db, records_service.create_record(db, payload), _names(db))


@router.put("/{record_id}")
def update_record(record_id: str, payload: ServiceRecordCreate, db: Session = Depends(get_db)) -> dict:
    record = records_service.update_record(db, record_id, payload)
    return _payload(db, record, _names(db), feedback_service.feedback_by_record(db, [record.id]).get(record.id))


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: str, db: Session = Depends(get_db)) -> None:
    records_service.delete_record(db, record_id)


@router.post("/{record_id}/feedback-request")
def mark_feedback_requested(record_id: str, db: Session = Depends(get_db)) -> dict:
    """Recepción abrió el WhatsApp para pedir la calificación: queda marcado como enviado."""
    record = feedback_service.mark_requested(db, record_id)
    return _payload(db, record, _names(db), feedback_service.feedback_by_record(db, [record.id]).get(record.id))
