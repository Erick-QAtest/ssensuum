from datetime import date, timedelta

# Lo que gana cada masajista por servicio atendido; en uno de 4 manos o de pareja, cada uno gana lo mismo.
PAY_PER_SERVICE = 500
# Cuota semanal de limpieza: se descuenta del primer servicio de la semana. Sin servicios, no se cobra.
WEEKLY_CLEANING_FEE = 100


def week_start(day: date) -> date:
    """Lunes de la semana que contiene ese día (las semanas van de lunes a domingo)."""
    return day - timedelta(days=day.weekday())


def settle(services: list[dict], tips: int) -> dict:
    """Liquidación de un masajista: services ya viene ordenado por fecha de cobro."""
    lines = []
    for index, service in enumerate(services):
        cleaning = WEEKLY_CLEANING_FEE if index == 0 else 0
        lines.append({**service, "gross": PAY_PER_SERVICE, "cleaning": cleaning, "pay": PAY_PER_SERVICE - cleaning})
    gross = PAY_PER_SERVICE * len(lines)
    cleaning = WEEKLY_CLEANING_FEE if lines else 0
    return {
        "services": len(lines),
        "gross": gross,
        "cleaning": cleaning,
        "servicePay": gross - cleaning,
        "tips": tips,
        "total": gross - cleaning + tips,
        "lines": lines,
    }
