from .domain.rules import ensure_tz, hold_expired
from .models import Customer, Reservation, ScheduleBlock, Service, Therapist
from .repositories.reservations import therapist_ids


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
        "details": service.details,
    }


def therapist_payload(therapist: Therapist) -> dict:
    return {
        "id": therapist.id,
        "name": therapist.name,
        "strengths": therapist.strengths,
        "photoUrl": therapist.photo_url,
        "bio": therapist.bio,
    }


def reservation_payload(reservation: Reservation) -> dict:
    return {
        "id": reservation.id,
        "customerId": reservation.customer_id,
        "serviceId": reservation.service_id,
        "therapistIds": therapist_ids(reservation),
        "startsAt": ensure_tz(reservation.starts_at).isoformat(),
        "endsAt": ensure_tz(reservation.ends_at).isoformat(),
        "cabinId": reservation.cabin_id,
        "source": reservation.source,
        "status": "EXPIRED" if reservation.status == "PENDING_PAYMENT" and hold_expired(reservation.hold_expires_at) else reservation.status,
        "depositAmount": reservation.deposit_amount,
        "holdExpiresAt": ensure_tz(reservation.hold_expires_at).isoformat() if reservation.hold_expires_at else None,
    }


def block_payload(block: ScheduleBlock) -> dict:
    return {
        "id": block.id,
        "therapistId": block.therapist_id,
        "cabinId": block.cabin_id,
        "startsAt": ensure_tz(block.starts_at).isoformat(),
        "endsAt": ensure_tz(block.ends_at).isoformat(),
        "reason": block.reason,
    }


def customer_payload(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "phone": customer.phone,
        "firstName": customer.first_name,
        "lastName": customer.last_name,
        "email": customer.email,
        "birthday": customer.birthday,
        "membershipExpiresOn": customer.membership_expires_on,
        "notes": customer.notes,
        "createdAt": customer.created_at.isoformat(),
    }
