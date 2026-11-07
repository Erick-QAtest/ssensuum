"""Operación diaria: zonas con foto y puntos, tareas del día, marcas y cierre."""

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..domain import operations as ops
from ..domain.errors import ConflictError, NotFoundError, ValidationError
from ..domain.hr import MAX_PHOTO_BYTES, photo_extension
from ..domain import notices
from ..domain.rules import TZ, ensure_tz
from ..models import (
    Customer, MarketingPost, OpsCheck, OpsDay, OpsEvidence, OpsPoint, OpsStockMove, OpsSupply, OpsZone, Reservation,
    ReservationNotice, Service, StaffProfile, Therapist,
)


def ensure_zones(db: Session) -> None:
    """Crea las zonas que falten; no toca nombres, fotos ni puntos existentes."""
    existing = {row.id for row in db.scalars(select(OpsZone))}
    for sort, (zone_id, name) in enumerate(ops.ZONES):
        if zone_id not in existing:
            db.add(OpsZone(id=zone_id, name=name, sort=sort))
    supplies = {row.id for row in db.scalars(select(OpsSupply))}
    for supply_id, name, unit, pack, days, lead, price in ops.SUPPLIES:
        if supply_id not in supplies:
            db.add(OpsSupply(id=supply_id, name=name, unit=unit, pack_size=pack, daily_use=round(pack / days, 4), lead_days=lead, safety_days=3, price=price))
    db.commit()


# --- Zonas, fotos y puntos ---


def _zone(db: Session, zone_id: str) -> OpsZone:
    zone = db.get(OpsZone, zone_id)
    if not zone:
        raise NotFoundError("Zona no encontrada")
    return zone


def photos_dir() -> Path:
    path = Path(settings.ops_photos_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def photo_path(zone_id: str) -> Optional[Path]:
    # El id llega de la URL: solo se aceptan zonas conocidas para no salir de la carpeta.
    if zone_id not in ops.ZONE_IDS:
        return None
    for candidate in photos_dir().glob(f"{zone_id}.*"):
        return candidate
    return None


def set_photo(db: Session, zone_id: str, content: bytes) -> OpsZone:
    zone = _zone(db, zone_id)
    if not content:
        raise ValidationError("Elige la foto de la zona")
    if len(content) > MAX_PHOTO_BYTES:
        raise ValidationError("La foto pesa más de 5 MB")
    suffix = photo_extension(content)
    if not suffix:
        raise ValidationError("La foto debe ser JPG, PNG o WebP")
    for old in photos_dir().glob(f"{zone.id}.*"):
        old.unlink(missing_ok=True)
    (photos_dir() / f"{zone.id}{suffix}").write_bytes(content)
    zone.photo_version = int(datetime.now(timezone.utc).timestamp())
    db.commit()
    return zone


def points(db: Session, zone_ids: Optional[list[str]] = None) -> list[OpsPoint]:
    query = select(OpsPoint).order_by(OpsPoint.created_at, OpsPoint.id)
    if zone_ids is not None:
        query = query.where(OpsPoint.zone_id.in_(zone_ids))
    return list(db.scalars(query))


def add_point(db: Session, zone_id: str, x: float, y: float, kind: str, label: str) -> OpsPoint:
    _zone(db, zone_id)
    if kind not in ops.POINT_KINDS:
        raise ValidationError("Tipo de punto no reconocido")
    label = " ".join(label.split())
    if not label:
        raise ValidationError("Escribe qué hay que hacer en ese punto")
    point = OpsPoint(id=str(uuid.uuid4()), zone_id=zone_id, x=x, y=y, kind=kind, label=label)
    db.add(point)
    db.commit()
    return point


def delete_point(db: Session, point_id: str) -> None:
    point = db.get(OpsPoint, point_id)
    if not point:
        raise NotFoundError("Punto no encontrado")
    db.delete(point)
    db.commit()


def zones_overview(db: Session) -> list[dict]:
    by_zone: dict[str, list[OpsPoint]] = {}
    for point in points(db):
        by_zone.setdefault(point.zone_id, []).append(point)
    rows = db.scalars(select(OpsZone).order_by(OpsZone.sort)).all()
    return [_zone_payload(zone, by_zone.get(zone.id, [])) for zone in rows]


def _zone_payload(zone: OpsZone, zone_points: list[OpsPoint], checks: Optional[dict] = None, task_key: str = "") -> dict:
    return {
        "id": zone.id,
        "name": zone.name,
        "photoUrl": f"/admin/ops/zones/{zone.id}/photo?v={zone.photo_version}" if zone.photo_version else None,
        "points": [
            {
                "id": point.id,
                "x": point.x,
                "y": point.y,
                "kind": point.kind,
                "kindLabel": ops.POINT_KINDS[point.kind],
                "label": point.label,
                **(_check_payload(checks.get(ops.point_key(task_key, point.id))) if checks is not None else {}),
            }
            for point in zone_points
        ],
    }


# --- Día operativo ---


def today() -> date:
    return datetime.now(TZ).date()


def _check_payload(check: Optional[OpsCheck]) -> dict:
    return {"status": check.status if check else "pendiente", "reason": check.reason if check else None}


def _checks(db: Session, day: date) -> dict[str, OpsCheck]:
    return {row.item_key: row for row in db.scalars(select(OpsCheck).where(OpsCheck.day == day.isoformat()))}


def _posts(db: Session, day: date) -> list[MarketingPost]:
    return list(db.scalars(select(MarketingPost).where(MarketingPost.publish_on == day.isoformat()).order_by(MarketingPost.channel)))


def day_overview(db: Session, day: date) -> dict:
    checks = _checks(db, day)
    posts = _posts(db, day)
    zones = {zone.id: zone for zone in db.scalars(select(OpsZone))}
    all_points = points(db)
    tasks = []
    supplies = supplies_overview(db, day) if day == today() else []
    to_order = [row for row in supplies if row["status"] in ("pedir", "urgente")]
    urgent = [row for row in supplies if row["status"] == "urgente"]
    evidence = _evidence_by_key(db, day)
    for task in ops.tasks_for(day, bool(posts), bool(urgent)):
        own = checks.get(task.key)
        item = {
            "key": task.key,
            "label": task.label,
            "minutes": task.minutes,
            "shift": task.shift,
            "shiftLabel": ops.SHIFTS[task.shift],
            "detail": task.detail or None,
            "zones": [],
            "posts": [],
            "supplies": [],
            "evidence": [],
        }
        relevant = [p for p in all_points if p.zone_id in task.zones and (not task.kinds or p.kind in task.kinds)]
        with_points = {p.zone_id for p in relevant}
        # En el aseo a fondo, una zona sin foto o sin puntos se marca aparte, como tarea simple.
        missing = [zones[z].name for z in task.zones if z in zones and z not in with_points] if not task.kinds else []
        item["zonesWithoutPoints"] = missing
        if task.source in ("order", "urgent"):
            rows = to_order if task.source == "order" else urgent
            item["supplies"] = [{"name": row["name"], "quantity": row["quantity"], "unit": row["unit"], "status": row["status"]} for row in rows]
            status = own.status if own else "pendiente"
        elif task.source == "posts":
            item["posts"] = [{"id": p.id, "title": p.title, "channel": p.channel, "status": p.status} for p in posts]
            done = all(p.status == "publicado" for p in posts)
            status = own.status if own and own.status == "no_se_pudo" else ("hecho" if done else "pendiente")
        elif relevant:
            for zone_id in task.zones:
                zone_points = [p for p in relevant if p.zone_id == zone_id]
                if zone_points:
                    item["zones"].append(_zone_payload(zones[zone_id], zone_points, checks, task.key))
            marked = all(ops.point_key(task.key, p.id) in checks for p in relevant)
            rest_done = not missing or bool(own and own.status == "hecho")
            status = own.status if own and own.status == "no_se_pudo" else ("hecho" if marked and rest_done else "pendiente")
        else:
            # Sin puntos en la foto (o sin foto todavía) se marca la tarea completa.
            status = own.status if own else "pendiente"
        for zone_id, point in _required_evidence(task, day, zones, relevant):
            photo = evidence.get((task.key, zone_id, point.id if point else None))
            item["evidence"].append({
                "zoneId": zone_id,
                "zoneName": zones[zone_id].name,
                "pointId": point.id if point else None,
                "pointLabel": point.label if point else None,
                "photo": _evidence_payload(photo, zones) if photo else None,
            })
        # Sin la foto pedida (o con la foto marcada para repetir) la tarea no queda hecha.
        if status == "hecho" and any(not row["photo"] or row["photo"]["review"] == "repetir" for row in item["evidence"]):
            status = "pendiente"
        item.update({"status": status, "reason": own.reason if own else None})
        tasks.append(item)

    closed = db.get(OpsDay, day.isoformat())
    if day == today() and not closed:
        tasks[:0] = _confirmation_tasks(db, day, checks)
    pending = sum(1 for task in tasks if task.get("status") == "pendiente")
    return {
        "day": day.isoformat(),
        "weekday": ops.WEEKDAYS[day.weekday()],
        "cycleWeek": ops.cycle_week(day),
        "isToday": day == today(),
        "closed": bool(closed),
        "closedAt": closed.closed_at.replace(tzinfo=timezone.utc).isoformat() if closed else None,
        "pending": pending,
        "minutes": sum(task["minutes"] for task in tasks),
        "canClose": not closed and pending == 0 and day <= today(),
        "tasks": tasks,
    }


def _open_day(db: Session, day: date) -> None:
    if db.get(OpsDay, day.isoformat()):
        raise ConflictError("El día ya está cerrado: reábrelo para cambiar algo")
    if day > today():
        raise ValidationError("Solo se marcan tareas de hoy o de días anteriores")


def _valid_key(db: Session, day: date, item_key: str) -> None:
    if item_key.startswith(CONFIRM_PREFIX):
        if day != today() or not db.get(Reservation, item_key[len(CONFIRM_PREFIX):]):
            raise ValidationError("Esa cita no se confirma hoy")
        return
    task_key, _, point_id = item_key.partition("@")
    task = ops.TASKS_BY_KEY.get(task_key)
    if not task or task not in ops.tasks_for(day, True, True):
        raise ValidationError("Esa tarea no toca este día")
    if point_id:
        point = db.get(OpsPoint, point_id)
        if not point or point.zone_id not in task.zones or (task.kinds and point.kind not in task.kinds):
            raise ValidationError("Ese punto no es parte de la tarea")


def check(db: Session, day: date, item_key: str, status: str, reason: Optional[str]) -> dict:
    _open_day(db, day)
    _valid_key(db, day, item_key)
    if status not in ops.STATUSES:
        raise ValidationError("Estado no reconocido")
    reason = " ".join((reason or "").split()) or None
    if status == "no_se_pudo" and not reason:
        raise ValidationError("Escribe por qué no se pudo")
    row = db.scalar(select(OpsCheck).where(OpsCheck.day == day.isoformat(), OpsCheck.item_key == item_key))
    if not row:
        row = OpsCheck(id=str(uuid.uuid4()), day=day.isoformat(), item_key=item_key)
        db.add(row)
    row.status = status
    row.reason = reason if status == "no_se_pudo" else None
    row.checked_at = datetime.utcnow()
    db.commit()
    return day_overview(db, day)


def uncheck(db: Session, day: date, item_key: str) -> dict:
    _open_day(db, day)
    row = db.scalar(select(OpsCheck).where(OpsCheck.day == day.isoformat(), OpsCheck.item_key == item_key))
    if row:
        db.delete(row)
        db.commit()
    return day_overview(db, day)


def close_day(db: Session, day: date) -> dict:
    overview = day_overview(db, day)
    if overview["closed"]:
        raise ConflictError("El día ya está cerrado")
    if day > today():
        raise ValidationError("Solo se cierra hoy o un día anterior")
    if overview["pending"]:
        raise ValidationError(f"Faltan {overview['pending']} tareas por marcar")
    db.add(OpsDay(day=day.isoformat()))
    db.commit()
    return day_overview(db, day)


def reopen_day(db: Session, day: date) -> dict:
    row = db.get(OpsDay, day.isoformat())
    if row:
        db.delete(row)
        db.commit()
    return day_overview(db, day)


# --- Insumos ---


def _supply(db: Session, supply_id: str) -> OpsSupply:
    supply = db.get(OpsSupply, supply_id)
    if not supply:
        raise NotFoundError("Insumo no encontrado")
    return supply


def _received_since(db: Session, supply_id: str, since: Optional[str]) -> float:
    query = select(OpsStockMove).where(OpsStockMove.supply_id == supply_id, OpsStockMove.kind == "recepcion")
    if since:
        query = query.where(OpsStockMove.day > since)
    return sum(row.quantity for row in db.scalars(query))


def _supply_payload(db: Session, supply: OpsSupply, on: date) -> dict:
    estimate = None
    if supply.stock is not None and supply.counted_on:
        received = _received_since(db, supply.id, supply.counted_on)
        estimate = max(0.0, ops.projected_stock(supply.stock, date.fromisoformat(supply.counted_on), received, supply.daily_use, on))
    plan = ops.supply_plan(estimate, supply.daily_use, supply.lead_days, supply.safety_days, supply.pack_size, on)
    return {
        "id": supply.id,
        "name": supply.name,
        "unit": supply.unit,
        "packSize": supply.pack_size,
        "dailyUse": supply.daily_use,
        "leadDays": supply.lead_days,
        "safetyDays": supply.safety_days,
        "price": supply.price,
        "countedStock": supply.stock,
        "countedOn": supply.counted_on,
        "estimate": round(estimate, 2) if estimate is not None else None,
        **plan,
    }


def supplies_overview(db: Session, on: Optional[date] = None) -> list[dict]:
    on = on or today()
    rows = db.scalars(select(OpsSupply).where(OpsSupply.active.is_(True)).order_by(OpsSupply.name)).all()
    order = {"urgente": 0, "pedir": 1, "sin_contar": 2, "bien": 3}
    return sorted((_supply_payload(db, row, on) for row in rows), key=lambda row: (order[row["status"]], row["name"]))


def save_supply(db: Session, supply_id: Optional[str], payload) -> list[dict]:
    name = " ".join(payload.name.split())
    unit = " ".join(payload.unit.split())
    if not name or not unit:
        raise ValidationError("Escribe el nombre y la unidad del insumo")
    supply = _supply(db, supply_id) if supply_id else OpsSupply(id=str(uuid.uuid4()), stock=None)
    supply.name, supply.unit = name, unit
    supply.pack_size, supply.daily_use = payload.pack_size, payload.daily_use
    supply.lead_days, supply.safety_days, supply.price = payload.lead_days, payload.safety_days, payload.price
    if not supply_id:
        db.add(supply)
    db.commit()
    return supplies_overview(db)


def count_supplies(db: Session, counts: dict[str, float]) -> list[dict]:
    """Inventario: guarda lo contado y corrige el consumo diario con lo que realmente se gastó."""
    day = today()
    for supply_id, quantity in counts.items():
        if quantity < 0:
            raise ValidationError("Las existencias no pueden ser negativas")
        supply = _supply(db, supply_id)
        if supply.stock is not None and supply.counted_on and supply.counted_on < day.isoformat():
            days = (day - date.fromisoformat(supply.counted_on)).days
            used = supply.stock + _received_since(db, supply.id, supply.counted_on) - quantity
            if used >= 0:
                supply.daily_use = ops.smoothed_use(supply.daily_use, used / days)
        supply.stock, supply.counted_on = quantity, day.isoformat()
        db.add(OpsStockMove(id=str(uuid.uuid4()), supply_id=supply.id, day=day.isoformat(), kind="conteo", quantity=quantity))
    db.commit()
    return supplies_overview(db)


def receive_supply(db: Session, supply_id: str, quantity: float) -> list[dict]:
    supply = _supply(db, supply_id)
    if supply.stock is None:
        raise ValidationError("Cuenta este insumo antes de registrar lo recibido")
    day = today().isoformat()
    if supply.counted_on == day:
        # Contado hoy: lo recibido se suma directo al conteo.
        supply.stock += quantity
    else:
        db.add(OpsStockMove(id=str(uuid.uuid4()), supply_id=supply.id, day=day, kind="recepcion", quantity=quantity))
    db.commit()
    return supplies_overview(db)


# --- Evidencia ---


def _required_evidence(task, day: date, zones: dict, relevant: list[OpsPoint]) -> list[tuple]:
    """Aseo a fondo: una foto por zona que tenga foto de referencia. Rondas: un punto al azar del día."""
    if task.source:
        return []
    if task.kinds:
        if not relevant:
            return []
        ordered = sorted(relevant, key=lambda point: point.id)
        point = ordered[ops.random_index(day, task.key, len(ordered))]
        return [(point.zone_id, point)]
    return [(zone_id, None) for zone_id in task.zones if zone_id in zones and zones[zone_id].photo_version]


def _evidence_by_key(db: Session, day: date) -> dict:
    rows = db.scalars(select(OpsEvidence).where(OpsEvidence.day == day.isoformat()).order_by(OpsEvidence.uploaded_at))
    return {(row.task_key, row.zone_id, row.point_id): row for row in rows}  # la más reciente gana


def _evidence_payload(row: OpsEvidence, zones: dict) -> dict:
    zone = zones.get(row.zone_id)
    return {
        "id": row.id,
        "url": f"/admin/ops/evidence/{row.id}/photo" if row.file_name else None,
        "referenceUrl": f"/admin/ops/zones/{zone.id}/photo?v={zone.photo_version}" if zone and zone.photo_version else None,
        "uploadedAt": row.uploaded_at.replace(tzinfo=timezone.utc).isoformat(),
        "review": row.review,
        "reviewLabel": ops.REVIEWS[row.review],
        "reviewNote": row.review_note,
    }


def evidence_dir() -> Path:
    path = Path(settings.ops_photos_dir) / "evidencia"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _prune_evidence(db: Session) -> None:
    limit = (today() - timedelta(days=ops.EVIDENCE_DAYS)).isoformat()
    for row in db.scalars(select(OpsEvidence).where(OpsEvidence.day < limit, OpsEvidence.file_name.is_not(None))):
        (evidence_dir() / row.file_name).unlink(missing_ok=True)
        row.file_name = None


def add_evidence(db: Session, day: date, task_key: str, zone_id: str, point_id: Optional[str], content: bytes) -> dict:
    _open_day(db, day)
    task = ops.TASKS_BY_KEY.get(task_key)
    if not task or task not in ops.tasks_for(day, True, True):
        raise ValidationError("Esa tarea no toca este día")
    zones = {zone.id: zone for zone in db.scalars(select(OpsZone))}
    relevant = [p for p in points(db, list(task.zones)) if not task.kinds or p.kind in task.kinds]
    required = {(z, p.id if p else None) for z, p in _required_evidence(task, day, zones, relevant)}
    if (zone_id, point_id or None) not in required:
        raise ValidationError("Esa foto no se pide en esta tarea")
    if not content:
        raise ValidationError("Toma la foto de evidencia")
    if len(content) > MAX_PHOTO_BYTES:
        raise ValidationError("La foto pesa más de 5 MB")
    suffix = photo_extension(content)
    if not suffix:
        raise ValidationError("La foto debe ser JPG, PNG o WebP")
    row = OpsEvidence(id=str(uuid.uuid4()), day=day.isoformat(), task_key=task_key, zone_id=zone_id, point_id=point_id or None)
    row.file_name = f"{row.id}{suffix}"
    (evidence_dir() / row.file_name).write_bytes(content)
    db.add(row)
    _prune_evidence(db)
    db.commit()
    return day_overview(db, day)


def evidence_file(db: Session, evidence_id: str) -> Optional[Path]:
    row = db.get(OpsEvidence, evidence_id)
    if not row or not row.file_name:
        return None
    path = evidence_dir() / row.file_name
    return path if path.exists() else None


def review_evidence(db: Session, evidence_id: str, review: str, note: Optional[str]) -> dict:
    row = db.get(OpsEvidence, evidence_id)
    if not row:
        raise NotFoundError("Foto no encontrada")
    if review not in ("bien", "repetir"):
        raise ValidationError("Elige bien o repetir")
    note = " ".join((note or "").split()) or None
    if review == "repetir" and not note:
        raise ValidationError("Escribe qué hay que repetir")
    row.review, row.review_note = review, note if review == "repetir" else None
    db.commit()
    return evidence_payload_full(db, row)


def evidence_payload_full(db: Session, row: OpsEvidence) -> dict:
    zones = {zone.id: zone for zone in db.scalars(select(OpsZone))}
    task = ops.TASKS_BY_KEY.get(row.task_key)
    point = db.get(OpsPoint, row.point_id) if row.point_id else None
    return {
        **_evidence_payload(row, zones),
        "day": row.day,
        "taskLabel": task.label if task else row.task_key,
        "zoneName": zones[row.zone_id].name if row.zone_id in zones else row.zone_id,
        "pointLabel": point.label if point else None,
    }


def list_evidence(db: Session, start: date, end: date) -> list[dict]:
    rows = db.scalars(select(OpsEvidence).where(OpsEvidence.day >= start.isoformat(), OpsEvidence.day <= end.isoformat())
                      .order_by(OpsEvidence.day.desc(), OpsEvidence.uploaded_at.desc())).all()
    return [evidence_payload_full(db, row) for row in rows]


# --- Confirmación de citas pagadas ---

CONFIRM_PREFIX = "cita:"
CONFIRM_STATUSES = ("CONFIRMED", "NEEDS_ATTENTION")


def calendar_url(reservation_id: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/api/reservations/{reservation_id}/calendar.ics"


def _confirmation_targets(db: Session, reservation: Reservation) -> list[dict]:
    """A quién hay que avisar de una cita y con qué SMS."""
    service = db.get(Service, reservation.service_id)
    service_name = service.name if service else reservation.service_id
    customer = db.get(Customer, reservation.customer_id) if reservation.customer_id else None
    first_name = (customer.first_name if customer else "") or "cliente"
    ids = json.loads(reservation.therapist_ids_json)
    team = {row.id: row.name for row in db.scalars(select(Therapist).where(Therapist.id.in_(ids)))}
    phones = {row.therapist_id: row.phone for row in db.scalars(select(StaffProfile).where(StaffProfile.therapist_id.in_(ids)))}
    starts = ensure_tz(reservation.starts_at)
    ends = ensure_tz(reservation.ends_at)

    if reservation.status == "NEEDS_ATTENTION":
        text = notices.needs_attention_message(first_name, service_name)
        return [{"target": "cliente", "label": f"Resolver con {first_name}", "phone": customer.phone if customer else None, "text": text}]

    targets = [{
        "target": "cliente",
        "label": f"Cliente: {first_name}",
        "phone": customer.phone if customer else None,
        "text": notices.customer_message(first_name, service_name, [team.get(i, i) for i in ids], starts, reservation.deposit_amount, calendar_url(reservation.id)),
    }]
    for therapist_id in ids:
        name = team.get(therapist_id, therapist_id)
        partners = [team.get(i, i) for i in ids if i != therapist_id]
        targets.append({
            "target": f"masajista:{therapist_id}",
            "label": f"Masajista: {name}",
            "phone": phones.get(therapist_id),
            "text": notices.therapist_message(name, service_name, first_name, starts, ends, partners),
        })
    return targets


def _confirmation_tasks(db: Session, day: date, checks: dict) -> list[dict]:
    """Una tarea por cita pagada que aún no se confirma: aparece hoy y se queda hasta que se envía."""
    start = datetime(day.year, day.month, day.day, tzinfo=TZ)
    rows = db.scalars(select(Reservation).where(Reservation.status.in_(CONFIRM_STATUSES)).order_by(Reservation.starts_at)).all()
    sent = {(row.reservation_id, row.target): row for row in db.scalars(select(ReservationNotice))}
    tasks = []
    for reservation in rows:
        if ensure_tz(reservation.ends_at) < start:
            continue
        key = f"{CONFIRM_PREFIX}{reservation.id}"
        own = checks.get(key)
        targets = _confirmation_targets(db, reservation)
        items = []
        for target in targets:
            notice = sent.get((reservation.id, target["target"]))
            items.append({
                "target": target["target"],
                "label": target["label"],
                "href": notices.sms_link(target["phone"], target["text"]),
                "segments": notices.sms_segments(target["text"]),
                "text": target["text"],
                "sentAt": notice.sent_at.replace(tzinfo=timezone.utc).isoformat() if notice else None,
            })
        all_sent = all(item["sentAt"] for item in items)
        last_sent = max((sent[(reservation.id, t["target"])].sent_on for t in targets), default=None) if all_sent else None
        if last_sent and not own and last_sent < day.isoformat():
            continue  # ya se confirmó en un día anterior
        status = own.status if own else ("hecho" if all_sent else "pendiente")
        starts = ensure_tz(reservation.starts_at)
        service = db.get(Service, reservation.service_id)
        attention = reservation.status == "NEEDS_ATTENTION"
        tasks.append({
            "key": key,
            "label": f"{'Resolver' if attention else 'Confirmar'} cita: {service.name if service else reservation.service_id}, {notices.day_label(starts)} a las {notices.time_label(starts)}",
            "minutes": 5,
            "shift": "apertura",
            "shiftLabel": ops.SHIFTS["apertura"],
            "detail": "El horario se ocupó mientras pagaba: ofrece otro horario o la devolución." if attention else "Pago recibido. Envía cada mensaje por SMS desde el celular.",
            "zones": [], "posts": [], "supplies": [], "evidence": [], "zonesWithoutPoints": [],
            "notices": items,
            "status": status,
            "reason": own.reason if own else None,
        })
    return tasks


def record_notice(db: Session, reservation_id: str, target: str) -> dict:
    reservation = db.get(Reservation, reservation_id)
    if not reservation or reservation.status not in CONFIRM_STATUSES:
        raise NotFoundError("Cita no encontrada")
    if target not in {row["target"] for row in _confirmation_targets(db, reservation)}:
        raise ValidationError("A esa persona no se le avisa de esta cita")
    if not db.scalar(select(ReservationNotice).where(ReservationNotice.reservation_id == reservation_id, ReservationNotice.target == target)):
        db.add(ReservationNotice(id=str(uuid.uuid4()), reservation_id=reservation_id, target=target, sent_on=today().isoformat()))
        db.commit()
    return day_overview(db, today())


def calendar_for(db: Session, reservation_id: str) -> str:
    reservation = db.get(Reservation, reservation_id)
    if not reservation or reservation.status != "CONFIRMED":
        raise NotFoundError("Cita no encontrada")
    service = db.get(Service, reservation.service_id)
    return notices.calendar_file(
        reservation.id, service.name if service else reservation.service_id,
        ensure_tz(reservation.starts_at), ensure_tz(reservation.ends_at), (reservation.created_at or datetime.utcnow()).replace(tzinfo=timezone.utc),
    )
