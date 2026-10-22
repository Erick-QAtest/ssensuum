from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    customer_id: Optional[str] = Field(default=None, alias="customerId")
    service_id: str = Field(alias="serviceId")
    therapist_ids: list[str] = Field(alias="therapistIds")
    starts_at: str = Field(alias="startsAt")
    cabin_id: Optional[str] = Field(default=None, alias="cabinId")
    source: Optional[str] = "web"

    model_config = {"populate_by_name": True}


class ReservationReschedule(BaseModel):
    starts_at: str = Field(alias="startsAt")

    model_config = {"populate_by_name": True}


class ScheduleBlockCreate(BaseModel):
    therapist_id: Optional[str] = Field(default=None, alias="therapistId")
    cabin_id: Optional[str] = Field(default=None, alias="cabinId")
    starts_at: str = Field(alias="startsAt")
    ends_at: str = Field(alias="endsAt")
    reason: str

    model_config = {"populate_by_name": True}


class CustomerCreate(BaseModel):
    phone: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(default="", alias="lastName")
    email: Optional[str] = None
    birthday: Optional[date] = None
    membership_expires_on: Optional[date] = Field(default=None, alias="membershipExpiresOn")
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}


class CustomerUpdate(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    email: Optional[str] = None
    birthday: Optional[date] = None
    membership_expires_on: Optional[date] = Field(default=None, alias="membershipExpiresOn")
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}


class CheckoutCreate(BaseModel):
    service_id: str = Field(alias="serviceId")
    # Vacío = sin preferencia: se asigna terapeuta disponible.
    therapist_ids: list[str] = Field(default_factory=list, alias="therapistIds")
    starts_at: str = Field(alias="startsAt")
    first_name: str = Field(alias="firstName")
    phone: str

    model_config = {"populate_by_name": True}


class SiteEventCreate(BaseModel):
    name: str
    label: str = Field(default="", max_length=120)


class TipEntry(BaseModel):
    therapist_id: str = Field(alias="therapistId")
    amount: int = Field(ge=0)

    model_config = {"populate_by_name": True}


class StaffProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, alias="fullName", max_length=200)
    phone: Optional[str] = None
    email: Optional[str] = None
    birthday: Optional[date] = None
    hired_on: Optional[date] = Field(default=None, alias="hiredOn")
    emergency_contact: Optional[str] = Field(default=None, alias="emergencyContact", max_length=200)
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}


class PayoutUpdate(BaseModel):
    record_id: str = Field(alias="recordId")
    therapist_id: str = Field(alias="therapistId")
    paid: bool

    model_config = {"populate_by_name": True}


class FinanceMovementCreate(BaseModel):
    day: date
    kind: str
    category: Optional[str] = None
    description: str = Field(max_length=200)
    amount: int = Field(gt=0)
    account: str
    to_account: Optional[str] = Field(default=None, alias="toAccount")

    model_config = {"populate_by_name": True}


class RecurringExpenseCreate(BaseModel):
    description: str = Field(max_length=200)
    category: str
    amount: int = Field(gt=0)
    account: str
    day_of_month: int = Field(alias="dayOfMonth", ge=1, le=31)
    start_month: str = Field(alias="startMonth", pattern=r"^\d{4}-(0[1-9]|1[0-2])$")

    model_config = {"populate_by_name": True}


class ServiceRecordCreate(BaseModel):
    customer_name: str = Field(alias="customerName", max_length=200)
    customer_phone: str = Field(alias="customerPhone")
    service_id: str = Field(alias="serviceId")
    therapist_ids: list[str] = Field(alias="therapistIds")
    paid_at: str = Field(alias="paidAt")
    amount: int = Field(ge=0)
    payment_method: str = Field(alias="paymentMethod")
    tips: list[TipEntry] = Field(default_factory=list)
    tip_method: Optional[str] = Field(default=None, alias="tipMethod")
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}
