from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..repositories import catalog as catalog_repo
from ..serializers import service_payload, therapist_payload

router = APIRouter(tags=["catalog"])


@router.get("/services")
def services(db: Session = Depends(get_db)) -> list[dict]:
    return [service_payload(row) for row in catalog_repo.list_active_services(db)]


@router.get("/therapists")
def therapists(db: Session = Depends(get_db)) -> list[dict]:
    return [therapist_payload(row) for row in catalog_repo.list_active_therapists(db)]
