from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import SiteEventCreate
from ..services import events as events_service

router = APIRouter(tags=["events"])


@router.post("/events", status_code=204)
def record_event(payload: SiteEventCreate, db: Session = Depends(get_db)) -> Response:
    events_service.record(db, payload)
    return Response(status_code=204)


@router.get("/admin/events")
def events_summary(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)) -> dict:
    return events_service.summary(db, days)
