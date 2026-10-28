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

# Cómo se realiza cada masaje (carta "Servicios y equipo" de SSENSUUM).
SERVICE_DETAILS = {
    "massage-special": "Un masaje hecho a tu medida: combinas diferentes técnicas y presiones en una misma sesión, y decides en qué zonas enfocarla: pies, espalda, piernas, glúteos y más.",
    "swedish": "Se aplica con aceites sobre todo el cuerpo. El terapeuta combina deslizamientos, amasamiento, fricción y percusión en movimientos largos y rítmicos. La presión es ligera a media para soltar tensión superficial, activar la circulación e inducir calma.",
    "descontracturante": "Se localizan nudos y contracturas (cuello, hombros, lumbar). Se trabaja con presión sostenida, amasamiento profundo y estiramientos cortos para liberar el músculo acortado y devolver movilidad.",
    "four-hands": "Dos terapeutas trabajan tu cuerpo al mismo tiempo, en espejo y al mismo ritmo. Al recibir dos estímulos a la vez, el cuerpo deja de seguir el movimiento y se suelta antes. Eliges a los dos terapeutas al reservar.",
    "deep-tissue": "Presión lenta y precisa sobre capas profundas y fascia. Se usa el antebrazo, los nudillos o el pulgar siguiendo la fibra muscular. Ideal para dolor crónico, postura y recuperación.",
    "lymphatic": "Maniobras muy suaves, rítmicas y unidireccionales que siguen el flujo de la linfa hacia los ganglios. No es un masaje fuerte: estimula la eliminación de líquidos y reduce la inflamación.",
    "sports": "Combina amasamiento, fricción transversal, movilizaciones y estiramientos. Se adapta a antes de competir (activar) o después del esfuerzo (recuperar), con enfoque en los grupos musculares de carga.",
    "thai": "Sobre colchoneta o camilla, con ropa cómoda. El terapeuta usa palmas, pulgares y su propio peso para comprimir, estirar y abrir líneas de energía. Incluye posturas pasivas de yoga.",
    "couples-massage": "Dos personas en la misma cabina, al mismo tiempo, cada quien con su terapeuta. Se trabaja la ruta completa de una hora en paralelo, con la música y la luz compartidas. Eligen a sus dos terapeutas al reservar.",
    "aromatherapy": "Se elige una mezcla de aceites esenciales según el objetivo: calma, energía o respiración. El masaje sueco se realiza con ese aceite y el aroma acompaña la sesión.",
    "bamboo": "Cañas de bambú templadas se ruedan y presionan sobre la musculatura. El cilindro permite una presión uniforme y profunda, deshace adherencias y deja una sensación de apertura.",
}

# Equipo con el que arranca una base nueva. Después, altas, bajas y fotos se
# manejan desde Recursos humanos: el arranque solo agrega a quien falte.
THERAPISTS = [
    {
        "id": "aleman",
        "name": "Alemán",
        "photo_url": "/ssensuum/equipo/aleman.jpg",
        "strengths": "Cercanía · Confianza · Calma",
        "bio": "Su trato cálido y relajado te hace sentir en confianza desde el primer momento. Alemán crea un ambiente ligero y sin prisas, "
        "ideal si buscas desconectarte, soltar el estrés y disfrutar de una sesión cercana y amable.",
    },
    {
        "id": "mazer",
        "name": "Mazer",
        "photo_url": "/ssensuum/equipo/mazer.jpg",
        "strengths": "Serenidad · Detalle · Escucha",
        "bio": "De presencia serena y mirada atenta, Mazer trabaja con calma y cuidado en cada movimiento. Escucha lo que tu cuerpo necesita "
        "y guía la sesión con paciencia, perfecta para quienes buscan una experiencia pausada y reparadora.",
    },
    {
        "id": "jessy",
        "name": "Jessy",
        "photo_url": "/ssensuum/equipo/jessy.jpg",
        "strengths": "Enfoque · Discreción · Constancia",
        "bio": "Jessy transmite enfoque y seriedad profesional. Respeta tus tiempos y tu espacio, y mantiene un ritmo constante durante "
        "toda la sesión: ideal si valoras la discreción y un masaje sin distracciones.",
    },
    {
        "id": "dany",
        "name": "Dany",
        "photo_url": "/ssensuum/equipo/dany.jpg",
        "strengths": "Seguridad · Energía · Calidez",
        "bio": "Seguro y cercano a la vez, Dany combina energía y calidez en cada sesión. Su confianza te hace sentir en buenas manos, "
        "ideal si buscas liberar la tensión acumulada y terminar la sesión con energía renovada.",
    },
    {
        "id": "jairo",
        "name": "Jairo",
        "photo_url": "/ssensuum/equipo/jairo.jpg",
        "strengths": "Equilibrio · Amabilidad · Atención",
        "bio": "Amable y de trato tranquilo, Jairo encuentra el equilibrio entre relajación y bienestar. Está atento a cada detalle de tu "
        "comodidad y adapta la sesión a tu ritmo para que vivas una experiencia a tu medida.",
    },
    {
        "id": "borja",
        "name": "Borja",
        "photo_url": "/ssensuum/equipo/borja.jpg",
        "strengths": "Profesionalismo · Técnica · Puntualidad",
        "bio": "Formado en el trato profesional y la presentación impecable, Borja transmite orden y seguridad desde que entras a la sala. "
        "Trabaja con técnica cuidada y atención constante, ideal si buscas una sesión seria, puntual y bien ejecutada.",
    },
    {
        "id": "kevin",
        "name": "Kevin",
        "photo_url": "/ssensuum/equipo/kevin.jpg",
        "strengths": "Alegría · Soltura · Trato",
        "bio": "De trato ligero y buen ánimo, Kevin hace que la primera visita se sienta cómoda desde que entras. Trabaja con soltura y "
        "la conversación justa, sin perder la seriedad de la sesión.",
        "is_new": True,
    },
    {
        "id": "paul",
        "name": "Paul",
        "photo_url": "/ssensuum/equipo/paul.jpg",
        "strengths": "Aplomo · Firmeza · Disciplina",
        "bio": "Serio y de mirada directa, Paul transmite aplomo desde el primer saludo. Trabaja con firmeza y método, buena opción si "
        "buscas una sesión de presión alta y manos seguras.",
        "is_new": True,
    },
    {
        "id": "richy",
        "name": "Richy",
        "photo_url": "/ssensuum/equipo/richy.jpg",
        "strengths": "Ritmo · Paciencia · Entrega",
        "bio": "De trato tranquilo y ritmo parejo, Richy trabaja sin prisa y sostiene la presión que acordaron de principio a fin. "
        "Buena opción si prefieres una sesión constante, sin cambios bruscos.",
        "is_new": True,
    },
    {
        "id": "braulio",
        "name": "Braulio",
        "photo_url": "/ssensuum/equipo/braulio.jpg",
        "strengths": "Carácter · Precisión · Actitud",
        "bio": "De carácter decidido y trato frontal, Braulio pregunta lo necesario y se pone a trabajar. Buena opción si buscas una "
        "sesión de presión firme, directa y sin rodeos.",
        "is_new": True,
    },
]


def seed(db: Session) -> None:
    has_services = db.scalar(select(Service.id).limit(1))
    if not has_services:
        db.add_all(SERVICES)
        db.flush()

    sync_therapists(db)
    sync_service_details(db)

    db.commit()


def sync_therapists(db: Session) -> None:
    for row in THERAPISTS:
        if db.get(Therapist, row["id"]):
            continue
        db.add(Therapist(
            id=row["id"],
            name=row["name"],
            photo_url=row.get("photo_url", ""),
            strengths=row.get("strengths", ""),
            bio=row.get("bio"),
            is_new=row.get("is_new", False),
            active=True,
        ))


def sync_service_details(db: Session) -> None:
    for service_id, details in SERVICE_DETAILS.items():
        service = db.get(Service, service_id)
        if service:
            service.details = details
