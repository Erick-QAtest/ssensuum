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
