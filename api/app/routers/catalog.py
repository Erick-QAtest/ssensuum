from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..domain.errors import NotFoundError
from ..repositories import catalog as catalog_repo
from ..serializers import service_payload, therapist_payload
from ..services import hr as hr_service

router = APIRouter(tags=["catalog"])


@router.get("/services")
def services(db: Session = Depends(get_db)) -> list[dict]:
    return [service_payload(row) for row in catalog_repo.list_active_services(db)]


@router.get("/therapists")
def therapists(db: Session = Depends(get_db)) -> list[dict]:
    return [therapist_payload(row) for row in catalog_repo.list_active_therapists(db)]


@router.get("/therapists/{therapist_id}/photo")
def therapist_photo(therapist_id: str) -> FileResponse:
    # La URL lleva la versión (?v=), así que el navegador puede guardarla mucho tiempo.
    path = hr_service.photo_path(therapist_id)
    if not path:
        raise NotFoundError("Foto no encontrada")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff"})
