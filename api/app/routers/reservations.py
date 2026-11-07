from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ReservationCreate, ReservationReschedule
from ..serializers import reservation_payload
from ..services import operations as ops_service
from ..services import reservations as reservations_service

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", status_code=201)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)) -> dict:
    return reservation_payload(reservations_service.create_reservation(db, payload))


@router.get("/{reservation_id}")
def get_reservation(reservation_id: str, db: Session = Depends(get_db)) -> dict:
    return reservation_payload(reservations_service.get_reservation(db, reservation_id))


@router.patch("/{reservation_id}/reschedule")
def reschedule_reservation(
    reservation_id: str,
    payload: ReservationReschedule,
    db: Session = Depends(get_db),
) -> dict:
    return reservation_payload(reservations_service.reschedule_reservation(db, reservation_id, payload))


@router.get("/{reservation_id}/calendar.ics")
def reservation_calendar(reservation_id: str, db: Session = Depends(get_db)) -> Response:
    # Público como la reserva misma (el id es imposible de adivinar); no lleva datos personales.
    body = ops_service.calendar_for(db, reservation_id)
    return Response(body, media_type="text/calendar; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="ssensuum.ics"'})
