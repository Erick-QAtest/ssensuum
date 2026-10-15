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
