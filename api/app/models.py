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
    # Cómo se realiza el servicio, para quien quiere saber más antes de reservar.
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Therapist(Base):
    __tablename__ = "therapists"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    strengths: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_new: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    birthday: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    membership_expires_on: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    # Mientras la reserva espera su pago, el horario queda apartado solo hasta esta hora.
    hold_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    therapist_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    cabin_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(250), nullable=False)


class SiteEvent(Base):
    """Conteo anónimo de visitas y clics: sin IP, cookies ni datos personales."""

    __tablename__ = "site_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class ServiceRecord(Base):
    """Registro de cada servicio atendido: quién vino, qué se hizo, con quién y cuánto se cobró."""

    __tablename__ = "service_records"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(String(80), nullable=False)
    # Se guarda el nombre tal como estaba al cobrar, por si el catálogo cambia después.
    service_name: Mapped[str] = mapped_column(String(160), nullable=False)
    therapist_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    # [{"therapistId": "...", "amount": 200}]: la propina de cada terapeuta por separado.
    tips_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    tip_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class StaffProfile(Base):
    """Datos de recursos humanos de cada terapeuta. Tabla aparte para que el seed del catálogo no los toque."""

    __tablename__ = "staff_profiles"

    therapist_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    birthday: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    hired_on: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class HrDocument(Base):
    """Archivo del repositorio de recursos humanos; el contenido vive en disco (settings.hr_files_dir)."""

    __tablename__ = "hr_documents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    # Vacío = documento general del equipo, no de un terapeuta en particular.
    therapist_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    stored_name: Mapped[str] = mapped_column(String(80), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class TherapistPayout(Base):
    """Pago a un masajista por un servicio registrado: honorarios y propina, dentro de las 48 horas."""

    __tablename__ = "therapist_payouts"

    record_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    therapist_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    # Lo que se pagó en ese momento, por si el registro del servicio cambia después.
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
