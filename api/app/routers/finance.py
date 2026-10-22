from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import FinanceMovementCreate
from ..serializers import finance_movement_payload
from ..services import finance as finance_service

# Bajo /admin para que nginx lo proteja con el usuario y contraseña de administración.
router = APIRouter(prefix="/admin/finanzas", tags=["finanzas"])


@router.get("/meta")
def finance_meta() -> dict:
    return finance_service.meta()


@router.get("/statements")
def statements(start: date = Query(alias="from"), end: date = Query(alias="to"), db: Session = Depends(get_db)) -> dict:
    """Estado de resultados y flujo de efectivo del periodo, y balance general al cierre."""
    return finance_service.statements(db, start, end)


@router.get("/statements/export")
def export_statements(start: date = Query(alias="from"), end: date = Query(alias="to"), db: Session = Depends(get_db)) -> Response:
    return Response(
        content=finance_service.export_xlsx(db, start, end),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="finanzas-ssensuum-{start.isoformat()}-a-{end.isoformat()}.xlsx"'},
    )


@router.get("/movements")
def list_movements(start: date = Query(alias="from"), end: date = Query(alias="to"), db: Session = Depends(get_db)) -> list[dict]:
    return [finance_movement_payload(row) for row in finance_service.list_movements(db, start, end)]


@router.post("/movements", status_code=201)
def create_movement(payload: FinanceMovementCreate, db: Session = Depends(get_db)) -> dict:
    return finance_movement_payload(finance_service.create_movement(db, payload))


@router.delete("/movements/{movement_id}", status_code=204)
def delete_movement(movement_id: str, db: Session = Depends(get_db)) -> None:
    finance_service.delete_movement(db, movement_id)
