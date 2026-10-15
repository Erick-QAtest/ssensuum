from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..schemas import CheckoutCreate
from ..serializers import reservation_payload
from ..services import checkout as checkout_service

router = APIRouter(tags=["payments"])


@router.get("/payments/status")
def payments_status() -> dict:
    return {"enabled": bool(settings.mp_access_token)}


@router.post("/checkout", status_code=201)
def start_checkout(payload: CheckoutCreate, db: Session = Depends(get_db)) -> dict:
    reservation, checkout_url = checkout_service.start_checkout(db, payload)
    return {"reservation": reservation_payload(reservation), "checkoutUrl": checkout_url}


@router.post("/checkout/{reservation_id}/retry")
def retry_checkout(reservation_id: str, db: Session = Depends(get_db)) -> dict:
    reservation, checkout_url = checkout_service.retry_checkout(db, reservation_id)
    return {"reservation": reservation_payload(reservation), "checkoutUrl": checkout_url}


@router.post("/payments/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    # No se confía en el contenido del aviso: solo se toma el id y se consulta el pago a Mercado Pago.
    params = request.query_params
    try:
        body = await request.json()
    except ValueError:
        body = {}
    kind = params.get("type") or params.get("topic") or body.get("type") or body.get("topic")
    payment_id = params.get("data.id") or params.get("id") or (body.get("data") or {}).get("id")
    if kind == "payment" and payment_id:
        checkout_service.sync_payment(db, str(payment_id))
    return {"received": True}


@router.post("/payments/{payment_id}/sync")
def sync_payment(payment_id: str, db: Session = Depends(get_db)) -> dict:
    reservation = checkout_service.sync_payment(db, payment_id)
    return {"reservation": reservation_payload(reservation) if reservation else None}
