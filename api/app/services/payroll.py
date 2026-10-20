import io
from datetime import date, datetime, time, timedelta, timezone

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from ..domain.errors import NotFoundError, ValidationError
from ..domain.hr import CLEANING_AUTHORIZATION
from ..domain.payroll import PAYOUTS_START, payout_due, settle, week_start
from ..domain.rules import TZ, ensure_tz
from ..models import TherapistPayout
from ..repositories import hr as hr_repo
from ..repositories import records as records_repo
from ..schemas import PayoutUpdate


def _utc(value: datetime) -> datetime:
    # SQLite pierde la zona horaria: los pagos se guardan en UTC.
    return value.replace(tzinfo=value.tzinfo or timezone.utc)


def _settle_weeks(db: Session, first_monday: date, weeks: int) -> list[dict]:
    """Liquidación por masajista y semana, con el estado de pago de cada servicio."""
    start = datetime.combine(first_monday, time.min, tzinfo=TZ)
    rows = sorted(records_repo.list_paid_between(db, start, start + timedelta(days=7 * weeks)), key=lambda row: row.paid_at)
    names = {row.id: row.name for row in hr_repo.list_therapists(db)}
    authorized = {tid for tid, categories in hr_repo.categories_by_therapist(db).items() if CLEANING_AUTHORIZATION in categories}
    paid = hr_repo.payouts(db, [row.id for row in rows])
    now = datetime.now(TZ)

    services: dict[tuple[date, str], list[dict]] = {}
    for record in rows:
        service_at = ensure_tz(record.paid_at)
        tips = {tip["therapistId"]: tip["amount"] for tip in records_repo.tips(record)}
        for therapist_id in records_repo.therapist_ids(record):
            services.setdefault((week_start(service_at.date()), therapist_id), []).append({
                "recordId": record.id,
                "paidAt": service_at.isoformat(),
                "serviceName": record.service_name,
                "customerName": record.customer_name,
                "tip": tips.get(therapist_id, 0),
            })

    result = []
    for (monday, therapist_id), items in services.items():
        row = settle(items, therapist_id in authorized)
        for line in row["lines"]:
            due = payout_due(datetime.fromisoformat(line["paidAt"]))
            payout = paid.get((line["recordId"], therapist_id))
            line["dueAt"] = due.isoformat()
            line["payoutAt"] = ensure_tz(_utc(payout.paid_at)).isoformat() if payout else None
            line["overdue"] = payout is None and now > due
        row["paidLines"] = sum(1 for line in row["lines"] if line["payoutAt"])
        row["pending"] = sum(line["pay"] for line in row["lines"] if not line["payoutAt"])
        result.append({"weekStart": monday, "therapistId": therapist_id, "therapistName": names.get(therapist_id, therapist_id), **row})
    return result


def weekly_payroll(db: Session, day: date) -> dict:
    monday = week_start(day)
    staff = sorted(_settle_weeks(db, monday, 1), key=lambda row: row["therapistName"])
    for row in staff:
        row.pop("weekStart")
    return {
        "weekStart": monday.isoformat(),
        "weekEnd": (monday + timedelta(days=6)).isoformat(),
        "staff": staff,
        "totals": {
            key: sum(row[key] for row in staff)
            for key in ("services", "gross", "cleaning", "cleaningToCollect", "servicePay", "tips", "total", "pending")
        },
    }


def pending_payouts(db: Session) -> list[dict]:
    """Servicios desde el inicio de los contratos cuyo pago al masajista sigue pendiente, del más urgente al último."""
    first_monday = week_start(PAYOUTS_START)
    weeks = (week_start(datetime.now(TZ).date()) - first_monday).days // 7 + 1
    pending = []
    for row in _settle_weeks(db, first_monday, weeks):
        for line in row["lines"]:
            if not line["payoutAt"] and datetime.fromisoformat(line["paidAt"]).date() >= PAYOUTS_START:
                pending.append({"therapistId": row["therapistId"], "therapistName": row["therapistName"], **line})
    return sorted(pending, key=lambda line: line["dueAt"])


def set_payout(db: Session, payload: PayoutUpdate) -> None:
    record = records_repo.get(db, payload.record_id)
    if not record:
        raise NotFoundError("Registro no encontrado")
    if payload.therapist_id not in records_repo.therapist_ids(record):
        raise ValidationError("Ese masajista no atendió el servicio")
    existing = hr_repo.get_payout(db, payload.record_id, payload.therapist_id)
    if not payload.paid:
        if existing:
            hr_repo.delete(db, existing)
        return
    if existing:
        return
    service_at = ensure_tz(record.paid_at)
    rows = _settle_weeks(db, week_start(service_at.date()), 1)
    line = next(
        line for row in rows if row["therapistId"] == payload.therapist_id
        for line in row["lines"] if line["recordId"] == payload.record_id
    )
    hr_repo.save(db, TherapistPayout(
        record_id=payload.record_id,
        therapist_id=payload.therapist_id,
        amount=line["pay"],
        paid_at=datetime.now(timezone.utc),
    ))


def export_payroll_xlsx(db: Session, day: date) -> bytes:
    payroll = weekly_payroll(db, day)
    workbook = Workbook()
    summary = workbook.active
    summary.title = "Liquidación"
    summary.append([f"Semana del {payroll['weekStart']} al {payroll['weekEnd']}"])
    summary.append(["Masajista", "Servicios", "Honorarios", "Limpieza descontada", "Limpieza por cobrar aparte",
                    "Propinas", "Total a pagar", "Pendiente de pago"])
    for row in payroll["staff"]:
        summary.append([row["therapistName"], row["services"], row["gross"], -row["cleaning"], row["cleaningToCollect"],
                        row["tips"], row["total"], row["pending"]])
    totals = payroll["totals"]
    summary.append(["Total", totals["services"], totals["gross"], -totals["cleaning"], totals["cleaningToCollect"],
                    totals["tips"], totals["total"], totals["pending"]])

    detail = workbook.create_sheet("Detalle")
    detail.append(["Masajista", "Servicio realizado", "Servicio", "Cliente", "Honorarios", "Limpieza", "Propina",
                   "A pagar", "Pagar a más tardar", "Pagado el"])
    for row in payroll["staff"]:
        for line in row["lines"]:
            stamp = lambda value: datetime.fromisoformat(value).astimezone(TZ).strftime("%Y-%m-%d %H:%M") if value else None
            detail.append([row["therapistName"], stamp(line["paidAt"]), line["serviceName"], line["customerName"],
                           line["gross"], -line["cleaning"], line["tip"], line["pay"], stamp(line["dueAt"]), stamp(line["payoutAt"])])

    for sheet, header_row in ((summary, 2), (detail, 1)):
        for cell in sheet[header_row]:
            cell.font = Font(bold=True)
        for column in sheet.columns:
            width = max(len(str(cell.value or "")) for cell in column[header_row - 1:])
            sheet.column_dimensions[column[0].column_letter].width = min(width + 2, 40)
    summary[1][0].font = Font(bold=True)
    for cell in summary[summary.max_row]:
        cell.font = Font(bold=True)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
