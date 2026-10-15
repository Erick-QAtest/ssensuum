import type { Service } from '../../lib/types';

export const SPECIAL_ID = 'massage-special';

// Grupos de la carta, solo en el frontend (la base no cambia).
export const CARTA_GROUPS = [
  { key: 'suave', title: 'Suave y lento', ids: ['swedish', 'aromatherapy', 'lymphatic'] },
  { key: 'firme', title: 'Firme', ids: ['descontracturante', 'deep-tissue', 'sports', 'bamboo', 'thai'] },
  { key: 'dos', title: 'Para dos', ids: ['four-hands', 'couples-massage'] },
] as const;

export type CartaGroupKey = (typeof CARTA_GROUPS)[number]['key'];

const SOFT_HINT = /suave|ligera|relaj|calma|aceite|r[ií]tmic/i;

// Un masaje nuevo que no esté en la lista cae en el grupo que mejor le queda.
export function cartaGroupFor(service: Service): CartaGroupKey {
  const listed = CARTA_GROUPS.find((group) => (group.ids as readonly string[]).includes(service.id));
  if (listed) return listed.key;
  if (service.therapistsRequired >= 2) return 'dos';
  return SOFT_HINT.test(`${service.description} ${service.details ?? ''}`) ? 'suave' : 'firme';
}

export const CLUB_RULES = [
  { lead: 'Sensual, nunca sexual:', text: 'no hay contacto sexual ni servicios adicionales.' },
  { lead: 'Si se cruza ese límite,', text: 'la sesión termina en ese momento y sin reembolso.' },
  { lead: 'Respeto total:', text: 'tu terapeuta puede ajustar o detener la sesión si algo no se siente bien.' },
  { lead: 'Tu visita es confidencial.', text: '' },
];

// Solo testimonios reales, con permiso del cliente. Vacío = la sección no se muestra.
export const TESTIMONIALS: { quote: string; author: string }[] = [];

// Respuestas pendientes de confirmar con el club. Vacío = la sección no se muestra.
// Preguntas previstas: ¿Qué pasa si cancelo? ¿Cómo pago? ¿Qué aparece en mi estado
// de cuenta? ¿Puedo cambiar de terapeuta? ¿Qué tengo que llevar?
export const FAQ: { question: string; answer: string }[] = [];
