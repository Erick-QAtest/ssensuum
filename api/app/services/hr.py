import io
import os
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from ..config import settings
from ..domain.customers import normalize_email, normalize_phone
from ..domain.errors import NotFoundError, ValidationError
from ..domain.hr import (
    DOCUMENT_CATEGORIES,
    MAX_DOCUMENT_BYTES,
    REQUIRED_DOCUMENTS,
    TEMPLATE_CATEGORY,
    clean_file_name,
    content_type_for,
    extension,
    folder_name,
)
from ..models import HrDocument, StaffProfile, Therapist
from ..repositories import hr as hr_repo
from ..schemas import StaffProfileUpdate


def files_dir() -> Path:
    path = Path(settings.hr_files_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def document_path(document: HrDocument) -> Path:
    return files_dir() / document.stored_name


def _therapist(db: Session, therapist_id: str) -> Therapist:
    therapist = hr_repo.get_therapist(db, therapist_id)
    if not therapist:
        raise NotFoundError("Terapeuta no encontrado")
    return therapist


def missing_documents(categories: set[str]) -> list[str]:
    return [category for category in REQUIRED_DOCUMENTS if category not in categories]


def staff_overview(db: Session) -> list[dict]:
    profiles = hr_repo.profiles(db)
    counts = hr_repo.document_counts(db)
    categories = hr_repo.categories_by_therapist(db)
    return [
        {
            "therapist": row,
            "profile": profiles.get(row.id),
            "documents": counts.get(row.id, 0),
            "missing": missing_documents(categories.get(row.id, set())),
        }
        for row in hr_repo.list_therapists(db)
    ]


def update_profile(db: Session, therapist_id: str, payload: StaffProfileUpdate) -> dict:
    therapist = _therapist(db, therapist_id)
    phone = None
    if (payload.phone or "").strip():
        phone = normalize_phone(payload.phone)
        if not phone:
            raise ValidationError("El teléfono debe tener 10 dígitos")
    email = None
    if (payload.email or "").strip():
        email = normalize_email(payload.email)
        if not email:
            raise ValidationError("El correo no es válido")

    profile = hr_repo.get_profile(db, therapist_id) or StaffProfile(therapist_id=therapist_id)
    profile.full_name = " ".join((payload.full_name or "").split()) or None
    profile.phone = phone
    profile.email = email
    profile.birthday = payload.birthday.isoformat() if payload.birthday else None
    profile.hired_on = payload.hired_on.isoformat() if payload.hired_on else None
    profile.emergency_contact = (payload.emergency_contact or "").strip() or None
    profile.notes = (payload.notes or "").strip() or None
    profile.updated_at = datetime.now(timezone.utc)
    hr_repo.save(db, profile)
    return {
        "therapist": therapist,
        "profile": profile,
        "documents": hr_repo.document_counts(db).get(therapist_id, 0),
        "missing": missing_documents(hr_repo.categories_by_therapist(db).get(therapist_id, set())),
    }


def list_documents(db: Session, therapist_id: Optional[str], category: Optional[str] = None) -> list[HrDocument]:
    # Los formatos para firmar tienen su propia sección: el repositorio solo los lista si se piden.
    exclude = None if category else TEMPLATE_CATEGORY
    # "general" filtra los documentos del equipo que no son de nadie en particular.
    if therapist_id == "general":
        return hr_repo.list_documents(db, general_only=True, category=category, exclude_category=exclude)
    return hr_repo.list_documents(db, therapist_id, category=category, exclude_category=exclude)


def get_document(db: Session, document_id: str) -> HrDocument:
    document = hr_repo.get_document(db, document_id)
    if not document:
        raise NotFoundError("Documento no encontrado")
    return document


def upload_document(
    db: Session,
    file_name: str,
    content: bytes,
    therapist_id: Optional[str],
    category: str,
    title: Optional[str],
) -> HrDocument:
    name = clean_file_name(file_name)
    if not name:
        raise ValidationError("Elige un archivo")
    content_type = content_type_for(name)
    if not content_type:
        raise ValidationError("Formato no permitido. Usa PDF, imagen, Word, Excel, CSV o texto")
    if not content:
        raise ValidationError("El archivo está vacío")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise ValidationError("El archivo pesa más de 8 MB")
    if category not in DOCUMENT_CATEGORIES:
        raise ValidationError("Categoría no válida")
    therapist_id = (therapist_id or "").strip() or None
    if therapist_id and category == TEMPLATE_CATEGORY:
        raise ValidationError("Un formato para firmar es para todo el equipo: no lo asignes a un masajista")
    if therapist_id:
        _therapist(db, therapist_id)

    document_id = str(uuid.uuid4())
    document = HrDocument(
        id=document_id,
        therapist_id=therapist_id,
        category=category,
        title=" ".join((title or "").split())[:200] or PurePosixPath(name).stem[:200] or name,
        file_name=name,
        content_type=content_type,
        size_bytes=len(content),
        stored_name=f"{document_id}{extension(name)}",
    )
    path = document_path(document)
    path.write_bytes(content)
    try:
        return hr_repo.save(db, document)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise


def delete_document(db: Session, document_id: str) -> None:
    document = get_document(db, document_id)
    path = document_path(document)
    hr_repo.delete(db, document)
    path.unlink(missing_ok=True)


def export_staff_xlsx(db: Session) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Equipo"
    headers = ["ID", "Nombre", "Nombre completo", "Estado", "Teléfono", "Correo", "Cumpleaños", "Fecha de ingreso",
               "Contacto de emergencia", "Fortalezas", "Documentos", "Documentación", "Notas"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for item in staff_overview(db):
        therapist, profile = item["therapist"], item["profile"]
        sheet.append([
            therapist.id,
            therapist.name,
            profile.full_name if profile else None,
            "Activo" if therapist.active else "Baja",
            profile.phone if profile else None,
            profile.email if profile else None,
            profile.birthday if profile else None,
            profile.hired_on if profile else None,
            profile.emergency_contact if profile else None,
            therapist.strengths or None,
            item["documents"],
            "Completa" if not item["missing"] else "Falta: " + ", ".join(DOCUMENT_CATEGORIES[c] for c in item["missing"]),
            profile.notes if profile else None,
        ])
    for column, header in zip(sheet.columns, headers):
        width = max(len(header), *(len(str(cell.value or "")) for cell in column))
        sheet.column_dimensions[column[0].column_letter].width = min(width + 2, 60)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def export_documents_zip(db: Session) -> str:
    """Escribe un ZIP con todo el repositorio, una carpeta por terapeuta, y devuelve su ruta temporal."""
    names = {row.id: row.name for row in hr_repo.list_therapists(db)}
    handle, zip_path = tempfile.mkstemp(prefix="ssensuum-rh-", suffix=".zip")
    os.close(handle)
    used: set[str] = set()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for document in hr_repo.list_documents(db):
            source = document_path(document)
            if not source.exists():
                continue
            owner = folder_name(names.get(document.therapist_id, "General") if document.therapist_id else "General")
            stem, suffix = PurePosixPath(document.file_name).stem, PurePosixPath(document.file_name).suffix
            target = f"{owner}/{document.category}/{document.file_name}"
            copy = 2
            while target in used:
                target = f"{owner}/{document.category}/{stem} ({copy}){suffix}"
                copy += 1
            used.add(target)
            archive.write(source, target)
    return zip_path
