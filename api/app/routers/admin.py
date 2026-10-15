from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ScheduleBlockCreate
from ..serializers import block_payload, customer_payload, reservation_payload
from ..services import agenda as agenda_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/agenda")
def admin_agenda(requested_date: date = Query(alias="date"), db: Session = Depends(get_db)) -> dict:
    return {
        "date": requested_date.isoformat(),
        "items": [reservation_payload(row) for row in agenda_service.agenda_for(db, requested_date)],
    }


@router.get("/reservations")
def admin_reservations(
    start: date = Query(alias="from"),
    days: int = Query(default=7, ge=1, le=62),
    db: Session = Depends(get_db),
) -> dict:
    items = agenda_service.reservations_overview(db, start, days)
    return {
        "from": start.isoformat(),
        "days": days,
        "items": [
            {
                **reservation_payload(item["reservation"]),
                "paymentId": item["reservation"].payment_id,
                "serviceName": item["serviceName"],
                "therapistNames": item["therapistNames"],
                "customer": customer_payload(item["customer"]) if item["customer"] else None,
            }
            for item in items
        ],
    }


@router.post("/blocks", status_code=201)
def create_block(payload: ScheduleBlockCreate, db: Session = Depends(get_db)) -> dict:
    return block_payload(agenda_service.create_block(db, payload))


@router.delete("/blocks/{block_id}", status_code=204)
def delete_block(block_id: str, db: Session = Depends(get_db)) -> None:
    agenda_service.delete_block(db, block_id)
