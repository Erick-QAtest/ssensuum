import type { Service, Therapist } from './types';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

async function getJson<T>(path: string, errorMessage: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(errorMessage);
  return response.json();
}

export function getServices() {
  return getJson<Service[]>('/services', 'No se pudo cargar el catálogo');
}

export function getTherapists() {
  return getJson<Therapist[]>('/therapists', 'No se pudo cargar el equipo');
}

export async function getAvailability(serviceId: string, date: string, therapistId?: string) {
  const params = new URLSearchParams({ serviceId, date });
  if (therapistId) params.set('therapistId', therapistId);
  const body = await getJson<{ slots?: string[] }>(`/availability?${params.toString()}`, 'No se pudo consultar disponibilidad');
  return body.slots ?? [];
}
