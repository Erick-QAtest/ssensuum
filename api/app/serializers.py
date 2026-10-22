from datetime import timezone
from typing import Optional

from .domain.finance import CASH_ACCOUNTS, EXPENSE_CATEGORIES, MOVEMENT_KINDS, OTHER_INCOME_CATEGORIES
from .domain.hr import DOCUMENT_CATEGORIES
from .domain.rules import ensure_tz, hold_expired
from .models import Customer, FinanceMovement, HrDocument, Reservation, ScheduleBlock, Service, ServiceRecord, StaffProfile, Therapist
from .repositories import records as records_repo
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
        "isNew": bool(therapist.is_new),
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


def record_payload(record: ServiceRecord, therapist_names: dict[str, str]) -> dict:
    ids = records_repo.therapist_ids(record)
    tips = records_repo.tips(record)
    return {
        "id": record.id,
        "customerId": record.customer_id,
        "customerName": record.customer_name,
        "customerPhone": record.customer_phone,
        "serviceId": record.service_id,
        "serviceName": record.service_name,
        "therapistIds": ids,
        "therapistNames": [therapist_names.get(tid, tid) for tid in ids],
        "paidAt": ensure_tz(record.paid_at).isoformat(),
        "amount": record.amount,
        "paymentMethod": record.payment_method,
        "tips": tips,
        "tipTotal": sum(tip["amount"] for tip in tips),
        "tipMethod": record.tip_method,
        "notes": record.notes,
        "createdAt": record.created_at.isoformat(),
    }


def staff_payload(therapist: Therapist, profile: Optional[StaffProfile], documents: int, missing: list[str]) -> dict:
    return {
        **therapist_payload(therapist),
        "active": therapist.active,
        "fullName": profile.full_name if profile else None,
        "phone": profile.phone if profile else None,
        "email": profile.email if profile else None,
        "birthday": profile.birthday if profile else None,
        "hiredOn": profile.hired_on if profile else None,
        "emergencyContact": profile.emergency_contact if profile else None,
        "notes": profile.notes if profile else None,
        "documents": documents,
        "missingDocuments": [{"category": category, "label": DOCUMENT_CATEGORIES[category]} for category in missing],
        "documentationComplete": not missing,
    }


def hr_document_payload(document: HrDocument) -> dict:
    return {
        "id": document.id,
        "therapistId": document.therapist_id,
        "category": document.category,
        "categoryLabel": DOCUMENT_CATEGORIES.get(document.category, document.category),
        "title": document.title,
        "fileName": document.file_name,
        "contentType": document.content_type,
        "sizeBytes": document.size_bytes,
        # Se guarda en UTC; SQLite pierde la zona horaria al leerla de vuelta.
        "uploadedAt": ensure_tz(document.uploaded_at.replace(tzinfo=document.uploaded_at.tzinfo or timezone.utc)).isoformat(),
    }


def finance_movement_payload(movement: FinanceMovement) -> dict:
    categories = EXPENSE_CATEGORIES if movement.kind == "gasto" else OTHER_INCOME_CATEGORIES
    return {
        "id": movement.id,
        "day": movement.day,
        "kind": movement.kind,
        "kindLabel": MOVEMENT_KINDS[movement.kind][0],
        "category": movement.category,
        "categoryLabel": categories.get(movement.category) if movement.category else None,
        "description": movement.description,
        "amount": movement.amount,
        "account": movement.account,
        "accountLabel": CASH_ACCOUNTS[movement.account],
        "toAccount": movement.to_account,
        "toAccountLabel": CASH_ACCOUNTS.get(movement.to_account) if movement.to_account else None,
    }
