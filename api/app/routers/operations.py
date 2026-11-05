from datetime import date

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..domain import operations as ops
from ..domain.errors import NotFoundError
from ..domain.hr import MAX_PHOTO_BYTES
from ..schemas import OpsCheckInput, OpsCountInput, OpsPointInput, OpsReceiveInput, OpsSupplyInput
from ..services import operations as ops_service

# Bajo /admin para que nginx lo proteja con el usuario y contraseña de administración.
router = APIRouter(prefix="/admin/ops", tags=["operación"])


@router.get("/meta")
def meta() -> dict:
    return {
        "pointKinds": [{"id": key, "label": label} for key, label in ops.POINT_KINDS.items()],
        "today": ops_service.today().isoformat(),
    }


@router.get("/zones")
def list_zones(db: Session = Depends(get_db)) -> list[dict]:
    return ops_service.zones_overview(db)


@router.put("/zones/{zone_id}/photo")
def upload_photo(zone_id: str, photo: UploadFile = File(...), db: Session = Depends(get_db)) -> list[dict]:
    ops_service.set_photo(db, zone_id, photo.file.read(MAX_PHOTO_BYTES + 1))
    return ops_service.zones_overview(db)


@router.get("/zones/{zone_id}/photo")
def zone_photo(zone_id: str) -> FileResponse:
    path = ops_service.photo_path(zone_id)
    if not path:
        raise NotFoundError("Foto no encontrada")
    # Privada: la URL cambia de versión (?v=) al subir otra foto.
    return FileResponse(path, headers={"Cache-Control": "private, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff"})


@router.post("/zones/{zone_id}/points", status_code=201)
def add_point(zone_id: str, payload: OpsPointInput, db: Session = Depends(get_db)) -> list[dict]:
    ops_service.add_point(db, zone_id, payload.x, payload.y, payload.kind, payload.label)
    return ops_service.zones_overview(db)


@router.delete("/points/{point_id}")
def delete_point(point_id: str, db: Session = Depends(get_db)) -> list[dict]:
    ops_service.delete_point(db, point_id)
    return ops_service.zones_overview(db)


@router.get("/days/{day}")
def get_day(day: date, db: Session = Depends(get_db)) -> dict:
    return ops_service.day_overview(db, day)


@router.post("/days/{day}/checks")
def check(day: date, payload: OpsCheckInput, db: Session = Depends(get_db)) -> dict:
    return ops_service.check(db, day, payload.item_key, payload.status, payload.reason)


@router.delete("/days/{day}/checks/{item_key}")
def uncheck(day: date, item_key: str, db: Session = Depends(get_db)) -> dict:
    return ops_service.uncheck(db, day, item_key)


@router.post("/days/{day}/close")
def close(day: date, db: Session = Depends(get_db)) -> dict:
    return ops_service.close_day(db, day)


@router.post("/days/{day}/reopen")
def reopen(day: date, db: Session = Depends(get_db)) -> dict:
    return ops_service.reopen_day(db, day)


@router.get("/supplies")
def list_supplies(db: Session = Depends(get_db)) -> list[dict]:
    return ops_service.supplies_overview(db)


@router.post("/supplies", status_code=201)
def create_supply(payload: OpsSupplyInput, db: Session = Depends(get_db)) -> list[dict]:
    return ops_service.save_supply(db, None, payload)


@router.put("/supplies/{supply_id}")
def update_supply(supply_id: str, payload: OpsSupplyInput, db: Session = Depends(get_db)) -> list[dict]:
    return ops_service.save_supply(db, supply_id, payload)


@router.post("/supplies/count")
def count_supplies(payload: OpsCountInput, db: Session = Depends(get_db)) -> list[dict]:
    return ops_service.count_supplies(db, payload.counts)


@router.post("/supplies/{supply_id}/receive")
def receive_supply(supply_id: str, payload: OpsReceiveInput, db: Session = Depends(get_db)) -> list[dict]:
    return ops_service.receive_supply(db, supply_id, payload.quantity)
