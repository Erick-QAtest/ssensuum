from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import availability as availability_service

router = APIRouter(tags=["availability"])


@router.get("/availability")
def availability(
    service_id: str = Query(alias="serviceId"),
    requested_date: date = Query(alias="date"),
    therapist_id: Optional[str] = Query(default=None, alias="therapistId"),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "date": requested_date.isoformat(),
        "timezone": "America/Mexico_City",
        "slots": availability_service.slots_for(db, service_id, requested_date, therapist_id),
    }
