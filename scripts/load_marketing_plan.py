#!/usr/bin/env python3
"""Carga en el calendario de Marketing el plan del 9 de noviembre al 6 de diciembre de 2026.

Cada publicación lleva su objetivo y un prompt listo para pegar en una IA.
Uso: python3 scripts/load_marketing_plan.py --api http://127.0.0.1:8100
Se puede correr varias veces: lo que ya está (misma fecha y titular) no se duplica ni se sobrescribe.
"""

import argparse
import json
import urllib.parse
import urllib.request

FROM, TO = "2026-11-09", "2026-12-06"
QUIZ = "Haz el quiz y descubre qué sesión va contigo (enlace en la bio)."
CHOOSE = "Elige a tu terapeuta (enlace en la bio)."
WHATSAPP = "Resuelve tus dudas por WhatsApp: 33 1068 1307."

BRAND = """SSENSUUM es un club privado de masaje para hombres en la Col. Americana, Guadalajara (Mexicaltzingo 2122-B). Abre todos los días de 9:00 a.m. a 8:30 p.m.
Promesa: "Tú eliges quién te atiende". El cliente elige terapeuta, técnica, presión y zonas.
Datos que sí puedes usar:
- Masaje especial SSENSUUM: 60 minutos, $1,500. Se aparta con $300 que se descuentan del total. Se reserva con 3 horas de anticipación.
- Tres pasos: eliges terapeuta y técnica, apartas, llegas. Hay estacionamiento en los cajones 1, 2 y 3, frente al club.
- Si la presión o el ambiente no son lo esperado, se ajusta en los primeros 10 minutos.
- La visita es confidencial. El terapeuta puede ajustar o detener la sesión si algo no se siente bien.
Público: hombres de Guadalajara que nunca han ido a un club así o que tienen dudas sobre quién los atiende y qué pasa ahí.
Tono: sobrio, directo y cálido. Frases cortas, en español de México y hablando de "tú"."""

VISUAL = """Línea gráfica "La Ficha": toda pieza lleva una franja con las opciones de la sesión y una seleccionada, como en el quiz del sitio.
- Colores: crema #f6efe7 y #ecdccb, café #633725 y #3e2419.
- Tipografía: DM Serif Display para el titular (máximo 7 palabras) y Karla para la ficha.
- Imagen: manos, texturas, cabina vacía y retratos con uniforme, con luz cálida.
- En video, la ficha va abajo pero por encima de la zona que tapan los botones de Reels y TikTok."""

LIMITS = """- Nada sugerente: sin torsos aceitados, sin dobles sentidos, sin insinuar nada más allá de un masaje profesional.
- Sin promesas de salud: di "para soltar tensión", nunca "cura", "elimina" ni "trata".
- No inventes testimonios, cifras, precios, promociones ni datos del terapeuta. Si falta un dato, escribe [FALTA: qué dato] y sigue.
- No muestres clientes ni los describas de forma identificable.
- No generes con IA la cara ni el cuerpo de personas reales: para el equipo se usan sus fotos reales, con autorización de imagen firmada.
- No menciones medicina estética."""

TASKS = {
    "reel": """Escribe un Reel vertical de 15 a 25 segundos:
1. Tres ganchos alternativos para los primeros 2 segundos; marca el que recomiendas y di por qué.
2. Guion en tabla, toma por toma: tiempo, imagen, texto en pantalla y voz o sonido.
3. El momento en que aparece La Ficha y su texto exacto.
4. Texto de la publicación: máximo 150 caracteres, más el llamado a la acción.
5. Ajustes para TikTok, si hacen falta.
6. Si alguna toma es solo de objetos o del lugar, un prompt en inglés para generarla con IA de video.""",
    "carrusel": """Escribe un carrusel vertical 4:5 de 5 a 7 láminas:
1. Lámina por lámina: titular (máximo 7 palabras), texto (máximo 20 palabras) y qué imagen lleva.
2. La primera lámina debe detener el scroll; la última lleva La Ficha y el llamado a la acción.
3. Texto de la publicación: máximo 150 caracteres, más el llamado a la acción.
4. Un prompt en inglés para generar con IA cada fondo que sea solo de objetos o del lugar.""",
    "foto": """Escribe una pieza fija vertical 4:5:
1. Texto exacto sobre la imagen y su jerarquía.
2. Dirección de arte: encuadre, luz y lugar de La Ficha.
3. Texto de la publicación: máximo 150 caracteres, más el llamado a la acción.
4. Si la imagen es solo de objetos o del lugar, un prompt en inglés para generarla con IA.""",
}

OUTPUT_CHECK = """Antes de responder, revisa en silencio: ¿se entiende sin sonido?, ¿cumple el objetivo y una sola idea?, ¿respeta cada restricción?, ¿el titular tiene máximo 7 palabras? Corrige lo que no cumpla.
Responde solo con los entregables, numerados, sin explicar tu proceso."""

POSTS = [
    {"date": "2026-11-09", "format": "reel", "pillar": "tecnicas", "title": "Tu cuello ya te avisó.", "ficha": "Zona: espalda y cuello", "cta": QUIZ,
     "objective": "Alcance: detener a quien no te conoce con una molestia que reconoce. Que lo guarde o lo comparta.",
     "angle": "La tensión de cuello y hombros de quien pasa el día sentado o en el celular. Reconocerla primero; el club aparece hasta el final."},
    {"date": "2026-11-11", "format": "carrusel", "pillar": "experiencia", "title": "Tu primera visita, en tres pasos.", "ficha": "Eliges → apartas → llegas", "cta": WHATSAPP,
     "objective": "Confianza: quitar el miedo a lo desconocido mostrando qué pasa desde que eliges hasta que llegas.",
     "angle": "Explicar los tres pasos reales con calma, incluido el anticipo que se descuenta, el estacionamiento y el ajuste en los primeros 10 minutos."},
    {"date": "2026-11-13", "format": "reel", "pillar": "equipo", "title": "Braulio no da rodeos.", "ficha": "Trato: directo y firme", "cta": CHOOSE,
     "objective": "Preferencia: que quien busca presión firme ya tenga un terapeuta en mente.",
     "angle": 'Presentar a Braulio con video real. Fortalezas: carácter, precisión y actitud. Perfil: "De carácter decidido y trato frontal, Braulio pregunta lo necesario y se pone a trabajar. Buena opción si buscas una sesión de presión firme, directa y sin rodeos."'},
    {"date": "2026-11-15", "format": "reel", "pillar": "tecnicas", "title": "Suave, media o firme: ¿cuál es la tuya?", "ficha": "Presión: suave · media · firme", "cta": QUIZ,
     "objective": "Alcance e interacción: una pregunta fácil de contestar que invita a comentar y lleva al quiz.",
     "angle": "Mostrar con manos sobre una superficie neutra la diferencia entre las tres presiones y cerrar preguntándole cuál prefiere."},
    {"date": "2026-11-16", "format": "reel", "pillar": "tecnicas", "title": "Si hoy descansas, que sea de verdad.", "ficha": "Objetivo: desconectado de todo", "cta": QUIZ,
     "objective": "Alcance: aprovechar el día feriado para mostrar el masaje como descanso real, no como lujo.",
     "angle": "Es lunes feriado en México y el club abre todos los días. Contraste entre descansar viendo el celular y desconectarse de verdad durante una hora."},
    {"date": "2026-11-19", "format": "foto", "pillar": "fechas", "title": "Día del Hombre: hoy también te toca.", "ficha": "Tú eliges", "cta": CHOOSE,
     "objective": "Identificación: reforzar que este lugar está pensado para él, usando una fecha con sentido para el club y sin descuento.",
     "angle": "19 de noviembre, Día Internacional del Hombre. Mensaje breve y sobrio sobre darse un rato para uno mismo. Sin promoción y sin estereotipos de masculinidad."},
    {"date": "2026-11-20", "format": "reel", "pillar": "equipo", "title": "Mazer no tiene prisa.", "ficha": "Trato: tranquilo y pausado", "cta": CHOOSE,
     "objective": "Preferencia: que quien quiere una sesión pausada identifique a su terapeuta antes de reservar.",
     "angle": 'Presentar a Mazer con video real y ritmo lento. Fortalezas: serenidad, detalle y escucha. Perfil: "De presencia serena y mirada atenta, Mazer trabaja con calma y cuidado en cada movimiento. Escucha lo que tu cuerpo necesita y guía la sesión con paciencia."'},
    {"date": "2026-11-22", "format": "carrusel", "pillar": "experiencia", "title": "Lo que preguntas antes de venir.", "ficha": "Tu visita es confidencial", "cta": WHATSAPP,
     "objective": "Confianza: contestar las dudas que frenan la primera reserva, sobre todo privacidad y pago.",
     "angle": "Responde cinco preguntas: ¿qué pasa si cancelo?, ¿cómo pago?, ¿qué aparece en mi estado de cuenta?, ¿puedo cambiar de terapeuta?, ¿qué tengo que llevar? Usa solo estas respuestas confirmadas por el club: [PEGA AQUÍ LAS RESPUESTAS]."},
    {"date": "2026-11-23", "format": "reel", "pillar": "tecnicas", "title": "Entrenas duro. ¿Cuándo recuperas?", "ficha": "Objetivo: recuperado del ejercicio", "cta": QUIZ,
     "objective": "Alcance a un público nuevo: hombres que entrenan y ya cuidan su cuerpo.",
     "angle": "Hablarle a quien entrena: planea el gimnasio, pero no la recuperación. Mencionar el masaje deportivo, pre o post esfuerzo, sin prometer resultados físicos."},
    {"date": "2026-11-25", "format": "reel", "pillar": "equipo", "title": "Con Dany, en confianza desde el saludo.", "ficha": "Trato: cercano y cálido", "cta": CHOOSE,
     "objective": "Preferencia: bajar la tensión de quien va por primera vez mostrando un trato cercano.",
     "angle": 'Presentar a Dany con video real. Fortalezas: seguridad, energía y calidez. Perfil: "Seguro y cercano a la vez, Dany combina energía y calidez en cada sesión. Su confianza te hace sentir en buenas manos."'},
    {"date": "2026-11-27", "format": "carrusel", "pillar": "tecnicas", "title": "Sueco, descontracturante o tejido profundo.", "ficha": "Presión: de suave a firme", "cta": QUIZ,
     "objective": "Consideración: ayudarle a entender las técnicas para que elija con criterio. Contenido para guardar.",
     "angle": "Comparar tres técnicas de la carta. Sueco: presión ligera a media para soltar tensión. Descontracturante: presión sostenida sobre nudos y contracturas. Tejido profundo: presión lenta sobre capas profundas. Todas: 60 minutos, $1,500."},
    {"date": "2026-11-29", "format": "foto", "pillar": "testimonios", "title": "Lo que dicen del club.", "ficha": "Reseña real", "cta": CHOOSE,
     "objective": "Prueba: confirmar con la voz de un cliente real que la experiencia cumple lo que promete.",
     "angle": 'Usa textual esta reseña, publicada con permiso y sin datos que identifiquen al cliente: [PEGA AQUÍ LA RESEÑA REAL]. Si no hay reseña con permiso, no la inventes: propón en su lugar una pieza de Experiencia titulada "Tres cosas que puedes pedir en tu sesión" (terapeuta, presión y zonas).'},
    {"date": "2026-11-30", "format": "reel", "pillar": "tecnicas", "title": "El cierre de año también pesa.", "ficha": "Zona: espalda y cuello", "cta": QUIZ,
     "objective": "Alcance con intención: conectar el estrés de fin de año con reservar ahora.",
     "angle": "La acumulación de pendientes y compromisos de diciembre se siente en espalda y hombros. Cerrar invitando a apartar su hora antes de que se llene su propia agenda."},
    {"date": "2026-12-02", "format": "reel", "pillar": "equipo", "title": "Borja: técnica cuidada, sin distracciones.", "ficha": "Trato: serio y profesional", "cta": CHOOSE,
     "objective": "Preferencia: dar seguridad a quien busca seriedad y puntualidad.",
     "angle": 'Presentar a Borja con video real. Fortalezas: profesionalismo, técnica y puntualidad. Perfil: "Formado en el trato profesional y la presentación impecable, Borja transmite orden y seguridad desde que entras a la sala."'},
    {"date": "2026-12-04", "format": "reel", "pillar": "experiencia", "title": "Así te espera tu cabina.", "ficha": "Horario: mañana · tarde · noche", "cta": CHOOSE,
     "objective": "Deseo y confianza: mostrar el lugar real para que se imagine ahí y dé el paso de reservar.",
     "angle": "Recorrido real y lento por el acceso y una cabina vacía, con detalles de toallas, luz y aceites. Sin personas y sin voz en off explicativa."},
    {"date": "2026-12-06", "format": "reel", "pillar": "equipo", "title": "Jessy: enfoque y discreción.", "ficha": "Trato: serio y profesional", "cta": CHOOSE,
     "objective": "Preferencia: cerrar el mes con el atributo que más le importa a este cliente, la discreción.",
     "angle": 'Presentar a Jessy con video real. Fortalezas: enfoque, discreción y constancia. Perfil: "Jessy transmite enfoque y seriedad profesional. Respeta tus tiempos y tu espacio, y mantiene un ritmo constante durante toda la sesión."'},
]


def build_prompt(post: dict) -> str:
    return f"""# Rol
Eres director creativo y copywriter senior de redes sociales, especializado en marcas locales de bienestar para hombres.

# Marca
{BRAND}

# Esta publicación
- Titular: {post["title"]}
- Objetivo: {post["objective"]}
- Ángulo: {post["angle"]}
- La Ficha: {post["ficha"]}
- Llamado a la acción: {post["cta"]}
- Redes: Instagram primero; se replica en TikTok y Facebook.

# Línea gráfica
{VISUAL}

# Tarea
{TASKS[post["format"]]}

# Restricciones
{LIMITS}

# Formato de salida y revisión
{OUTPUT_CHECK}"""


def plan() -> list[dict]:
    return [
        {
            "channel": "instagram",
            "publishOn": post["date"],
            "status": "idea",
            "format": post["format"],
            "pillar": post["pillar"],
            "title": post["title"],
            "objective": post["objective"],
            "aiPrompt": build_prompt(post),
        }
        for post in POSTS
    ]


def request(method: str, url: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True, help="URL de la API, por ejemplo http://127.0.0.1:8100")
    api = parser.parse_args().api.rstrip("/")

    query = urllib.parse.urlencode({"from": FROM, "to": TO})
    existing = {(row["publishOn"], row["title"]) for row in request("GET", f"{api}/admin/marketing/posts?{query}")}
    created = 0
    for post in plan():
        if (post["publishOn"], post["title"]) in existing:
            continue
        saved = request("POST", f"{api}/admin/marketing/posts", post)
        if saved.get("aiPrompt") != post["aiPrompt"]:
            # Una API sin desplegar ignora los campos nuevos: se borra lo creado y se detiene.
            request_delete = urllib.request.Request(f"{api}/admin/marketing/posts/{saved['id']}", method="DELETE")
            urllib.request.urlopen(request_delete, timeout=15).close()
            raise SystemExit("La API no guardó el prompt: despliega la versión nueva antes de cargar el plan.")
        created += 1
    print(f"Creadas: {created}. Ya existían: {len(POSTS) - created}. Total del plan: {len(POSTS)}.")


if __name__ == "__main__":
    main()
