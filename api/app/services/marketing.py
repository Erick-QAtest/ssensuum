import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..domain import marketing
from ..domain.errors import NotFoundError, ValidationError
from ..domain.rules import TZ, ensure_tz
from ..models import ChannelSnapshot, MarketingIdea, MarketingPost
from ..repositories import events as events_repo
from ..repositories import marketing as marketing_repo
from ..schemas import ChannelSnapshotCreate, MarketingIdeaCreate, MarketingPostCreate
from . import customers as customers_service


def meta() -> dict:
    def options(values: dict) -> list[dict]:
        return [{"id": key, "label": label} for key, label in values.items()]

    return {
        "channels": options(marketing.SOCIAL_CHANNELS),
        "sources": options(marketing.SOURCES),
        "statuses": options(marketing.POST_STATUSES),
        "formats": options(marketing.POST_FORMATS),
        "pillars": options(marketing.PILLARS),
        "metrics": options(marketing.METRICS),
    }


def attribution(db: Session, days: int) -> dict:
    today = datetime.now(TZ).date()
    since = today - timedelta(days=days - 1)
    # created_at de los eventos se guarda en UTC (datetime.utcnow), así que el corte también.
    events_since = datetime.utcnow() - timedelta(days=days)
    touches = [
        marketing.CustomerTouch(
            source=customer.acquisition_source,
            created_on=ensure_tz(customer.created_at).date() if customer.created_at else today,
            stage=summary["stage"],
            visits=summary["visits"],
        )
        for customer, summary in customers_service.summaries(db)
    ]
    rows = marketing.attribution(events_repo.counts_by_channel_since(db, events_since), touches, since)
    return {"days": days, "from": since.isoformat(), "rows": rows}


# --- Calendario ---


def _clean_text(value: Optional[str]) -> Optional[str]:
    return (value or "").strip() or None


def _apply_post(db: Session, post: MarketingPost, payload: MarketingPostCreate) -> MarketingPost:
    if payload.channel not in marketing.SOCIAL_CHANNELS:
        raise ValidationError("Elige Instagram, TikTok, X o Facebook")
    if payload.status not in marketing.POST_STATUSES:
        raise ValidationError("Estado no reconocido")
    if payload.format not in marketing.POST_FORMATS:
        raise ValidationError("Formato no reconocido")
    if payload.pillar and payload.pillar not in marketing.PILLARS:
        raise ValidationError("Pilar no reconocido")
    title = " ".join(payload.title.split())
    if not title:
        raise ValidationError("Escribe de qué trata la publicación")
    url = _clean_text(payload.url)
    if url and not url.startswith(("http://", "https://")):
        raise ValidationError("El enlace debe empezar con https://")
    if payload.idea_id and not marketing_repo.get_idea(db, payload.idea_id):
        raise ValidationError("Idea no encontrada")

    post.channel = payload.channel
    post.publish_on = payload.publish_on.isoformat()
    post.status = payload.status
    post.format = payload.format
    post.pillar = payload.pillar or None
    post.title = title
    post.caption = _clean_text(payload.caption)
    post.url = url
    post.idea_id = payload.idea_id or None
    return marketing_repo.save(db, post)


def get_post(db: Session, post_id: str) -> MarketingPost:
    post = marketing_repo.get_post(db, post_id)
    if not post:
        raise NotFoundError("Publicación no encontrada")
    return post


def list_posts(db: Session, start: date, end: date) -> list[MarketingPost]:
    if end < start:
        raise ValidationError("El periodo no es válido")
    return marketing_repo.list_posts(db, start, end)


def create_post(db: Session, payload: MarketingPostCreate) -> MarketingPost:
    return _apply_post(db, MarketingPost(id=str(uuid.uuid4())), payload)


def update_post(db: Session, post_id: str, payload: MarketingPostCreate) -> MarketingPost:
    return _apply_post(db, get_post(db, post_id), payload)


def delete_post(db: Session, post_id: str) -> None:
    marketing_repo.delete(db, get_post(db, post_id))


# --- Ideas ---


def list_ideas(db: Session) -> list[tuple[MarketingIdea, int]]:
    used = marketing_repo.posts_per_idea(db)
    return [(idea, used.get(idea.id, 0)) for idea in marketing_repo.list_ideas(db)]


def create_idea(db: Session, payload: MarketingIdeaCreate) -> MarketingIdea:
    if payload.pillar not in marketing.PILLARS:
        raise ValidationError("Pilar no reconocido")
    hook = " ".join(payload.hook.split())
    if not hook:
        raise ValidationError("Escribe la idea o el gancho")
    return marketing_repo.save(db, MarketingIdea(id=str(uuid.uuid4()), pillar=payload.pillar, hook=hook, notes=_clean_text(payload.notes)))


def delete_idea(db: Session, idea_id: str) -> None:
    idea = marketing_repo.get_idea(db, idea_id)
    if not idea:
        raise NotFoundError("Idea no encontrada")
    marketing_repo.delete(db, idea)


# --- Métricas ---


def save_snapshot(db: Session, payload: ChannelSnapshotCreate) -> ChannelSnapshot:
    """Una captura por red y día: capturar de nuevo el mismo día la corrige."""
    if payload.channel not in marketing.SOCIAL_CHANNELS:
        raise ValidationError("Elige Instagram, TikTok, X o Facebook")
    if payload.day > datetime.now(TZ).date():
        raise ValidationError("La fecha no puede ser futura")
    values = {metric: getattr(payload, metric) for metric in marketing.METRICS}
    if all(value is None for value in values.values()):
        raise ValidationError("Captura al menos una métrica")
    day = payload.day.isoformat()
    snapshot = marketing_repo.find_snapshot(db, payload.channel, day) or ChannelSnapshot(id=str(uuid.uuid4()), channel=payload.channel, day=day)
    for metric, value in values.items():
        setattr(snapshot, metric, value)
    return marketing_repo.save(db, snapshot)


def metrics_by_channel(db: Session) -> list[dict]:
    """Capturas de cada red, de la más reciente a la más antigua, con el cambio contra la anterior."""
    by_channel: dict[str, list[dict]] = {channel: [] for channel in marketing.SOCIAL_CHANNELS}
    for snapshot in marketing_repo.list_snapshots(db):
        by_channel.setdefault(snapshot.channel, []).append({
            "id": snapshot.id,
            "day": snapshot.day,
            **{metric: getattr(snapshot, metric) for metric in marketing.METRICS},
        })
    return [
        {
            "channel": channel,
            "label": marketing.SOCIAL_CHANNELS.get(channel, channel),
            "snapshots": list(reversed(marketing.metric_changes(rows))),
        }
        for channel, rows in by_channel.items()
    ]


def delete_snapshot(db: Session, snapshot_id: str) -> None:
    snapshot = marketing_repo.get_snapshot(db, snapshot_id)
    if not snapshot:
        raise NotFoundError("Captura no encontrada")
    marketing_repo.delete(db, snapshot)
