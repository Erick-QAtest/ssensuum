import type { CheckoutRequest, Customer, CustomerImportResult, Reservation, Service, Therapist } from './types';

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

export function searchCustomers(query: string) {
  const params = new URLSearchParams({ limit: '200' });
  if (query.trim()) params.set('q', query.trim());
  return getJson<Customer[]>(`/customers?${params.toString()}`, 'No se pudo cargar la lista de clientes');
}

export async function importCustomers(file: File, dryRun: boolean): Promise<CustomerImportResult> {
  const body = new FormData();
  body.append('file', file);
  const response = await fetch(`${API}/customers/import?dryRun=${dryRun}`, { method: 'POST', body });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === 'string' ? error.detail : 'No se pudo procesar el archivo');
  }
  return response.json();
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function postJson<T>(path: string, body: unknown, errorMessage: string): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new ApiError(typeof error?.detail === 'string' ? error.detail : errorMessage, response.status);
  }
  return response.json();
}

export function startCheckout(request: CheckoutRequest) {
  return postJson<{ reservation: Reservation; checkoutUrl: string }>('/checkout', request, 'No pudimos iniciar el pago');
}

export function getReservation(id: string) {
  return getJson<Reservation>(`/reservations/${encodeURIComponent(id)}`, 'No encontramos tu reserva');
}

export function syncPayment(paymentId: string) {
  return postJson<{ reservation: Reservation | null }>(`/payments/${encodeURIComponent(paymentId)}/sync`, undefined, 'No pudimos verificar el pago');
}

export async function paymentsEnabled() {
  const body = await getJson<{ enabled: boolean }>('/payments/status', 'No se pudo consultar el estado de pagos');
  return body.enabled;
}

export type TrackEvent = 'page_view' | 'reserve_click' | 'booking_summary' | 'checkout_start' | 'whatsapp_click';

// Conteo anónimo de visitas y clics; nunca debe interrumpir al usuario.
export function track(name: TrackEvent, label = '') {
  try {
    const body = JSON.stringify({ name, label: label.slice(0, 120) });
    const url = `${API}/events`;
    if (navigator.sendBeacon?.(url, new Blob([body], { type: 'application/json' }))) return;
    fetch(url, { method: 'POST', body, headers: { 'Content-Type': 'application/json' }, keepalive: true }).catch(() => null);
  } catch {
    // sin conteo
  }
}

export function retryCheckout(reservationId: string) {
  return postJson<{ reservation: Reservation; checkoutUrl: string }>(`/checkout/${encodeURIComponent(reservationId)}/retry`, undefined, 'No pudimos reintentar el pago');
}
