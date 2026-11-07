"""Día operativo de recepción: qué toca cada día, por zona y por turno, y cuándo se puede cerrar.

El reparto sale de un ciclo de dos semanas calculado para que ningún día quede sobrecargado
(entre 348 y 380 minutos de tareas fijas por día, sin contar servicios).
"""

from dataclasses import dataclass, field
import hashlib
import math
from datetime import date, timedelta
from typing import Optional

# Tipos de punto en la foto de una zona, con el color con el que se dibujan.
POINT_KINDS = {"limpiar": "Limpiar", "rellenar": "Rellenar", "regar": "Regar", "bolsa": "Revisar bolsa"}

# Zonas del club. La foto y los puntos se agregan desde la pantalla de Operación.
ZONES = [
    ("sala", "Sala de espera"),
    ("antesala", "Antesala y escaleras"),
    ("bano-1", "Baño 1"),
    ("bano-2", "Baño 2"),
    ("bano-3", "Baño 3"),
    ("cocina", "Cocina"),
    ("cabina-masaje", "Cabina de masaje"),
    ("cabina-faciales", "Cabina de faciales"),
    ("cabina-estetica", "Cabina de medicina estética"),
    ("terraza", "Plantas y terraza"),
    ("bodega", "Bodega e insumos"),
]
ZONE_IDS = [zone_id for zone_id, _ in ZONES]
BATHROOMS = ["bano-1", "bano-2", "bano-3"]
CABINS = ["cabina-masaje", "cabina-faciales", "cabina-estetica"]

SHIFTS = {"apertura": "Turno de apertura", "cierre": "Turno de cierre"}
STATUSES = {"hecho": "Hecho", "no_se_pudo": "No se pudo"}

# Lunes de la semana A del ciclo; las semanas alternan A y B a partir de aquí.
CYCLE_START = date(2026, 11, 9)
WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


@dataclass(frozen=True)
class Task:
    key: str
    label: str
    minutes: int
    shift: str
    # Zonas cuya foto se recorre punto por punto; vacío = tarea simple.
    zones: tuple = ()
    # Solo estos tipos de punto (la ronda diaria revisa rellenos y bolsas, no limpia a fondo).
    kinds: tuple = ()
    # Días de la semana (0 = lunes); vacío = todos los días.
    weekdays: tuple = ()
    # "A" o "B" para las tareas quincenales.
    cycle_week: Optional[str] = None
    detail: str = ""
    # "posts": se completa sola cuando las publicaciones del día quedan publicadas en Marketing.
    source: str = ""
    tags: tuple = field(default_factory=tuple)


ALL = tuple(ZONE_IDS)
TASKS = [
    # Todos los días: 225 minutos.
    Task("abrir", "Abrir el club", 20, "apertura", detail="Luces, música, aromatizante y agua para clientes."),
    Task("agenda", "Revisar agenda y horarios de llegada de terapeutas", 10, "apertura",
         detail="Cada terapeuta puede estar desde 30 minutos antes hasta 30 minutos después de cada servicio."),
    Task("ronda-manana", "Ronda de limpieza", 35, "apertura", zones=("bano-1", "bano-2", "bano-3", "sala", "antesala", "cocina"),
         kinds=("rellenar", "bolsa"), detail="Rellena jabón y papel y revisa las bolsas de basura."),
    Task("confirmar", "Confirmar las citas de mañana", 30, "apertura"),
    Task("mensajes", "Responder mensajes y comentarios en redes", 15, "apertura"),
    Task("verificar-insumos", "Verificar insumos para los servicios de mañana", 15, "cierre"),
    Task("ronda-tarde", "Ronda de baños", 20, "cierre", zones=tuple(BATHROOMS), kinds=("rellenar", "bolsa")),
    Task("entradas", "Registrar entradas y salidas de terapeutas", 15, "cierre"),
    Task("cierre", "Cierre: cabinas, basura, conteo rápido y registro de servicios", 65, "cierre",
         detail="Deja las 3 cabinas listas, vacía los 8 botes, cuenta los insumos de alta rotación y registra los servicios del día."),
    # Publicaciones: solo los días con publicaciones en el calendario de Marketing.
    Task("publicar", "Publicar en redes", 20, "apertura", source="posts", detail="Se completa al marcar cada publicación como publicada en Marketing."),
    # Lunes
    Task("metricas", "Capturar métricas de la semana", 20, "apertura", weekdays=(0,), detail="Seguidores, alcance, interacciones y clics de cada red."),
    Task("riego-lun", "Riego de plantas", 25, "apertura", zones=ALL, kinds=("regar",), weekdays=(0,)),
    Task("aseo-terraza", "Aseo de plantas y terraza", 15, "apertura", zones=("terraza",), weekdays=(0,)),
    Task("aseo-cocina", "Aseo de cocina y refrigerador", 35, "cierre", zones=("cocina",), weekdays=(0,), detail="Incluye tirar lo caducado del refrigerador."),
    Task("aseo-escaleras", "Aseo de escaleras, barandales, puertas y manijas", 30, "cierre", zones=("antesala",), weekdays=(0,)),
    # Martes
    Task("inventario", "Inventario completo", 45, "apertura", weekdays=(1,), detail="Cuenta cada insumo en Operación → Insumos."),
    Task("aseo-bodega", "Aseo de bodega y 8 botes de basura", 45, "apertura", zones=("bodega",), weekdays=(1,)),
    Task("contenido-grabar", "Contenido: grabar con un terapeuta", 60, "cierre", weekdays=(1,),
         detail="Dentro de la ventana de llegada del terapeuta. Solo con su autorización de imagen."),
    # Miércoles
    Task("aseo-sala", "Aseo de sala de espera", 20, "apertura", zones=("sala",), weekdays=(2,)),
    Task("pedido", "Pedido de insumos", 30, "apertura", weekdays=(2,), source="order",
         detail="Pide lo que el sistema marca: así llega antes de que se acabe."),
    Task("contenido-producir-1", "Contenido: producir piezas (1 de 2)", 80, "cierre", weekdays=(2,), detail="Con los prompts de Marketing → Plan y prompts."),
    # Jueves
    Task("riego-jue", "Riego de plantas", 25, "apertura", zones=ALL, kinds=("regar",), weekdays=(3,)),
    Task("agua-flores", "Compra de agua y flores", 30, "apertura", weekdays=(3,)),
    Task("contenido-producir-2", "Contenido: producir piezas (2 de 2)", 80, "cierre", weekdays=(3,)),
    # Viernes
    Task("recibir-pedido", "Recibir y acomodar el pedido", 30, "apertura", weekdays=(4,), detail="Registra lo recibido en Operación → Insumos."),
    # Solo aparece si algún insumo ya no alcanza a esperar al pedido del miércoles.
    Task("compra-urgente", "Compra urgente de insumos", 30, "apertura", source="urgent"),
    Task("contenido-adaptar", "Contenido: adaptar a las 4 redes", 96, "cierre", weekdays=(4,)),
    # Sábado
    Task("aseo-cabinas", "Aseo de las 3 cabinas a fondo", 45, "apertura", zones=tuple(CABINS), weekdays=(5,)),
    Task("aseo-pisos", "Barrer y trapear toda la casa", 60, "apertura", weekdays=(5,), detail="Planta por planta."),
    Task("aseo-vidrios", "Ventanales, vidrios y repisas altas", 50, "cierre", weekdays=(5,)),
    # Domingo
    Task("aseo-banos", "Aseo de los 3 baños a fondo", 45, "apertura", zones=tuple(BATHROOMS), weekdays=(6,)),
    Task("contenido-programar", "Contenido: programar la semana siguiente", 48, "cierre", weekdays=(6,)),
    Task("lavanderia", "Lavandería: entrega y recogida", 40, "apertura", weekdays=(6,), cycle_week="A"),
    Task("aromatizantes", "Cambiar aromatizantes", 10, "cierre", weekdays=(6,), cycle_week="B"),
]
TASKS_BY_KEY = {task.key: task for task in TASKS}


def cycle_week(day: date) -> str:
    return "A" if ((day - CYCLE_START).days // 7) % 2 == 0 else "B"


def tasks_for(day: date, has_posts: bool, has_urgent: bool = False) -> list[Task]:
    """Tareas del día según el día de la semana, la semana del ciclo y el calendario de publicaciones."""
    week = cycle_week(day)
    result = []
    for task in TASKS:
        if task.weekdays and day.weekday() not in task.weekdays:
            continue
        if task.cycle_week and task.cycle_week != week:
            continue
        if task.source == "posts" and not has_posts:
            continue
        if task.source == "urgent" and not has_urgent:
            continue
        result.append(task)
    return result


def point_key(task_key: str, point_id: str) -> str:
    """Un mismo punto se marca por separado en cada tarea (la ronda diaria y el aseo a fondo)."""
    return f"{task_key}@{point_id}"


# --- Insumos ---

ORDER_WEEKDAY = 2  # el pedido semanal es el miércoles
# Insumos iniciales: (id, nombre, unidad, cantidad por compra, días que dura esa compra, días de entrega, precio por compra).
# Salen de la lista de compras del club; el consumo se corrige solo con cada inventario.
SUPPLIES = [
    ("agua", "Agua embotellada para clientes", "rack", 1, 7, 2, None),
    ("aromatizante", "Aromatizante", "pieza", 1, 15, 2, 100),
    ("bolsas-chicas", "Bolsas de basura chicas", "paquete", 1, 15, 2, 100),
    ("bolsas-grandes", "Bolsas de basura grandes", "paquete", 1, 15, 2, 100),
    ("desinfectante", "Desinfectante", "bote", 2, 90, 2, 200),
    ("jabon-polvo", "Jabón en polvo", "bolsa", 1, 90, 2, 100),
    ("fabuloso", "Fabuloso", "bote", 2, 90, 2, 200),
    ("papel-institucional", "Papel higiénico institucional", "caja", 1, 90, 2, 250),
    ("sanitas", "Toallas de papel (Sanitas)", "caja", 1, 90, 2, None),
    ("jabon-manos", "Jabón líquido para manos", "litro", 1, 30, 2, None),
]


def next_order_day(today: date) -> date:
    return today + timedelta(days=(ORDER_WEEKDAY - today.weekday()) % 7)


def projected_stock(stock: float, counted_on: date, received: float, daily_use: float, on: date) -> float:
    """Existencia estimada: último conteo, más lo recibido, menos el consumo diario desde el conteo."""
    return stock + received - daily_use * max(0, (on - counted_on).days)


def supply_plan(estimate: Optional[float], daily_use: float, lead_days: int, safety_days: int, pack_size: float, today: date) -> dict:
    """Cuándo y cuánto pedir para que el insumo nunca baje de su margen de seguridad.

    Se pide en el pedido semanal (miércoles) si, de no pedir, lo siguiente llegaría tarde:
    la existencia al llegar el pedido de la otra semana quedaría por debajo de safety_days de consumo.
    Si ni pidiendo este miércoles alcanza, es compra urgente hoy.
    """
    if estimate is None:
        return {"status": "sin_contar", "orderOn": None, "quantity": None, "daysLeft": None, "runsOutOn": None}
    order_day = next_order_day(today)
    days_left = estimate / daily_use if daily_use > 0 else None
    runs_out = today + timedelta(days=int(days_left)) if days_left is not None else None
    if daily_use <= 0:
        return {"status": "bien", "orderOn": None, "quantity": 0, "daysLeft": None, "runsOutOn": None}

    def stock_on(day: date) -> float:
        return estimate - daily_use * (day - today).days

    arrival_now = order_day + timedelta(days=lead_days)
    arrival_next = arrival_now + timedelta(days=7)
    margin = daily_use * safety_days
    # Lo necesario para llegar con margen hasta que entre el pedido de la semana siguiente.
    needed = daily_use * ((arrival_next - today).days + safety_days) - estimate
    quantity = max(pack_size, math.ceil(needed / pack_size) * pack_size) if needed > 0 else pack_size
    if stock_on(arrival_now) < margin:
        urgent_need = daily_use * ((arrival_next - today).days + safety_days) - estimate
        return {"status": "urgente", "orderOn": today.isoformat(), "quantity": max(pack_size, math.ceil(urgent_need / pack_size) * pack_size),
                "daysLeft": round(days_left, 1), "runsOutOn": runs_out.isoformat()}
    if stock_on(arrival_next) < margin:
        return {"status": "pedir", "orderOn": order_day.isoformat(), "quantity": quantity, "daysLeft": round(days_left, 1), "runsOutOn": runs_out.isoformat()}
    return {"status": "bien", "orderOn": None, "quantity": 0, "daysLeft": round(days_left, 1), "runsOutOn": runs_out.isoformat()}


def smoothed_use(previous: float, observed: float) -> float:
    """El consumo se ajusta con cada inventario: mitad lo que se tenía, mitad lo observado."""
    return round(0.5 * previous + 0.5 * observed, 4)


# --- Evidencia ---

EVIDENCE_DAYS = 60  # las fotos de evidencia se borran después de este tiempo
REVIEWS = {"pendiente": "Sin revisar", "bien": "Bien", "repetir": "Repetir"}


def random_index(day: date, task_key: str, size: int) -> int:
    """Punto al azar para la foto de la ronda: cambia cada día, pero es el mismo durante todo el día."""
    digest = hashlib.sha256(f"{day.isoformat()}:{task_key}".encode()).hexdigest()
    return int(digest, 16) % size
