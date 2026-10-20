from datetime import date, datetime, timedelta

# Honorarios por servicio concluido (cláusula CUARTA); en uno de 4 manos o de pareja, cada masajista cobra lo mismo.
PAY_PER_SERVICE = 500
# Aportación semanal para limpieza (cláusula QUINTA): una vez por semana con al menos un servicio.
WEEKLY_CLEANING_FEE = 100
# Plazo para pagar honorarios y propinas de cada servicio (cláusula CUARTA).
PAYOUT_DEADLINE = timedelta(hours=48)
# Inicio de los contratos marco: los servicios anteriores se pagaron con el esquema previo.
PAYOUTS_START = date(2026, 10, 20)


def week_start(day: date) -> date:
    """Lunes de la semana que contiene ese día (las semanas van de lunes a domingo)."""
    return day - timedelta(days=day.weekday())


def payout_due(service_at: datetime) -> datetime:
    return service_at + PAYOUT_DEADLINE


def settle(services: list[dict], compensate_cleaning: bool) -> dict:
    """Liquidación semanal de un masajista; services va ordenado por fecha y cada uno trae su propina ("tip").

    La limpieza solo se descuenta del primer servicio si el masajista firmó la autorización de compensación;
    si no, queda como cobro aparte, a más tardar el lunes siguiente.
    """
    lines = []
    for index, service in enumerate(services):
        cleaning = WEEKLY_CLEANING_FEE if index == 0 and compensate_cleaning else 0
        tip = service.get("tip", 0)
        lines.append({**service, "gross": PAY_PER_SERVICE, "cleaning": cleaning, "tip": tip, "pay": PAY_PER_SERVICE - cleaning + tip})
    gross = PAY_PER_SERVICE * len(lines)
    fee = WEEKLY_CLEANING_FEE if lines else 0
    cleaning = fee if compensate_cleaning else 0
    tips = sum(line["tip"] for line in lines)
    return {
        "services": len(lines),
        "gross": gross,
        "cleaning": cleaning,
        "cleaningToCollect": fee - cleaning,
        "cleaningCompensated": compensate_cleaning,
        "servicePay": gross - cleaning,
        "tips": tips,
        "total": gross - cleaning + tips,
        "lines": lines,
    }
