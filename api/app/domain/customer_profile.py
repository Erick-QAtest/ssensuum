"""Perfil del cliente: recurrencia, preferencias y etapa en el funnel, a partir de sus visitas y reservas."""

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

# Etapas en el orden en que se recorren; en_riesgo e inactivo aplican a quien ya vino y dejó de venir.
FUNNEL_STAGES = {
    "lead": "Interesado",
    "primera_reserva": "Primera reserva",
    "primera_visita": "Primera visita",
    "recurrente": "Recurrente",
    "miembro": "Miembro Private Club",
    "en_riesgo": "En riesgo",
    "inactivo": "Inactivo",
}

# Con una sola visita aún no hay frecuencia propia: se espera que vuelva en este plazo.
DEFAULT_GAP_DAYS = 45
# Se considera en riesgo al pasar 1.5 veces su frecuencia habitual (nunca antes de 21 días)…
OVERDUE_FACTOR = 1.5
MIN_OVERDUE_DAYS = 21
# …e inactivo al pasar 3 veces su frecuencia (nunca antes de 90 días).
INACTIVE_FACTOR = 3
MIN_INACTIVE_DAYS = 90

# Mismas ventanas que el quiz (web/features/quiz/quiz.ts).
TIME_WINDOWS = (("manana", 12), ("tarde", 17), ("noche", 24))
WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

QUIZ_QUESTIONS = ("objetivo", "presion", "zona", "trato", "horario")
_QUIZ_VALUE = re.compile(r"^[a-z]{1,20}$")


@dataclass
class Visit:
    """Un día en que el cliente vino: de un servicio registrado o de una reserva confirmada que ya pasó."""

    at: datetime
    service_name: str
    therapist_ids: list[str] = field(default_factory=list)
    amount: Optional[int] = None
    tip: int = 0


def membership_active(expires_on: Optional[str], today: date) -> bool:
    return bool(expires_on) and expires_on >= today.isoformat()


def clean_quiz_answers(raw: Optional[dict]) -> dict[str, str]:
    """Solo se guardan las preguntas del quiz, con valores cortos tal como los envía el sitio."""
    if not isinstance(raw, dict):
        return {}
    answers = {}
    for key in QUIZ_QUESTIONS:
        value = raw.get(key)
        if isinstance(value, str) and _QUIZ_VALUE.match(value):
            answers[key] = value
    return answers


def load_quiz(quiz_json: Optional[str]) -> dict[str, str]:
    try:
        return clean_quiz_answers(json.loads(quiz_json)) if quiz_json else {}
    except ValueError:
        return {}


def visit_days(visits: list[Visit]) -> list[date]:
    return sorted({visit.at.date() for visit in visits})


def recurrence(visits: list[Visit], today: date) -> dict:
    days = visit_days(visits)
    if not days:
        return {
            "visits": 0, "firstVisit": None, "lastVisit": None, "averageGapDays": None,
            "daysSinceLastVisit": None, "nextExpectedVisit": None, "status": None,
        }
    gaps = [(later - earlier).days for earlier, later in zip(days, days[1:])]
    average = round(sum(gaps) / len(gaps)) if gaps else None
    expected = average or DEFAULT_GAP_DAYS
    since = (today - days[-1]).days
    return {
        "visits": len(days),
        "firstVisit": days[0].isoformat(),
        "lastVisit": days[-1].isoformat(),
        "averageGapDays": average,
        "daysSinceLastVisit": since,
        "nextExpectedVisit": date.fromordinal(days[-1].toordinal() + expected).isoformat(),
        "status": recurrence_status(since, expected),
    }


def recurrence_status(days_since_last: int, expected_gap: int) -> str:
    if days_since_last > max(expected_gap * INACTIVE_FACTOR, MIN_INACTIVE_DAYS):
        return "inactivo"
    if days_since_last > max(expected_gap * OVERDUE_FACTOR, MIN_OVERDUE_DAYS):
        return "atrasado"
    return "al_corriente"


def funnel_stage(visits: list[Visit], has_upcoming: bool, is_member: bool, today: date) -> str:
    """Etapa del cliente. Quien ya vino y tarda más de lo normal en volver queda en riesgo o inactivo,
    aunque sea miembro, salvo que ya tenga otra cita reservada."""
    summary = recurrence(visits, today)
    if summary["visits"] and not has_upcoming:
        if summary["status"] == "inactivo":
            return "inactivo"
        if summary["status"] == "atrasado":
            return "en_riesgo"
    if is_member:
        return "miembro"
    if summary["visits"] >= 2:
        return "recurrente"
    if summary["visits"] == 1:
        return "primera_visita"
    return "primera_reserva" if has_upcoming else "lead"


def _most_common(values: list[str]) -> Optional[dict]:
    if not values:
        return None
    value, count = Counter(values).most_common(1)[0]
    return {"value": value, "count": count}


def time_window(at: datetime) -> str:
    return next(name for name, until in TIME_WINDOWS if at.hour < until)


def preferences(visits: list[Visit]) -> dict:
    paid = [visit.amount for visit in visits if visit.amount is not None]
    return {
        "service": _most_common([visit.service_name for visit in visits]),
        "therapistId": _most_common([tid for visit in visits for tid in visit.therapist_ids]),
        "weekday": _most_common([WEEKDAYS[visit.at.weekday()] for visit in visits]),
        "timeWindow": _most_common([time_window(visit.at) for visit in visits]),
        "totalSpent": sum(paid),
        "averageTicket": round(sum(paid) / len(paid)) if paid else None,
        "totalTips": sum(visit.tip for visit in visits),
    }
