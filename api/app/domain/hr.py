import re
import unicodedata
from pathlib import PurePath
from typing import Optional

# nginx acepta hasta 10 MB por petición; se deja margen para el resto del formulario.
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024

DOCUMENT_CATEGORIES = {
    "contrato": "Contrato firmado",
    "autorizacion_imagen": "Autorización de imagen",
    "autorizacion_descuento": "Autorización de descuento de limpieza",
    "identificacion": "Identificación oficial",
    "comprobante": "Comprobante",
    "certificado": "Certificado",
    "nomina": "Nómina",
    "otro": "Otro",
    "plantilla": "Formato para firmar",
}

# Formatos en blanco que se descargan, se imprimen y se firman; son del equipo, no de un masajista.
TEMPLATE_CATEGORY = "plantilla"

# Lo que cada masajista debe entregar firmado para tener su documentación completa.
# La autorización de imagen cuenta aunque no marque ninguna casilla: lo que se pide es el documento firmado.
REQUIRED_DOCUMENTS = ("contrato", "autorizacion_imagen", "autorizacion_descuento", "identificacion")
# Con este documento firmado, la limpieza semanal se descuenta de los honorarios (cláusula QUINTA).
CLEANING_AUTHORIZATION = "autorizacion_descuento"

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


# La foto del equipo se recorta en el navegador; aquí solo se acepta una imagen ligera que el sitio pueda mostrar.
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def photo_extension(content: bytes) -> Optional[str]:
    """Extensión según el contenido real del archivo, no según su nombre."""
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def therapist_slug(name: str) -> str:
    """Identificador de un masajista a partir de su nombre: "Alemán" → "aleman"."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60]
