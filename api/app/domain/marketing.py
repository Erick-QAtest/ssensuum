"""Marketing orgánico: de qué red llega cada cliente, el calendario de publicaciones y las métricas por red."""

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

# Redes donde se publica: el calendario y las métricas solo usan estas.
SOCIAL_CHANNELS = {"instagram": "Instagram", "tiktok": "TikTok", "x": "X", "facebook": "Facebook"}
# Cómo nos conoció un cliente: las redes y lo que llega fuera de ellas.
SOURCES = {**SOCIAL_CHANNELS, "google": "Google / Maps", "recomendacion": "Recomendación", "otro": "Otro"}

# Valores cortos que se usan en los enlaces de cada red (?utm_source=ig) y dominios de referencia.
_ALIASES = {
    "instagram": "instagram", "ig": "instagram", "insta": "instagram",
    "tiktok": "tiktok", "tt": "tiktok",
    "x": "x", "twitter": "x", "tw": "x",
    "facebook": "facebook", "fb": "facebook", "meta": "facebook",
    "google": "google", "maps": "google", "gmb": "google",
}
# Una parte del dominio (l.instagram.com, m.facebook.com, www.google.com.mx) basta para reconocer la red.
_HOST_LABELS = {"instagram": "instagram", "tiktok": "tiktok", "facebook": "facebook", "fb": "facebook", "twitter": "x", "google": "google"}
_X_HOSTS = {"x.com", "t.co"}

POST_STATUSES = {"idea": "Idea", "listo": "Listo para publicar", "publicado": "Publicado"}
POST_FORMATS = {"reel": "Reel / video", "carrusel": "Carrusel", "foto": "Foto", "historia": "Historia", "texto": "Texto / hilo"}
PILLARS = {
    "equipo": "Conoce al equipo",
    "tecnicas": "Técnicas y beneficios",
    "experiencia": "El lugar y la experiencia",
    "private_club": "Private Club",
    "testimonios": "Testimonios",
    "fechas": "Fechas especiales",
}

# Lo que se captura a mano cada semana de cada red.
METRICS = {"followers": "Seguidores", "reach": "Alcance", "interactions": "Interacciones", "link_clicks": "Clics al enlace"}


def normalize_channel(value: Optional[str]) -> Optional[str]:
    """Red a partir de un utm_source o del dominio de referencia; None si no se reconoce."""
    text = (value or "").strip().lower()
    if not text:
        return None
    if text in _ALIASES:
        return _ALIASES[text]
    host = re.sub(r"^https?://", "", text).split("/")[0].split(":")[0]
    if host in _X_HOSTS or any(host.endswith(f".{name}") for name in _X_HOSTS):
        return "x"
    for label in host.split("."):
        if label in _HOST_LABELS:
            return _HOST_LABELS[label]
    return None


def clean_source(value: Optional[str]) -> Optional[str]:
    """Origen elegido a mano (Registro, Clientes): una de las opciones de SOURCES."""
    text = (value or "").strip().lower()
    if not text:
        return None
    return text if text in SOURCES else normalize_channel(text)


def metric_changes(snapshots: list[dict]) -> list[dict]:
    """Agrega a cada captura (ordenadas por fecha, de una misma red) cuánto cambió cada métrica desde la anterior."""
    rows = []
    previous: Optional[dict] = None
    for snapshot in snapshots:
        changes = {}
        for metric in METRICS:
            current, before = snapshot.get(metric), (previous or {}).get(metric)
            changes[metric] = current - before if current is not None and before is not None else None
        rows.append({**snapshot, "changes": changes})
        previous = snapshot
    return rows


def conversion(numerator: int, denominator: int) -> Optional[float]:
    return round(numerator / denominator * 100, 1) if denominator else None


# Fila para visitas y clientes sin red conocida (llegaron directo, por buscador sin referencia, o no se preguntó).
UNKNOWN = "sin_origen"
_EVENT_COLUMNS = {"page_view": "visits", "reserve_click": "reserveClicks", "checkout_start": "checkoutStarts", "whatsapp_click": "whatsappClicks"}


@dataclass
class CustomerTouch:
    source: Optional[str]
    created_on: date
    stage: str
    visits: int


def attribution(event_counts: list[tuple[Optional[str], str, int]], customers: list[CustomerTouch], since: date) -> list[dict]:
    """Por red: visitas y clics del periodo, clientes nuevos del periodo y en qué etapa están todos los que llegaron por ahí."""
    keys = [*SOURCES, UNKNOWN]
    rows = {
        key: {
            "source": key,
            "label": SOURCES.get(key, "Directo o sin dato"),
            **{column: 0 for column in _EVENT_COLUMNS.values()},
            "newCustomers": 0,
            "customers": 0,
            "visited": 0,
            "recurring": 0,
            "members": 0,
            "atRisk": 0,
        }
        for key in keys
    }
    for channel, name, count in event_counts:
        column = _EVENT_COLUMNS.get(name)
        if column:
            rows[channel if channel in rows else UNKNOWN][column] += count
    for customer in customers:
        row = rows[customer.source if customer.source in rows else UNKNOWN]
        row["customers"] += 1
        row["newCustomers"] += customer.created_on >= since
        row["visited"] += customer.visits > 0
        row["recurring"] += customer.visits >= 2
        row["members"] += customer.stage == "miembro"
        row["atRisk"] += customer.stage in ("en_riesgo", "inactivo")
    for row in rows.values():
        row["conversion"] = conversion(row["newCustomers"], row["visits"])
    return list(rows.values())
