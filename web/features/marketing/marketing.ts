// Código corto de cada red en sus enlaces (?utm_source=ig); la API lo traduce a la red.
export const LINK_CODES: Record<string, string> = { instagram: 'ig', tiktok: 'tt', x: 'x', facebook: 'fb' };

export function bioLink(origin: string, channel: string, path = '/') {
  return `${origin}${path}?utm_source=${LINK_CODES[channel] ?? channel}`;
}

export function count(value: number | null | undefined) {
  return value === null || value === undefined ? '—' : value.toLocaleString('es-MX');
}

export function signed(value: number | null | undefined) {
  if (value === null || value === undefined || value === 0) return null;
  return `${value > 0 ? '+' : '−'}${Math.abs(value).toLocaleString('es-MX')}`;
}

export function shortDay(iso: string) {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric', month: 'short' });
}

export function monthRange(year: number, month: number) {
  const pad = (value: number) => String(value).padStart(2, '0');
  const last = new Date(year, month + 1, 0).getDate();
  return { from: `${year}-${pad(month + 1)}-01`, to: `${year}-${pad(month + 1)}-${pad(last)}` };
}
