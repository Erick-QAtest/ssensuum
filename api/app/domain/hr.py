import re
import unicodedata
from pathlib import PurePath
from typing import Optional

# nginx acepta hasta 10 MB por petición; se deja margen para el resto del formulario.
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024

DOCUMENT_CATEGORIES = {
    "contrato": "Contrato",
    "identificacion": "Identificación",
    "comprobante": "Comprobante",
    "certificado": "Certificado",
    "nomina": "Nómina",
    "otro": "Otro",
}

# Solo documentos de oficina e imágenes: nada que el navegador pueda ejecutar al abrirlo.
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
}


def clean_file_name(value: str) -> str:
    """Nombre seguro para mostrar y descargar: sin rutas ni caracteres de control."""
    name = PurePath(value.replace("\\", "/")).name
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r"[\x00-\x1f\x7f/\\:*?\"<>|]+", "_", name).strip(" .")
    return name[:255]


def extension(file_name: str) -> str:
    return PurePath(file_name).suffix.lower()


def content_type_for(file_name: str) -> Optional[str]:
    return ALLOWED_EXTENSIONS.get(extension(file_name))


def folder_name(value: str) -> str:
    """Nombre de carpeta dentro del ZIP de exportación."""
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9 _-]+", "", text).strip() or "General"
