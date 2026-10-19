import type { PaymentMethod } from '../../lib/types';

export const TZ = 'America/Mexico_City';

export const PAYMENT_METHODS: { id: PaymentMethod; label: string }[] = [
  { id: 'efectivo', label: 'Efectivo' },
  { id: 'tarjeta', label: 'Tarjeta' },
  { id: 'transferencia', label: 'Transferencia' },
  { id: 'mercadopago', label: 'Mercado Pago' },
];

export function methodLabel(method: string | null) {
  return PAYMENT_METHODS.find((row) => row.id === method)?.label ?? method ?? '—';
}

// Valor para <input type="datetime-local"> en hora de Guadalajara, sin importar la zona del navegador.
export function localDateTimeInput(iso: string) {
  return new Date(iso).toLocaleString('sv-SE', { timeZone: TZ }).slice(0, 16).replace(' ', 'T');
}

export function paidAtLabel(iso: string) {
  return new Date(iso).toLocaleString('es-MX', { timeZone: TZ, weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false });
}

export function formatPhone(phone: string) {
  return phone.replace(/^(\d{2})(\d{4})(\d{4})$/, '$1 $2 $3');
}
