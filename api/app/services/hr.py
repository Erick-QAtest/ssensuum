import io
import os
import tempfile
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from ..config import settings
from ..domain.customers import normalize_email, normalize_phone
from ..domain.errors import ConflictError, NotFoundError, ValidationError
from ..domain.hr import (
    DOCUMENT_CATEGORIES,
    MAX_DOCUMENT_BYTES,
    MAX_PHOTO_BYTES,
    REQUIRED_DOCUMENTS,
    TEMPLATE_CATEGORY,
    clean_file_name,
    content_type_for,
    extension,
    folder_name,
    photo_extension,
    therapist_slug,
)
from ..domain import schedule as schedule_rules
from ..domain.rules import TZ, ensure_tz
from ..models import HrDocument, Reservation, StaffProfile, Therapist
from ..repositories import catalog as catalog_repo
from ..repositories import customers as customers_repo
from ..repositories import hr as hr_repo
from ..repositories import reservations as reservations_repo
from ..schemas import StaffLeave, StaffProfileUpdate, StaffSchedule, StaffVacation
from . import payroll as payroll_service


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


def _member(db: Session, therapist: Therapist) -> dict:
    return {
        "therapist": therapist,
        "profile": hr_repo.get_profile(db, therapist.id),
        "documents": hr_repo.document_counts(db).get(therapist.id, 0),
        "missing": missing_documents(hr_repo.categories_by_therapist(db).get(therapist.id, set())),
    }


def _apply_profile(profile: StaffProfile, payload: StaffProfileUpdate) -> None:
    """Valida y copia los datos del expediente; lanza ValidationError antes de tocar nada."""
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

    profile.full_name = " ".join((payload.full_name or "").split()) or None
    profile.phone = phone
    profile.email = email
    profile.birthday = payload.birthday.isoformat() if payload.birthday else None
    profile.hired_on = payload.hired_on.isoformat() if payload.hired_on else None
    profile.emergency_contact = (payload.emergency_contact or "").strip() or None
    profile.notes = (payload.notes or "").strip() or None
    profile.updated_at = datetime.now(timezone.utc)


def _apply_public(therapist: Therapist, payload: StaffProfileUpdate) -> None:
    if payload.name is not None:
        name = " ".join(payload.name.split())
        if not name:
            raise ValidationError("Escribe el nombre con el que aparece en el sitio")
        therapist.name = name
    if payload.strengths is not None:
        therapist.strengths = " · ".join(part.strip() for part in payload.strengths.replace("·", ",").split(",") if part.strip())
    if payload.bio is not None:
        therapist.bio = " ".join(payload.bio.split()) or None


def update_profile(db: Session, therapist_id: str, payload: StaffProfileUpdate) -> dict:
    therapist = _therapist(db, therapist_id)
    profile = hr_repo.get_profile(db, therapist_id) or StaffProfile(therapist_id=therapist_id)
    _apply_public(therapist, payload)
    _apply_profile(profile, payload)
    db.add(therapist)
    hr_repo.save(db, profile)
    return _member(db, therapist)


def set_schedule(db: Session, therapist_id: str, payload: StaffSchedule) -> dict:
    therapist = _therapist(db, therapist_id)
    therapist.schedule_json = schedule_rules.dump(schedule_rules.normalize(payload.model_dump()))
    hr_repo.save(db, therapist)
    return _member(db, therapist)


def set_vacation(db: Session, therapist_id: str, payload: StaffVacation) -> dict:
    therapist = _therapist(db, therapist_id)
    if not therapist.active:
        raise ConflictError(f"{therapist.name} está de baja")
    if payload.returns_on and payload.returns_on <= payload.starts_on:
        raise ValidationError("El regreso debe ser después del inicio de las vacaciones")
    start, until = payload.starts_on.isoformat(), payload.returns_on.isoformat() if payload.returns_on else None
    clashes = [
        row for row in upcoming_reservations(db, therapist_id)
        if schedule_rules.on_vacation(start, until, ensure_tz(row.starts_at).date())
    ]
    if clashes and not payload.reservations_handled:
        count = "1 reserva" if len(clashes) == 1 else f"{len(clashes)} reservas"
        raise ConflictError(f"{therapist.name} tiene {count} durante sus vacaciones: avisa a esos clientes primero")
    therapist.vacation_from, therapist.vacation_until = start, until
    hr_repo.save(db, therapist)
    return _member(db, therapist)


def end_vacation(db: Session, therapist_id: str) -> dict:
    therapist = _therapist(db, therapist_id)
    therapist.vacation_from = therapist.vacation_until = None
    hr_repo.save(db, therapist)
    return _member(db, therapist)


def photos_dir() -> Path:
    path = Path(settings.team_photos_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def photo_path(therapist_id: str) -> Optional[Path]:
    # El id llega de la URL: solo se aceptan ids con forma de slug para que el patrón no se salga de la carpeta.
    if therapist_slug(therapist_id) != therapist_id:
        return None
    for candidate in photos_dir().glob(f"{therapist_id}.*"):
        return candidate
    return None


def _check_photo(content: bytes) -> str:
    if not content:
        raise ValidationError("Toma o elige la foto del masajista")
    if len(content) > MAX_PHOTO_BYTES:
        raise ValidationError("La foto pesa más de 5 MB")
    suffix = photo_extension(content)
    if not suffix:
        raise ValidationError("La foto debe ser JPG, PNG o WebP")
    return suffix


def _store_photo(therapist: Therapist, content: bytes, suffix: str) -> None:
    for old in photos_dir().glob(f"{therapist.id}.*"):
        old.unlink(missing_ok=True)
    (photos_dir() / f"{therapist.id}{suffix}").write_bytes(content)
    # La versión en la URL obliga a los navegadores a dejar la foto anterior.
    therapist.photo_url = f"/therapists/{therapist.id}/photo?v={int(datetime.now(timezone.utc).timestamp())}"


def set_photo(db: Session, therapist_id: str, content: bytes) -> dict:
    therapist = _therapist(db, therapist_id)
    _store_photo(therapist, content, _check_photo(content))
    hr_repo.save(db, therapist)
    return _member(db, therapist)


def hire(db: Session, payload: StaffProfileUpdate, photo: bytes) -> dict:
    """Alta completa: perfil público, foto y expediente. Queda activo y visible en el sitio y en las reservas."""
    name = " ".join((payload.name or "").split())
    if not name:
        raise ValidationError("Escribe el nombre con el que aparece en el sitio")
    slug = therapist_slug(name)
    if not slug:
        raise ValidationError("El nombre debe tener al menos una letra o número")
    for row in hr_repo.list_therapists(db):
        if therapist_slug(row.name) == slug:
            state = "activo" if row.active else "de baja: reactívalo desde la lista"
            raise ConflictError(f"{row.name} ya está en el equipo ({state})")
    suffix = _check_photo(photo)

    therapist_id, copy = slug, 2
    while hr_repo.get_therapist(db, therapist_id):
        therapist_id, copy = f"{slug}-{copy}", copy + 1
    therapist = Therapist(id=therapist_id, name=name, strengths="", photo_url="", is_new=True, active=True)
    profile = StaffProfile(therapist_id=therapist_id)
    _apply_public(therapist, payload)
    _apply_profile(profile, payload)
    _store_photo(therapist, photo, suffix)
    db.add(therapist)
    hr_repo.save(db, profile)
    return _member(db, therapist)


def upcoming_reservations(db: Session, therapist_id: str) -> list[Reservation]:
    now = datetime.now(TZ)
    rows = reservations_repo.list_active_starting_between(db, now, now + timedelta(days=3650))
    return sorted((row for row in rows if therapist_id in reservations_repo.therapist_ids(row)), key=lambda row: row.starts_at)


def offboarding(db: Session, therapist_id: str) -> dict:
    """Lo que hay que resolver antes de dar de baja: reservas por atender y pagos por hacerle."""
    _therapist(db, therapist_id)
    services = {row.id: row.name for row in catalog_repo.list_active_services(db)}
    reservations = []
    for row in upcoming_reservations(db, therapist_id):
        customer = customers_repo.get(db, row.customer_id) if row.customer_id else None
        reservations.append({
            "id": row.id,
            "startsAt": ensure_tz(row.starts_at).isoformat(),
            "serviceName": services.get(row.service_id, row.service_id),
            "customerName": " ".join(filter(None, [customer.first_name, customer.last_name])) if customer else None,
        })
    payouts = [line for line in payroll_service.pending_payouts(db) if line["therapistId"] == therapist_id]
    return {
        "upcomingReservations": reservations,
        "pendingPayouts": len(payouts),
        "pendingAmount": sum(line["pay"] for line in payouts),
    }


def leave(db: Session, therapist_id: str, payload: StaffLeave) -> dict:
    therapist = _therapist(db, therapist_id)
    if not therapist.active:
        raise ConflictError(f"{therapist.name} ya está de baja")
    upcoming = upcoming_reservations(db, therapist_id)
    if upcoming and not payload.reservations_handled:
        count = "1 reserva próxima" if len(upcoming) == 1 else f"{len(upcoming)} reservas próximas"
        raise ConflictError(f"{therapist.name} tiene {count}: avisa a esos clientes antes de darlo de baja")
    profile = hr_repo.get_profile(db, therapist_id) or StaffProfile(therapist_id=therapist_id)
    profile.left_on = payload.left_on.isoformat()
    profile.leave_reason = " ".join((payload.reason or "").split()) or None
    profile.updated_at = datetime.now(timezone.utc)
    therapist.active = False
    db.add(therapist)
    hr_repo.save(db, profile)
    return _member(db, therapist)


def rehire(db: Session, therapist_id: str) -> dict:
    therapist = _therapist(db, therapist_id)
    profile = hr_repo.get_profile(db, therapist_id)
    if profile:
        profile.left_on = None
        profile.leave_reason = None
        profile.updated_at = datetime.now(timezone.utc)
        db.add(profile)
    therapist.active = True
    hr_repo.save(db, therapist)
    return _member(db, therapist)


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
