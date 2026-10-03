import json
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .models import Reservation, ScheduleBlock, Service, Therapist
from .rules import (
    TZ,
    build_slots,
    ensure_tz,
    has_conflict,
    parse_iso_datetime,
    therapist_exists,
    validate_minimum_lead_time,
    validate_opening_hours,
)
from .schemas import ReservationCreate, ReservationReschedule, ScheduleBlockCreate
from .seed import seed

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="SSENSUUM API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reservation_lock = threading.Lock()



def service_payload(service: Service) -> dict:
    return {
        "id": service.id,
        "name": service.name,
        "category": service.category,
        "description": service.description,
        "durationMinutes": service.duration_minutes,
        "publicPrice": service.public_price,
        "memberPrice": service.member_price,
        "deposit": service.deposit,
        "therapistsRequired": service.therapists_required,
    }


def therapist_payload(therapist: Therapist) -> dict:
    return {
        "id": therapist.id,
        "name": therapist.name,
        "strengths": therapist.strengths,
        "photoUrl": therapist.photo_url,
    }


def reservation_payload(reservation: Reservation) -> dict:
    return {
        "id": reservation.id,
        "customerId": reservation.customer_id,
        "serviceId": reservation.service_id,
        "therapistIds": json.loads(reservation.therapist_ids_json),
        "startsAt": ensure_tz(reservation.starts_at).isoformat(),
        "endsAt": ensure_tz(reservation.ends_at).isoformat(),
        "cabinId": reservation.cabin_id,
        "source": reservation.source,
        "status": reservation.status,
        "depositAmount": reservation.deposit_amount,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ssensuum-api"}


@app.get("/services")
def services(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Service).where(Service.active.is_(True)).order_by(Service.category, Service.name)).all()
    return [service_payload(row) for row in rows]


@app.get("/therapists")
def therapists(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Therapist).where(Therapist.active.is_(True)).order_by(Therapist.name)).all()
    return [therapist_payload(row) for row in rows]


@app.get("/availability")
def availability(
    service_id: str = Query(alias="serviceId"),
    requested_date: date = Query(alias="date"),
    therapist_id: Optional[str] = Query(default=None, alias="therapistId"),
    db: Session = Depends(get_db),
) -> dict:
    service = db.get(Service, service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    if therapist_id and not therapist_exists(db, therapist_id):
        raise HTTPException(status_code=404, detail="Terapeuta no encontrado")

    return {
        "date": requested_date.isoformat(),
        "timezone": "America/Mexico_City",
        "slots": build_slots(db, service, requested_date, therapist_id),
    }


@app.post("/reservations", status_code=201)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)) -> dict:
    service = db.get(Service, payload.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    if len(set(payload.therapist_ids)) != len(payload.therapist_ids):
        raise HTTPException(status_code=422, detail="Los terapeutas deben ser distintos")
    if len(payload.therapist_ids) != service.therapists_required:
        raise HTTPException(status_code=422, detail=f"Este servicio requiere {service.therapists_required} terapeuta(s)")
    if not all(therapist_exists(db, therapist_id) for therapist_id in payload.therapist_ids):
        raise HTTPException(status_code=404, detail="Uno o más terapeutas no existen")

    starts_at = parse_iso_datetime(payload.starts_at)
    ends_at = starts_at + timedelta(minutes=service.duration_minutes)
    cabin_id = payload.cabin_id or "cabin-1"

    if not validate_minimum_lead_time(starts_at):
        raise HTTPException(status_code=422, detail="La cita debe reservarse con al menos 3 horas de anticipación")
    if not validate_opening_hours(starts_at, service.duration_minutes):
        raise HTTPException(status_code=422, detail="El horario está fuera del horario del club")

    # MVP local: serializa check+insert para hacer visible la regla RF-055.
    # En producción debe reforzarse con locking/constraints transaccionales en PostgreSQL.
    with reservation_lock:
        if has_conflict(db, starts_at, ends_at, payload.therapist_ids, cabin_id):
            raise HTTPException(status_code=409, detail="El terapeuta o la cabina ya están ocupados")

        reservation = Reservation(
            id=str(uuid.uuid4()),
            customer_id=payload.customer_id,
            service_id=service.id,
            therapist_ids_json=json.dumps(payload.therapist_ids),
            starts_at=starts_at,
            ends_at=ends_at,
            cabin_id=cabin_id,
            source=payload.source or "web",
            status="PENDING_PAYMENT",
            deposit_amount=service.deposit,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

    return reservation_payload(reservation)


@app.get("/reservations/{reservation_id}")
def get_reservation(reservation_id: str, db: Session = Depends(get_db)) -> dict:
    reservation = db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reservation_payload(reservation)


@app.patch("/reservations/{reservation_id}/reschedule")
def reschedule_reservation(
    reservation_id: str,
    payload: ReservationReschedule,
    db: Session = Depends(get_db),
) -> dict:
    reservation = db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    current_start = ensure_tz(reservation.starts_at)
    now = datetime.now(TZ)
    if current_start - now < timedelta(hours=5):
        raise HTTPException(status_code=422, detail="Con menos de 5 horas el anticipo se pierde")

    service = db.get(Service, reservation.service_id)
    if not service:
        raise HTTPException(status_code=500, detail="Servicio de la reserva no existe")

    new_start = parse_iso_datetime(payload.starts_at)
    new_end = new_start + timedelta(minutes=service.duration_minutes)
    therapist_ids = json.loads(reservation.therapist_ids_json)

    if not validate_minimum_lead_time(new_start):
        raise HTTPException(status_code=422, detail="La nueva cita debe tener al menos 3 horas de anticipación")
    if has_conflict(db, new_start, new_end, therapist_ids, reservation.cabin_id, reservation.id):
        raise HTTPException(status_code=409, detail="El nuevo horario ya está ocupado")

    reservation.starts_at = new_start
    reservation.ends_at = new_end
    reservation.status = "PENDING_PAYMENT"
    db.commit()
    db.refresh(reservation)
    return reservation_payload(reservation)


@app.get("/admin/agenda")
def admin_agenda(requested_date: date = Query(alias="date"), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Reservation).order_by(Reservation.starts_at)).all()
    filtered = [row for row in rows if ensure_tz(row.starts_at).date() == requested_date]
    return {
        "date": requested_date.isoformat(),
        "items": [reservation_payload(row) for row in filtered],
    }


@app.post("/admin/blocks", status_code=201)
def create_block(payload: ScheduleBlockCreate, db: Session = Depends(get_db)) -> dict:
    starts_at = parse_iso_datetime(payload.starts_at)
    ends_at = parse_iso_datetime(payload.ends_at)
    if ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="El fin debe ser posterior al inicio")
    block = ScheduleBlock(
        id=str(uuid.uuid4()),
        therapist_id=payload.therapist_id,
        cabin_id=payload.cabin_id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=payload.reason,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return {
        "id": block.id,
        "therapistId": block.therapist_id,
        "cabinId": block.cabin_id,
        "startsAt": ensure_tz(block.starts_at).isoformat(),
        "endsAt": ensure_tz(block.ends_at).isoformat(),
        "reason": block.reason,
    }


@app.delete("/admin/blocks/{block_id}", status_code=204)
def delete_block(block_id: str, db: Session = Depends(get_db)) -> None:
    block = db.get(ScheduleBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Bloqueo no encontrado")
    db.delete(block)
    db.commit()
