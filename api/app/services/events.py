from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..domain.errors import ValidationError
from ..domain.marketing import normalize_channel
from ..models import SiteEvent
from ..repositories import events as events_repo
from ..schemas import SiteEventCreate

EVENT_NAMES = {"page_view", "reserve_click", "booking_summary", "checkout_start", "whatsapp_click"}


def record(db: Session, payload: SiteEventCreate) -> None:
    if payload.name not in EVENT_NAMES:
        raise ValidationError("Evento no reconocido")
    events_repo.add(db, SiteEvent(name=payload.name, label=payload.label.strip(), channel=normalize_channel(payload.channel)))


def summary(db: Session, days: int) -> dict:
    # created_at se guarda en UTC (datetime.utcnow), así que el corte también.
    since = datetime.utcnow() - timedelta(days=days)
    totals: dict[str, dict] = {}
    for name, label, count in events_repo.counts_since(db, since):
        entry = totals.setdefault(name, {"total": 0, "byLabel": {}})
        entry["total"] += count
        entry["byLabel"][label or "-"] = count
    return {"days": days, "events": totals}
