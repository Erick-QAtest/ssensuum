import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..domain.customers import normalize_email, normalize_phone
from ..domain.errors import ConflictError, NotFoundError, ValidationError
from ..models import Customer
from ..repositories import customers as customers_repo
from ..schemas import CustomerCreate, CustomerUpdate

DUPLICATE_PHONE = "Ya existe un cliente con ese teléfono"


def _clean_phone(value: str) -> str:
    phone = normalize_phone(value)
    if not phone:
        raise ValidationError("El teléfono debe tener 10 dígitos")
    return phone


def _clean_email(value: Optional[str]) -> Optional[str]:
    if value is None or not value.strip():
        return None
    email = normalize_email(value)
    if not email:
        raise ValidationError("El correo no es válido")
    return email


def _clean_first_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ValidationError("El nombre es obligatorio")
    return name


def _save(db: Session, customer: Customer) -> Customer:
    try:
        return customers_repo.save(db, customer)
    except IntegrityError:
        db.rollback()
        raise ConflictError(DUPLICATE_PHONE)


def get_customer(db: Session, customer_id: str) -> Customer:
    customer = customers_repo.get(db, customer_id)
    if not customer:
        raise NotFoundError("Cliente no encontrado")
    return customer


def search_customers(db: Session, query: Optional[str], limit: int, offset: int) -> list[Customer]:
    text = (query or "").strip()
    # Permite buscar por teléfono aunque venga con espacios, guiones o +52.
    phone = normalize_phone(text)
    return customers_repo.search(db, phone or text or None, limit, offset)


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    phone = _clean_phone(payload.phone)
    if customers_repo.get_by_phone(db, phone):
        raise ConflictError(DUPLICATE_PHONE)
    customer = Customer(
        id=str(uuid.uuid4()),
        phone=phone,
        first_name=_clean_first_name(payload.first_name),
        last_name=payload.last_name.strip(),
        email=_clean_email(payload.email),
        birthday=payload.birthday.isoformat() if payload.birthday else None,
    )
    return _save(db, customer)


def update_customer(db: Session, customer_id: str, payload: CustomerUpdate) -> Customer:
    customer = get_customer(db, customer_id)
    changes = payload.model_dump(exclude_unset=True)

    if "phone" in changes:
        if changes["phone"] is None:
            raise ValidationError("El teléfono debe tener 10 dígitos")
        phone = _clean_phone(changes["phone"])
        existing = customers_repo.get_by_phone(db, phone)
        if existing and existing.id != customer.id:
            raise ConflictError(DUPLICATE_PHONE)
        customer.phone = phone
    if "first_name" in changes:
        customer.first_name = _clean_first_name(changes["first_name"] or "")
    if "last_name" in changes:
        customer.last_name = (changes["last_name"] or "").strip()
    if "email" in changes:
        customer.email = _clean_email(changes["email"])
    if "birthday" in changes:
        customer.birthday = changes["birthday"].isoformat() if changes["birthday"] else None

    return _save(db, customer)
