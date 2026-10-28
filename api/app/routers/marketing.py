from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ChannelSnapshotCreate, MarketingIdeaCreate, MarketingPostCreate
from ..serializers import marketing_idea_payload, marketing_post_payload
from ..services import marketing as marketing_service

# Bajo /admin para que nginx lo proteja con el usuario y contraseña de administración.
router = APIRouter(prefix="/admin/marketing", tags=["marketing"])


@router.get("/meta")
def marketing_meta() -> dict:
    return marketing_service.meta()


@router.get("/attribution")
def attribution(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)) -> dict:
    """Visitas, clics y clientes por red de origen."""
    return marketing_service.attribution(db, days)


@router.get("/posts")
def list_posts(start: date = Query(alias="from"), end: date = Query(alias="to"), db: Session = Depends(get_db)) -> list[dict]:
    return [marketing_post_payload(row) for row in marketing_service.list_posts(db, start, end)]


@router.post("/posts", status_code=201)
def create_post(payload: MarketingPostCreate, db: Session = Depends(get_db)) -> dict:
    return marketing_post_payload(marketing_service.create_post(db, payload))


@router.put("/posts/{post_id}")
def update_post(post_id: str, payload: MarketingPostCreate, db: Session = Depends(get_db)) -> dict:
    return marketing_post_payload(marketing_service.update_post(db, post_id, payload))


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: str, db: Session = Depends(get_db)) -> None:
    marketing_service.delete_post(db, post_id)


@router.get("/ideas")
def list_ideas(db: Session = Depends(get_db)) -> list[dict]:
    return [marketing_idea_payload(idea, used) for idea, used in marketing_service.list_ideas(db)]


@router.post("/ideas", status_code=201)
def create_idea(payload: MarketingIdeaCreate, db: Session = Depends(get_db)) -> dict:
    return marketing_idea_payload(marketing_service.create_idea(db, payload), 0)


@router.delete("/ideas/{idea_id}", status_code=204)
def delete_idea(idea_id: str, db: Session = Depends(get_db)) -> None:
    marketing_service.delete_idea(db, idea_id)


@router.get("/metrics")
def list_metrics(db: Session = Depends(get_db)) -> list[dict]:
    return marketing_service.metrics_by_channel(db)


@router.post("/metrics", status_code=201)
def save_metrics(payload: ChannelSnapshotCreate, db: Session = Depends(get_db)) -> list[dict]:
    marketing_service.save_snapshot(db, payload)
    return marketing_service.metrics_by_channel(db)


@router.delete("/metrics/{snapshot_id}", status_code=204)
def delete_metrics(snapshot_id: str, db: Session = Depends(get_db)) -> None:
    marketing_service.delete_snapshot(db, snapshot_id)
