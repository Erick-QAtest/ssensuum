from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ChannelSnapshot, MarketingIdea, MarketingPost


def list_posts(db: Session, start: date, end: date) -> list[MarketingPost]:
    statement = (
        select(MarketingPost)
        .where(MarketingPost.publish_on >= start.isoformat(), MarketingPost.publish_on <= end.isoformat())
        .order_by(MarketingPost.publish_on, MarketingPost.created_at)
    )
    return list(db.scalars(statement).all())


def get_post(db: Session, post_id: str) -> Optional[MarketingPost]:
    return db.get(MarketingPost, post_id)


def posts_per_idea(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {}
    for idea_id in db.scalars(select(MarketingPost.idea_id).where(MarketingPost.idea_id.is_not(None))).all():
        counts[idea_id] = counts.get(idea_id, 0) + 1
    return counts


def list_ideas(db: Session) -> list[MarketingIdea]:
    return list(db.scalars(select(MarketingIdea).order_by(MarketingIdea.pillar, MarketingIdea.created_at.desc())).all())


def get_idea(db: Session, idea_id: str) -> Optional[MarketingIdea]:
    return db.get(MarketingIdea, idea_id)


def list_snapshots(db: Session) -> list[ChannelSnapshot]:
    return list(db.scalars(select(ChannelSnapshot).order_by(ChannelSnapshot.channel, ChannelSnapshot.day)).all())


def get_snapshot(db: Session, snapshot_id: str) -> Optional[ChannelSnapshot]:
    return db.get(ChannelSnapshot, snapshot_id)


def find_snapshot(db: Session, channel: str, day: str) -> Optional[ChannelSnapshot]:
    return db.scalar(select(ChannelSnapshot).where(ChannelSnapshot.channel == channel, ChannelSnapshot.day == day))


def save(db: Session, row):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete(db: Session, row) -> None:
    db.delete(row)
    db.commit()
