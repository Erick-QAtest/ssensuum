import type { Schedule } from './types';

export const WEEKDAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const SHORT = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

function hour(value: string) {
  const [h, m] = value.split(':').map(Number);
  const suffix = h < 12 ? 'am' : 'pm';
  const twelve = h % 12 || 12;
  return m ? `${twelve}:${String(m).padStart(2, '0')} ${suffix}` : `${twelve} ${suffix}`;
}

// "Lun y Mar 5 pm–8:30 pm · Mié 3 pm–4 pm"; null si atiende en todo el horario del club.
export function scheduleSummary(schedule: Schedule | null): string | null {
  if (!schedule || 'always' in schedule) return null;
  const groups: { days: number[]; text: string }[] = [];
  for (let day = 0; day < 7; day += 1) {
    const windows = schedule.days[String(day)];
    if (!windows?.length) continue;
    const text = windows.map(([from, to]) => `${hour(from)}–${hour(to)}`).join(', ');
    const last = groups[groups.length - 1];
    if (last && last.text === text && last.days[last.days.length - 1] === day - 1) last.days.push(day);
    else groups.push({ days: [day], text });
  }
  return groups
    .map(({ days, text }) => {
      const label = days.length === 1 ? SHORT[days[0]] : days.length === 2 ? `${SHORT[days[0]]} y ${SHORT[days[1]]}` : `${SHORT[days[0]]} a ${SHORT[days[days.length - 1]]}`;
      return `${label} ${text}`;
    })
    .join(' · ');
}
