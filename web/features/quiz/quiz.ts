import type { Service, Therapist } from '../../lib/types';
import { SPECIAL_ID } from '../catalog/content';

export type QuestionId = 'objetivo' | 'presion' | 'zona' | 'trato' | 'horario';
export type Answers = Partial<Record<QuestionId, string>>;
export type Question = {
  id: QuestionId;
  title: string;
  options: { value: string; label: string; hint?: string }[];
};

// Ventanas de horario dentro de 9:00 a 20:30. Los horarios de la API vienen como "HH:MM".
export const TIME_WINDOWS = {
  manana: { label: 'Por la mañana', range: 'Entre 9:00 a.m. y 12:00 p.m.', from: '09:00', to: '11:59' },
  tarde: { label: 'Por la tarde', range: 'Entre 12:00 y 5:00 p.m.', from: '12:00', to: '16:59' },
  noche: { label: 'Por la noche', range: 'Entre 5:00 y 8:30 p.m.', from: '17:00', to: '20:30' },
} as const;
export type TimeWindow = keyof typeof TIME_WINDOWS;

// Estilos de trato y quién los representa, según las fortalezas y bios del equipo.
// Si alguien deja el equipo, el quiz lo salta; si se integra alguien, agrégalo aquí.
export const TRATO_STYLES = {
  cercano: { label: 'Cercano y cálido', hint: 'Para sentirte en confianza desde el saludo', ids: ['aleman', 'dany'] },
  tranquilo: { label: 'Tranquilo y pausado', hint: 'Sin prisas, con calma en cada movimiento', ids: ['mazer', 'jairo'] },
  profesional: { label: 'Serio y profesional', hint: 'Técnica cuidada y sin distracciones', ids: ['borja', 'jessy'] },
  directo: { label: 'Directo y con temple', hint: 'Firme y con buena comunicación', ids: ['chicano'] },
} as const;
type TratoStyle = keyof typeof TRATO_STYLES;

export const QUESTIONS: Question[] = [
  {
    id: 'objetivo',
    title: '¿Cómo quieres salir de tu sesión?',
    options: [
      { value: 'desconectar', label: 'Desconectado de todo' },
      { value: 'tension', label: 'Sin tensión en espalda y cuello' },
      { value: 'recuperar', label: 'Recuperado del ejercicio' },
      { value: 'probar', label: 'Todavía no sé', hint: 'Quiero probar y decidir ahí' },
    ],
  },
  {
    id: 'presion',
    title: '¿Qué presión prefieres?',
    options: [
      { value: 'suave', label: 'Suave' },
      { value: 'media', label: 'Media' },
      { value: 'firme', label: 'Firme' },
      { value: 'ajusta', label: 'Que mi terapeuta la ajuste' },
    ],
  },
  {
    id: 'zona',
    title: '¿Dónde quieres que se enfoque?',
    options: [
      { value: 'espalda', label: 'Espalda y cuello' },
      { value: 'piernas', label: 'Piernas' },
      { value: 'todo', label: 'Todo el cuerpo' },
    ],
  },
  {
    id: 'trato',
    title: '¿Qué trato prefieres?',
    options: [
      ...(Object.keys(TRATO_STYLES) as TratoStyle[]).map((key) => ({
        value: key,
        label: TRATO_STYLES[key].label,
        hint: TRATO_STYLES[key].hint,
      })),
      { value: 'igual', label: 'Me da igual', hint: 'El que tenga espacio en mi horario' },
    ],
  },
  {
    id: 'horario',
    title: '¿A qué hora te acomoda?',
    options: (Object.keys(TIME_WINDOWS) as TimeWindow[]).map((key) => ({
      value: key,
      label: TIME_WINDOWS[key].label,
      hint: TIME_WINDOWS[key].range,
    })),
  },
];

export type MassagePick = { serviceId: string; why: string };

// Recomendación de masaje a partir de objetivo, presión y zona.
export function pickMassage(a: Answers): MassagePick {
  if (a.objetivo === 'probar' || a.presion === 'ajusta') {
    return { serviceId: SPECIAL_ID, why: 'Como todavía no tienes una técnica definida, este se arma contigo al llegar: tú eliges técnicas, presión y zonas.' };
  }
  if (a.zona === 'piernas' && a.presion === 'suave' && a.objetivo !== 'recuperar') {
    return { serviceId: 'lymphatic', why: 'Maniobras suaves y rítmicas, enfocadas en las piernas.' };
  }
  if (a.objetivo === 'recuperar') {
    return { serviceId: 'sports', why: 'Trabaja los grupos musculares que cargaste al entrenar.' };
  }
  if (a.objetivo === 'tension') {
    if (a.presion === 'firme') return { serviceId: 'deep-tissue', why: 'Presión lenta para llegar a la tensión acumulada.' };
    if (a.presion === 'media') return { serviceId: 'descontracturante', why: 'Presión sostenida justo sobre nudos y contracturas.' };
    return { serviceId: 'swedish', why: 'Suelta la tensión sin presión fuerte.' };
  }
  if (a.objetivo === 'desconectar') {
    if (a.presion === 'firme') return { serviceId: 'bamboo', why: 'Cañas templadas con presión firme y uniforme.' };
    if (a.presion === 'media') return { serviceId: 'aromatherapy', why: 'Aceites esenciales que eliges según cómo quieres sentirte.' };
    return { serviceId: 'swedish', why: 'Presión ligera para bajar revoluciones.' };
  }
  return { serviceId: SPECIAL_ID, why: 'Tú eliges técnicas, presión y zonas.' };
}

// Si el masaje recomendado no está en la carta, se recomienda el masaje especial.
export function resolveService(pick: MassagePick, services: Service[]): { service: Service; why: string } | null {
  const service = services.find((row) => row.id === pick.serviceId);
  if (service) return { service, why: pick.why };
  const special = services.find((row) => row.id === SPECIAL_ID);
  return special ? { service: special, why: special.description } : null;
}

function isTratoStyle(value: string | undefined): value is TratoStyle {
  return Boolean(value && value in TRATO_STYLES);
}

// Orden dentro de cada estilo: quien encaja mejor con lo que busca va primero.
function orderedIds(style: TratoStyle, a: Answers): string[] {
  const wantsIntensity = a.presion === 'firme' || a.objetivo === 'tension' || a.objetivo === 'recuperar';
  if (style === 'cercano') return wantsIntensity ? ['dany', 'aleman'] : ['aleman', 'dany'];
  if (style === 'tranquilo') return a.objetivo === 'desconectar' ? ['mazer', 'jairo'] : ['jairo', 'mazer'];
  if (style === 'profesional') return wantsIntensity ? ['borja', 'jessy'] : ['jessy', 'borja'];
  return [...TRATO_STYLES[style].ids];
}

// null = sin preferencia (el que tenga espacio).
export function pickTherapist(a: Answers, therapists: Therapist[]): Therapist | null {
  if (!isTratoStyle(a.trato)) return null;
  for (const id of orderedIds(a.trato, a)) {
    const match = therapists.find((therapist) => therapist.id === id);
    if (match) return match;
  }
  return null;
}

// Los del mismo estilo van primero en la lista para cambiar de terapeuta.
export function therapistChoices(a: Answers, therapists: Therapist[]): Therapist[] {
  const sameStyle = isTratoStyle(a.trato) ? orderedIds(a.trato, a) : [];
  return [...therapists].sort((x, y) => {
    const ix = sameStyle.indexOf(x.id);
    const iy = sameStyle.indexOf(y.id);
    return (ix === -1 ? 99 : ix) - (iy === -1 ? 99 : iy);
  });
}

export function inWindow(slot: string, window: TimeWindow) {
  const { from, to } = TIME_WINDOWS[window];
  return slot >= from && slot <= to;
}

export function lowerFirst(text: string) {
  return text.charAt(0).toLowerCase() + text.slice(1);
}

export function quizMessage(therapist: Therapist | null, service: Service, window: TimeWindow) {
  return [
    'Hola SSENSUUM, hice el quiz.',
    `Terapeuta: ${therapist ? therapist.name : 'el que tenga espacio'}`,
    `Masaje: ${service.name}`,
    `Horario: ${lowerFirst(TIME_WINDOWS[window].label)}`,
    '¿Qué espacios tienen?',
  ].join('\n');
}

export function reserveHref(service: Service, therapist: Therapist | null, slot?: { date: string; time: string }) {
  const params = new URLSearchParams({ service: service.id });
  if (therapist) params.set('therapist', therapist.id);
  if (slot) {
    params.set('date', slot.date);
    params.set('time', slot.time);
  }
  return `/reservar?${params.toString()}`;
}
