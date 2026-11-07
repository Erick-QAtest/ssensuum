"""Confirmación de una cita pagada por SMS: mensajes para el cliente y el masajista, y el archivo de calendario.

Los textos viven aquí para usarlos igual cuando los envíe la recepción (enlaces sms: desde el celular)
o, más adelante, un proveedor de SMS. Son cortos y sin á, í, ó, ú: así caben en el alfabeto básico
de SMS (160 caracteres por segmento) y no en el de 70.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

ADDRESS = "Mexicaltzingo 2122-B, Col. Americana, Guadalajara"
PARKING = "Estacionamiento en los cajones 1, 2 y 3, frente al club."
MAPS_URL = "https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6"
ARRIVAL_MINUTES = 30  # el masajista puede estar desde 30 min antes hasta 30 min después

WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def day_label(moment: datetime) -> str:
    return f"{WEEKDAYS[moment.weekday()]} {moment.day} de {MONTHS[moment.month - 1]}"


def time_label(moment: datetime) -> str:
    hour = moment.hour % 12 or 12
    suffix = "a.m." if moment.hour < 12 else "p.m."
    return f"{hour}:{moment.minute:02d} {suffix}"


def money(amount: int) -> str:
    return f"${amount:,}"


def names(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} y {items[-1]}"


CLUB_PHONE = "33 2943 4598"
# á, í, ó, ú no existen en el alfabeto básico de SMS (é, ñ, ¿ y ¡ sí): un solo acento parte el mensaje en trozos de 70.
_SMS_PLAIN = str.maketrans("áíóúÁÍÓÚ", "aiouAIOU")
SMS_SEGMENT = 153  # caracteres por segmento cuando el mensaje ocupa más de uno


def sms_time(moment: datetime) -> str:
    """5:00 pm: más corto que "5:00 p.m." y sin el punto doble al final de una frase."""
    return time_label(moment).replace("a.m.", "am").replace("p.m.", "pm")


def sms_text(text: str) -> str:
    return text.translate(_SMS_PLAIN)


def sms_segments(text: str) -> int:
    return 1 if len(text) <= 160 else math.ceil(len(text) / SMS_SEGMENT)


def sms_link(phone: Optional[str], text: str) -> Optional[str]:
    """Enlace sms: a un celular de México (10 dígitos) que abre Mensajes con el texto listo; None si no hay teléfono.

    El "?&body=" funciona igual en iPhone y en Android.
    """
    if not phone:
        return None
    return f"sms:+52{phone}?&body={quote(text)}"


def customer_message(first_name: str, service: str, therapists: list[str], starts: datetime, deposit: int, calendar_url: str) -> str:
    return sms_text(
        f"SSENSUUM: Hola {first_name}, tu cita esta confirmada. {service} con {names(therapists)}, "
        f"{day_label(starts)}, {sms_time(starts)}. Mexicaltzingo 2122-B, Col. Americana (cajones 1-3). "
        f"Anticipo {money(deposit)} pagado. Calendario: {calendar_url}"
    )


def therapist_message(therapist: str, service: str, customer_first_name: str, starts: datetime, ends: datetime, partners: list[str]) -> str:
    arrive = starts - timedelta(minutes=ARRIVAL_MINUTES)
    leave = ends + timedelta(minutes=ARRIVAL_MINUTES)
    together = f" Trabajas con {names(partners)}." if partners else ""
    return sms_text(
        f"SSENSUUM: Hola {therapist}, cita confirmada: {service} con {customer_first_name}, "
        f"{day_label(starts)}, {sms_time(starts)}.{together} Llega {sms_time(arrive)}, sal antes de {sms_time(leave)}."
    )


def needs_attention_message(first_name: str, service: str) -> str:
    return sms_text(
        f"SSENSUUM: Hola {first_name}, recibimos tu anticipo para {service}, pero el horario se ocupo mientras pagabas. "
        f"Te ofrecemos otro horario o la devolucion del anticipo. Escribenos o llamanos: {CLUB_PHONE}"
    )


def _ics_time(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ics_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def calendar_file(reservation_id: str, service: str, starts: datetime, ends: datetime, created: datetime) -> str:
    """Evento .ics con aviso 2 horas antes. Sin datos personales: solo servicio, hora y lugar."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SSENSUUM//Reservas//ES",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{reservation_id}@ssensuum.mx",
        f"DTSTAMP:{_ics_time(created)}",
        f"DTSTART:{_ics_time(starts)}",
        f"DTEND:{_ics_time(ends)}",
        f"SUMMARY:{_ics_text(f'SSENSUUM · {service}')}",
        f"LOCATION:{_ics_text(ADDRESS)}",
        f"DESCRIPTION:{_ics_text(f'Anticipo pagado. {PARKING} Cómo llegar: {MAPS_URL}')}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Tu cita en SSENSUUM",
        "TRIGGER:-PT2H",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"
