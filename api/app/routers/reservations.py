from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ReservationCreate, ReservationReschedule
from ..serializers import reservation_payload
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
