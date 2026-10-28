import json
import re
from datetime import datetime, time
from typing import Optional

from .errors import ValidationError
from .rules import ensure_tz

# Horario de cada masajista, guardado como JSON en Therapist.schedule_json:
#   {"always": true}                         → disponible en todo el horario del club
#   {"days": {"0": [["17:00", "20:30"]], …}} → solo en esas franjas; 0 = lunes … 6 = domingo,
#                                              y un día sin franjas es día de descanso.
# Sin valor (None) = aún no se captura; se trata como disponible siempre.
WEEKDAYS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
ALWAYS = {"always": True}
_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def normalize(schedule: dict) -> dict:
    """Valida un horario que llega de RH y lo deja en su forma canónica."""
    if schedule.get("always"):
        return dict(ALWAYS)
    days = {}
    for key, windows in (schedule.get("days") or {}).items():
        if key not in {str(day) for day in range(7)}:
            raise ValidationError("Día no válido en el horario")
        clean = []
        for window in windows or []:
            if len(window) != 2 or not all(isinstance(value, str) and _TIME.match(value) for value in window):
                raise ValidationError(f"{WEEKDAYS[int(key)]}: usa horas en formato HH:MM")
            if window[0] >= window[1]:
                raise ValidationError(f"{WEEKDAYS[int(key)]}: la hora de salida debe ser después de la de entrada")
            clean.append([window[0], window[1]])
        clean.sort()
        if any(clean[i][1] > clean[i + 1][0] for i in range(len(clean) - 1)):
            raise ValidationError(f"{WEEKDAYS[int(key)]}: las franjas se enciman")
        if clean:
            days[key] = clean
    if not days:
        raise ValidationError("Marca al menos un día, o elige “Siempre disponible”")
    return {"days": days}


def load(schedule_json: Optional[str]) -> Optional[dict]:
    return json.loads(schedule_json) if schedule_json else None


def dump(schedule: dict) -> str:
    return json.dumps(schedule, separators=(",", ":"))


def works(schedule: Optional[dict], starts_at: datetime, ends_at: datetime) -> bool:
    """True si la sesión completa cae dentro de una franja del masajista."""
    if not schedule or schedule.get("always"):
        return True
    start, end = ensure_tz(starts_at), ensure_tz(ends_at)
    if start.date() != end.date() and end.time() != time(0, 0):
        return False
    begin = start.strftime("%H:%M")
    finish = "24:00" if end.date() != start.date() else end.strftime("%H:%M")
    return any(window[0] <= begin and finish <= window[1] for window in schedule["days"].get(str(start.weekday()), []))
