import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..domain.customer_profile import clean_quiz_answers
from ..domain.customers import normalize_phone
from ..domain.marketing import normalize_channel
from ..domain.errors import ConflictError, NotFoundError, PaymentGatewayError, ValidationError
from ..domain.rules import PAYMENT_HOLD, TZ, ensure_tz, hold_expired, parse_iso_datetime
from ..models import Customer, Reservation
from ..repositories import catalog as catalog_repo
from ..repositories import customers as customers_repo
from ..repositories import reservations as reservations_repo
from ..schemas import CheckoutCreate, ReservationCreate
from . import mercadopago
from .customers import set_source_if_missing
from .availability import free_therapists, has_conflict, least_busy_first
from .reservations import create_reservation

# Estados de Mercado Pago que deshacen un pago ya recibido.
REVERSED_PAYMENT_STATUSES = {"refunded", "charged_back", "cancelled"}


def _customer_for(db: Session, first_name: str, raw_phone: str, quiz: Optional[dict] = None, channel: Optional[str] = None) -> Customer:
    phone = normalize_phone(raw_phone)
    if not phone:
        raise ValidationError("El teléfono debe tener 10 dígitos")
    name = first_name.strip()
    if not name:
        raise ValidationError("El nombre es obligatorio")

    customer = customers_repo.get_by_phone(db, phone) or Customer(id=str(uuid.uuid4()), phone=phone, first_name=name)
    if not customer.first_name:
        customer.first_name = name
    answers = clean_quiz_answers(quiz)
    if answers:
        customer.quiz_json = json.dumps(answers)
        customer.quiz_at = datetime.now(TZ)
    set_source_if_missing(customer, normalize_channel(channel))
    return customers_repo.save(db, customer)


def start_checkout(db: Session, payload: CheckoutCreate) -> tuple[Reservation, str]:
    mercadopago.ensure_configured()
    service = catalog_repo.get_service(db, payload.service_id)
    if not service or not service.active:
        raise NotFoundError("Servicio no encontrado")
    customer = _customer_for(db, payload.first_name, payload.phone, payload.quiz, payload.channel)

    therapist_ids = payload.therapist_ids
    if not therapist_ids:
        starts_at = parse_iso_datetime(payload.starts_at)
        ends_at = starts_at + timedelta(minutes=service.duration_minutes)
        candidates = least_busy_first(db, catalog_repo.active_therapist_ids(db), starts_at.date())
        therapist_ids = free_therapists(db, candidates, service.therapists_required, starts_at, ends_at) or []
        if not therapist_ids:
            raise ConflictError("Ese horario se acaba de ocupar. Elige otro, por favor.")

    hold_expires_at = datetime.now(TZ) + PAYMENT_HOLD
    reservation = create_reservation(
        db,
        ReservationCreate(
            customerId=customer.id,
            serviceId=service.id,
            therapistIds=therapist_ids,
            startsAt=payload.starts_at,
            source="web-checkout",
        ),
        hold_expires_at=hold_expires_at,
    )

    try:
        preference = mercadopago.create_preference(
            reservation_id=reservation.id,
            title=f"Anticipo · {service.name}",
            amount=reservation.deposit_amount,
            payer_name=customer.first_name,
            payer_phone=customer.phone,
            expires_at=hold_expires_at,
        )
    except Exception:
        # Sin preferencia de pago no hay forma de pagar: libera el horario de inmediato.
        reservation.status = "CANCELLED"
        reservations_repo.save(db, reservation)
        raise

    return reservation, _checkout_url(preference)


def retry_checkout(db: Session, reservation_id: str) -> tuple[Reservation, str]:
    """Nuevo intento de pago para un apartado vigente (p. ej. tras una tarjeta rechazada)."""
    reservation = reservations_repo.get(db, reservation_id)
    if not reservation:
        raise NotFoundError("Reserva no encontrada")
    if reservation.status != "PENDING_PAYMENT" or hold_expired(reservation.hold_expires_at):
        raise ConflictError("Este apartado ya no está disponible. Elige un horario de nuevo.")
    service = catalog_repo.get_service(db, reservation.service_id)
    customer = customers_repo.get(db, reservation.customer_id or "")
    if not service or not customer:
        raise NotFoundError("Reserva no encontrada")

    reservation.hold_expires_at = datetime.now(TZ) + PAYMENT_HOLD
    reservations_repo.save(db, reservation)
    preference = mercadopago.create_preference(
        reservation_id=reservation.id,
        title=f"Anticipo · {service.name}",
        amount=reservation.deposit_amount,
        payer_name=customer.first_name,
        payer_phone=customer.phone,
        expires_at=ensure_tz(reservation.hold_expires_at),
    )
    return reservation, _checkout_url(preference)


def _checkout_url(preference: dict) -> str:
    checkout_url = preference.get("sandbox_init_point") if mercadopago.is_sandbox() else preference.get("init_point")
    if not checkout_url:
        raise PaymentGatewayError("No pudimos iniciar el pago. Intenta de nuevo en un momento.")
    return checkout_url


def sync_payment(db: Session, payment_id: str) -> Optional[Reservation]:
    """Aplica a la reserva el estado real del pago, consultado directo a Mercado Pago."""
    payment = mercadopago.get_payment(payment_id)
    reservation = reservations_repo.get(db, str(payment.get("external_reference") or ""))
    if not reservation:
        return None

    status = payment.get("status")
    if status == "approved":
        paid_enough = payment.get("currency_id") == "MXN" and float(payment.get("transaction_amount") or 0) >= reservation.deposit_amount
        if reservation.status == "PENDING_PAYMENT" and paid_enough:
            # Si el pago llegó después de vencer el apartado y alguien más tomó el horario,
            # el anticipo queda cobrado pero la cita necesita que el club la resuelva.
            taken = hold_expired(reservation.hold_expires_at) and has_conflict(
                db,
                ensure_tz(reservation.starts_at),
                ensure_tz(reservation.ends_at),
                reservations_repo.therapist_ids(reservation),
                reservation.cabin_id,
                reservation.id,
            )
            reservation.status = "NEEDS_ATTENTION" if taken else "CONFIRMED"
            reservation.hold_expires_at = None
        reservation.payment_id = str(payment_id)
        return reservations_repo.save(db, reservation)

    if status in REVERSED_PAYMENT_STATUSES and reservation.payment_id == str(payment_id):
        reservation.status = "CANCELLED"
        return reservations_repo.save(db, reservation)

    return reservation
