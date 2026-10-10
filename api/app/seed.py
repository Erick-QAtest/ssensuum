from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Service, Therapist


SERVICES = [
    Service(
        id="massage-special",
        name="Masaje especial SSENSUUM",
        category="Masajes",
        description="Tú eliges técnicas, presión y zonas.",
        duration_minutes=60,
        public_price=1500,
        member_price=1200,
        deposit=300,
        therapists_required=1,
    ),
    Service(id="swedish", name="Masaje sueco relajante", category="Masajes", description="Presión ligera a media para soltar tensión.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="descontracturante", name="Masaje descontracturante", category="Masajes", description="Presión sostenida sobre nudos y contracturas.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="four-hands", name="Masaje a 4 manos", category="Masajes", description="Dos terapeutas trabajan al mismo tiempo sobre tu cuerpo.", duration_minutes=60, public_price=3000, member_price=2400, deposit=600, therapists_required=2),
    Service(id="deep-tissue", name="Tejido profundo", category="Masajes", description="Presión lenta sobre capas profundas.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="lymphatic", name="Drenaje linfático", category="Masajes", description="Maniobras suaves y rítmicas.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="sports", name="Masaje deportivo", category="Masajes", description="Pre o post esfuerzo, en grupos de carga.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="thai", name="Masaje thai", category="Masajes", description="Estiramientos y posturas sobre colchoneta.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="couples-massage", name="Masaje de parejas", category="Masajes", description="En la misma cabina y al mismo tiempo, cada quien con su terapeuta.", duration_minutes=60, public_price=3000, member_price=2400, deposit=600, therapists_required=2),
    Service(id="aromatherapy", name="Aromaterapia", category="Masajes", description="Aceites esenciales según tu objetivo.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="bamboo", name="Masaje con bambú", category="Masajes", description="Cañas templadas para presión uniforme.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),

    Service(id="haircut", name="Corte", category="Barbería", description="Asesoría de estilo, corte y peinado.", duration_minutes=60, public_price=400, member_price=300, deposit=300, therapists_required=1),
    Service(id="beard", name="Barba completa", category="Barbería", description="Contornos, navaja y toalla caliente.", duration_minutes=40, public_price=350, member_price=250, deposit=300, therapists_required=1),
    Service(id="barber-package", name="Paquete completo", category="Barbería", description="Corte, barba, mascarilla de arcilla y masaje con máquina en hombros y espalda alta.", duration_minutes=120, public_price=800, member_price=500, deposit=300, therapists_required=1),
    Service(id="pedicure", name="Pedicura", category="Barbería", description="Limpieza, uñas, callosidades e hidratación.", duration_minutes=90, public_price=650, member_price=500, deposit=300, therapists_required=1),
    Service(id="hydrafacial", name="Hidrafacial con extracción", category="Barbería", description="Limpieza profunda con hidratación y extracción.", duration_minutes=80, public_price=950, member_price=800, deposit=300, therapists_required=1),

    Service(id="botox", name="Botox", category="Medicina estética", description="Líneas de expresión en frente, entrecejo y contorno de ojos.", duration_minutes=60, public_price=2600, member_price=2050, deposit=300, therapists_required=1),
    Service(id="aesthetic-lips", name="Ácido hialurónico · labios o mentón", category="Medicina estética", description="Volumen y contorno, por jeringa.", duration_minutes=60, public_price=3000, member_price=2400, deposit=300, therapists_required=1),
    Service(id="aesthetic-jaw", name="Ácido hialurónico · mandíbula", category="Medicina estética", description="Definición del ángulo mandibular.", duration_minutes=60, public_price=6500, member_price=5200, deposit=300, therapists_required=1),
    Service(id="aesthetic-nose", name="Ácido hialurónico · nariz", category="Medicina estética", description="Perfilado de nariz sin cirugía.", duration_minutes=60, public_price=3800, member_price=3000, deposit=300, therapists_required=1),
    Service(id="aesthetic-laser", name="Láser", category="Medicina estética", description="Cicatrices, manchas y peelings, por sesión.", duration_minutes=60, public_price=1500, member_price=1200, deposit=300, therapists_required=1),
    Service(id="aesthetic-morfosis", name="Reducción de medidas", category="Medicina estética", description="Protocolo Morfosis, por sesión.", duration_minutes=60, public_price=1350, member_price=1050, deposit=300, therapists_required=1),
    Service(id="aesthetic-biostimulation", name="Bioestimulación", category="Medicina estética", description="PDRN de salmón, Radiesse, Sculptra o Juvelook. Desde.", duration_minutes=60, public_price=2300, member_price=1800, deposit=300, therapists_required=1),
    Service(id="aesthetic-removal", name="Retiro de tatuajes y lunares", category="Medicina estética", description="Según tamaño. Desde.", duration_minutes=60, public_price=600, member_price=450, deposit=300, therapists_required=1),
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
