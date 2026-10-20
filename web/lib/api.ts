import type { AdminReservation, CheckoutRequest, Customer, CustomerImportResult, HrDocument, HrDocumentCategory, Reservation, Service, ServiceRecord, ServiceRecordInput, ServiceRecordSummary, StaffMember, StaffProfileInput, Therapist, WeeklyPayroll } from './types';

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

async function sendJson<T>(method: string, path: string, body: unknown, errorMessage: string): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new ApiError(typeof error?.detail === 'string' ? error.detail : errorMessage, response.status);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

function postJson<T>(path: string, body: unknown, errorMessage: string) {
  return sendJson<T>('POST', path, body, errorMessage);
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

export function getAdminReservations(from: string, days: number) {
  const params = new URLSearchParams({ from, days: String(days) });
  return getJson<{ items: AdminReservation[] }>(`/admin/reservations?${params.toString()}`, 'No se pudieron cargar las reservas').then((body) => body.items);
}

export function getServiceRecords(from: string, days: number) {
  const params = new URLSearchParams({ from, days: String(days) });
  return getJson<{ items: ServiceRecord[]; summary: ServiceRecordSummary }>(`/admin/records?${params.toString()}`, 'No se pudo cargar el registro');
}

export function saveServiceRecord(input: ServiceRecordInput, id?: string) {
  return id
    ? sendJson<ServiceRecord>('PUT', `/admin/records/${encodeURIComponent(id)}`, input, 'No se pudo guardar el registro')
    : postJson<ServiceRecord>('/admin/records', input, 'No se pudo guardar el registro');
}

export function deleteServiceRecord(id: string) {
  return sendJson<void>('DELETE', `/admin/records/${encodeURIComponent(id)}`, undefined, 'No se pudo borrar el registro');
}

// Recursos humanos: expediente del equipo y repositorio de documentos.

export function getStaff() {
  return getJson<StaffMember[]>('/admin/rh/staff', 'No se pudo cargar el equipo');
}

export function saveStaffProfile(therapistId: string, input: StaffProfileInput) {
  return sendJson<StaffMember>('PUT', `/admin/rh/staff/${encodeURIComponent(therapistId)}`, input, 'No se pudo guardar el expediente');
}

export function getHrDocuments(therapistId: string) {
  const params = new URLSearchParams();
  if (therapistId) params.set('therapistId', therapistId);
  return getJson<HrDocument[]>(`/admin/rh/documents?${params.toString()}`, 'No se pudieron cargar los documentos');
}

export async function uploadHrDocument(file: File, category: HrDocumentCategory, therapistId: string, title: string): Promise<HrDocument> {
  const body = new FormData();
  body.append('file', file);
  body.append('category', category);
  body.append('title', title);
  if (therapistId) body.append('therapistId', therapistId);
  const response = await fetch(`${API}/admin/rh/documents`, { method: 'POST', body });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === 'string' ? error.detail : response.status === 413 ? 'El archivo es demasiado grande' : 'No se pudo subir el archivo');
  }
  return response.json();
}

export function deleteHrDocument(id: string) {
  return sendJson<void>('DELETE', `/admin/rh/documents/${encodeURIComponent(id)}`, undefined, 'No se pudo borrar el documento');
}

// Enlaces de descarga directa: el navegador guarda el archivo con el nombre que manda la API.
export const hrDownloadUrl = (id: string) => `${API}/admin/rh/documents/${encodeURIComponent(id)}/download`;
export const hrStaffExportUrl = `${API}/admin/rh/staff/export`;
export const hrDocumentsExportUrl = `${API}/admin/rh/documents/export`;

export function getWeeklyPayroll(week: string) {
  return getJson<WeeklyPayroll>(`/admin/rh/payroll?week=${encodeURIComponent(week)}`, 'No se pudo calcular la liquidación');
}

export const hrPayrollExportUrl = (week: string) => `${API}/admin/rh/payroll/export?week=${encodeURIComponent(week)}`;
