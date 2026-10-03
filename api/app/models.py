from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    public_price: Mapped[int] = mapped_column(Integer, nullable=False)
    member_price: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit: Mapped[int] = mapped_column(Integer, nullable=False)
    therapists_required: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Therapist(Base):
    __tablename__ = "therapists"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    strengths: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    birthday: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    service_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    therapist_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cabin_id: Mapped[str] = mapped_column(String(80), nullable=False, default="cabin-1")
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="web")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING_PAYMENT")
    deposit_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    therapist_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    cabin_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(250), nullable=False)
