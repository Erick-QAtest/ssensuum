from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Service, Therapist


SERVICES = [
    Service(
        id="massage-special",
        name="Masaje especial",
        category="Masajes",
        description="Sesión de 1 hora que combina técnicas, presión y zonas según lo que necesitas.",
        duration_minutes=60,
        public_price=1500,
        member_price=1200,
        deposit=300,
        therapists_required=1,
    ),
    Service(
        id="deep-tissue",
        name="Tejido profundo",
        category="Masajes",
        description="Trabajo de presión profunda enfocado en tensión muscular persistente.",
        duration_minutes=60,
        public_price=1500,
        member_price=1200,
        deposit=300,
        therapists_required=1,
    ),
    Service(
        id="four-hands",
        name="Masaje 4 manos",
        category="Masajes",
        description="Dos terapeutas trabajan de forma coordinada durante una sesión de una hora.",
        duration_minutes=60,
        public_price=3000,
        member_price=2600,
        deposit=600,
        therapists_required=2,
    ),
    Service(
        id="couples-massage",
        name="Masaje de parejas",
        category="Masajes",
        description="Dos personas reciben masaje al mismo tiempo con dos terapeutas.",
        duration_minutes=60,
        public_price=3000,
        member_price=2600,
        deposit=600,
        therapists_required=2,
    ),
    Service(
        id="beard-cut",
        name="Corte y barba",
        category="Barbería",
        description="Servicio de barbería para corte y arreglo de barba.",
        duration_minutes=60,
        public_price=400,
        member_price=300,
        deposit=300,
        therapists_required=1,
    ),
    Service(
        id="aesthetic-session",
        name="Sesión estética",
        category="Medicina estética",
        description="Valoración y sesión estética según indicación profesional.",
        duration_minutes=60,
        public_price=2600,
        member_price=2050,
        deposit=300,
        therapists_required=1,
    ),
]

THERAPISTS = [
    Therapist(id="alex", name="Alex", strengths="Descontracturante · Tejido profundo · Deportivo"),
    Therapist(id="diego", name="Diego", strengths="Sueco relajante · Aromaterapia · Deportivo"),
    Therapist(id="mateo", name="Mateo", strengths="Tejido profundo · 4 manos · Parejas"),
    Therapist(id="leo", name="Leo", strengths="Relajación · Drenaje · Masaje especial"),
]


def seed(db: Session) -> None:
    has_services = db.scalar(select(Service.id).limit(1))
    if not has_services:
        db.add_all(SERVICES)

    has_therapists = db.scalar(select(Therapist.id).limit(1))
    if not has_therapists:
        db.add_all(THERAPISTS)

    db.commit()
