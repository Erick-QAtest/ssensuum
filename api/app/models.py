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
    # Días y horas en que atiende (ver domain/schedule.py); vacío = aún no se captura.
    schedule_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Vacaciones: no se le reserva desde vacation_from hasta el día antes de vacation_until (sin fecha = hasta nuevo aviso).
    vacation_from: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    vacation_until: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)


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
    # Últimas respuestas del quiz ({"presion": "firme", ...}), guardadas al reservar después de hacerlo.
    quiz_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quiz_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Cómo nos conoció (domain/marketing.SOURCES): la primera red registrada, no se sobrescribe sola.
    acquisition_source: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)


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
    # Red de la que llegó la visita (enlace con utm_source o sitio de referencia); no identifica a nadie.
    channel: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)


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
    left_on: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    leave_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
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


class FinanceMovement(Base):
    """Movimiento capturado en Finanzas: gastos, saldos iniciales, aportaciones, retiros, préstamos, equipo y traspasos."""

    __tablename__ = "finance_movements"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    day: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    account: Mapped[str] = mapped_column(String(20), nullable=False)
    to_account: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RecurringExpense(Base):
    """Gasto fijo mensual (renta, internet…): genera un gasto cada mes sin capturarlo."""

    __tablename__ = "recurring_expenses"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    account: Mapped[str] = mapped_column(String(20), nullable=False)
    # Día del mes en que se paga; en meses más cortos se usa el último día.
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False)
    # Primer y último mes que cuentan, "AAAA-MM"; sin último mes sigue vigente.
    start_month: Mapped[str] = mapped_column(String(7), nullable=False)
    end_month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MarketingPost(Base):
    """Publicación planeada o hecha en una red: el calendario de contenido orgánico."""

    __tablename__ = "marketing_posts"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    publish_on: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idea")
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    pillar: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    idea_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MarketingIdea(Base):
    """Idea o gancho reutilizable para publicaciones, agrupado por pilar de contenido."""

    __tablename__ = "marketing_ideas"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    pillar: Mapped[str] = mapped_column(String(20), nullable=False)
    hook: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChannelSnapshot(Base):
    """Métricas de una red capturadas a mano en una fecha (una por red y día)."""

    __tablename__ = "channel_snapshots"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    day: Mapped[str] = mapped_column(String(10), nullable=False)
    followers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interactions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    link_clicks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
