from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Mexico_City")
OPEN_TIME = time(9, 0)
CLOSE_TIME = time(20, 30)
LAST_ONE_HOUR_START = time(19, 30)
SLOT_STEP_MINUTES = 30
MINIMUM_LEAD_TIME = timedelta(hours=3)
RESCHEDULE_CUTOFF = timedelta(hours=5)
DEFAULT_CABIN_ID = "cabin-1"


def ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def parse_iso_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ensure_tz(dt)


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def validate_minimum_lead_time(starts_at: datetime, now: Optional[datetime] = None) -> bool:
    current = ensure_tz(now or datetime.now(TZ))
    return ensure_tz(starts_at) >= current + MINIMUM_LEAD_TIME


def validate_opening_hours(starts_at: datetime, duration_minutes: int) -> bool:
    local = ensure_tz(starts_at)
    day_open = datetime.combine(local.date(), OPEN_TIME, tzinfo=TZ)
    day_close = datetime.combine(local.date(), CLOSE_TIME, tzinfo=TZ)
    return local >= day_open and local + timedelta(minutes=duration_minutes) <= day_close


def can_reschedule(current_start: datetime, now: Optional[datetime] = None) -> bool:
    current = ensure_tz(now or datetime.now(TZ))
    return ensure_tz(current_start) - current >= RESCHEDULE_CUTOFF
