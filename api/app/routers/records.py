from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ServiceRecordCreate
from ..serializers import record_payload
from ..repositories import catalog as catalog_repo
from ..services import records as records_service

# Bajo /admin para que nginx lo proteja con el usuario y contraseña de administración.
router = APIRouter(prefix="/admin/records", tags=["records"])


def _names(db: Session) -> dict[str, str]:
    return {row.id: row.name for row in catalog_repo.list_active_therapists(db)}


@router.get("")
def list_records(
    start: date = Query(alias="from"),
    days: int = Query(default=1, ge=1, le=366),
    db: Session = Depends(get_db),
) -> dict:
    overview = records_service.records_overview(db, start, days)
    return {
        "from": start.isoformat(),
        "days": days,
        "summary": overview["summary"],
        "items": [record_payload(row, overview["therapists"]) for row in overview["rows"]],
    }


@router.post("", status_code=201)
def create_record(payload: ServiceRecordCreate, db: Session = Depends(get_db)) -> dict:
    return record_payload(records_service.create_record(db, payload), _names(db))


@router.put("/{record_id}")
def update_record(record_id: str, payload: ServiceRecordCreate, db: Session = Depends(get_db)) -> dict:
    return record_payload(records_service.update_record(db, record_id, payload), _names(db))


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: str, db: Session = Depends(get_db)) -> None:
    records_service.delete_record(db, record_id)
