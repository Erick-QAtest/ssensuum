from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Customer


def get(db: Session, customer_id: str) -> Optional[Customer]:
    return db.get(Customer, customer_id)


def get_by_phone(db: Session, phone: str) -> Optional[Customer]:
    return db.scalar(select(Customer).where(Customer.phone == phone))


def search(db: Session, query: Optional[str], limit: Optional[int] = None, offset: int = 0) -> list[Customer]:
    statement = select(Customer)
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Customer.phone.like(pattern),
                Customer.first_name.ilike(pattern),
                Customer.last_name.ilike(pattern),
            )
        )
    statement = statement.order_by(Customer.first_name, Customer.last_name, Customer.id).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


def list_all(db: Session) -> list[Customer]:
    return list(db.scalars(select(Customer)).all())


def save(db: Session, customer: Customer) -> Customer:
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def existing_phones(db: Session) -> set[str]:
    return set(db.scalars(select(Customer.phone)).all())


def save_all(db: Session, customers: list[Customer]) -> None:
    db.add_all(customers)
    db.commit()
