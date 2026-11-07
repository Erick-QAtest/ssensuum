import type { Therapist } from '../../lib/types';

// Orden del equipo en la página de inicio: estos primero, en este orden; el resto, aleatorio en cada visita.
export const TEAM_FIRST = ['jairo', 'kevin', 'dany', 'braulio'];

export function landingOrder(therapists: Therapist[], random: () => number = Math.random): Therapist[] {
  const first = TEAM_FIRST.map((id) => therapists.find((therapist) => therapist.id === id)).filter((t): t is Therapist => Boolean(t));
  const rest = therapists.filter((therapist) => !TEAM_FIRST.includes(therapist.id));
  for (let i = rest.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [rest[i], rest[j]] = [rest[j], rest[i]];
  }
  return [...first, ...rest];
}
