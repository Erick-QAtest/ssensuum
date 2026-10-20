import os
from datetime import date
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from ..db import get_db
from ..domain.hr import MAX_DOCUMENT_BYTES
from ..schemas import PayoutUpdate, StaffProfileUpdate
from ..serializers import hr_document_payload, staff_payload
from ..services import hr as hr_service
from ..services import payroll as payroll_service

# Bajo /admin para que nginx lo proteja con el usuario y contraseña de administración.
router = APIRouter(prefix="/admin/rh", tags=["recursos humanos"])


def _attachment(file_name: str) -> str:
    # filename* conserva acentos; filename queda como respaldo ASCII.
    fallback = file_name.encode("ascii", "replace").decode().replace("?", "_").replace('"', "")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(file_name)}"


@router.get("/staff")
def list_staff(db: Session = Depends(get_db)) -> list[dict]:
    return [staff_payload(**item) for item in hr_service.staff_overview(db)]


@router.get("/staff/export")
def export_staff(db: Session = Depends(get_db)) -> Response:
    return Response(
        content=hr_service.export_staff_xlsx(db),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _attachment(f"equipo-ssensuum-{date.today().isoformat()}.xlsx")},
    )


@router.put("/staff/{therapist_id}")
def update_staff(therapist_id: str, payload: StaffProfileUpdate, db: Session = Depends(get_db)) -> dict:
    return staff_payload(**hr_service.update_profile(db, therapist_id, payload))


@router.get("/documents")
def list_documents(
    therapist_id: Optional[str] = Query(default=None, alias="therapistId"),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [hr_document_payload(row) for row in hr_service.list_documents(db, therapist_id, category)]


@router.post("/documents", status_code=201)
def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    therapist_id: Optional[str] = Form(default=None, alias="therapistId"),
    title: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
) -> dict:
    # Se lee un byte de más para detectar archivos que exceden el límite sin cargarlos completos.
    content = file.file.read(MAX_DOCUMENT_BYTES + 1)
    return hr_document_payload(hr_service.upload_document(db, file.filename or "", content, therapist_id, category, title))


@router.get("/documents/export")
def export_documents(db: Session = Depends(get_db)) -> FileResponse:
    zip_path = hr_service.export_documents_zip(db)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        headers={"Content-Disposition": _attachment(f"documentos-rh-ssensuum-{date.today().isoformat()}.zip")},
        background=BackgroundTask(os.remove, zip_path),
    )


@router.get("/documents/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db)) -> FileResponse:
    document = hr_service.get_document(db, document_id)
    return FileResponse(
        hr_service.document_path(document),
        media_type=document.content_type,
        headers={"Content-Disposition": _attachment(document.file_name), "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> None:
    hr_service.delete_document(db, document_id)


@router.get("/payroll")
def weekly_payroll(day: date = Query(alias="week"), db: Session = Depends(get_db)) -> dict:
    """Liquidación de la semana (lunes a domingo) que contiene ese día."""
    return payroll_service.weekly_payroll(db, day)


@router.get("/payroll/pending")
def pending_payouts(db: Session = Depends(get_db)) -> list[dict]:
    """Pagos a masajistas que siguen pendientes; vencen 48 horas después del servicio."""
    return payroll_service.pending_payouts(db)


@router.put("/payroll/payouts", status_code=204)
def set_payout(payload: PayoutUpdate, db: Session = Depends(get_db)) -> None:
    payroll_service.set_payout(db, payload)


@router.get("/payroll/export")
def export_payroll(day: date = Query(alias="week"), db: Session = Depends(get_db)) -> Response:
    payroll = payroll_service.weekly_payroll(db, day)
    return Response(
        content=payroll_service.export_payroll_xlsx(db, day),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _attachment(f"liquidacion-{payroll['weekStart']}.xlsx")},
    )
