import type { HrDocumentCategory } from '../../lib/types';

export const DOCUMENT_CATEGORIES: { value: HrDocumentCategory; label: string }[] = [
  { value: 'contrato', label: 'Contrato firmado' },
  { value: 'autorizacion_imagen', label: 'Autorización de imagen' },
  { value: 'autorizacion_descuento', label: 'Autorización de descuento de limpieza' },
  { value: 'identificacion', label: 'Identificación oficial' },
  { value: 'comprobante', label: 'Comprobante' },
  { value: 'certificado', label: 'Certificado' },
  { value: 'nomina', label: 'Nómina' },
  { value: 'otro', label: 'Otro' },
  { value: 'plantilla', label: 'Formato para firmar (en blanco)' },
];

export type UploadPreset = { therapistId: string; category: HrDocumentCategory; key: number };

export const ACCEPTED_FILES = '.pdf,.jpg,.jpeg,.png,.webp,.heic,.doc,.docx,.xls,.xlsx,.csv,.txt';
export const MAX_DOCUMENT_BYTES = 8 * 1024 * 1024;

export function formatPhone(phone: string) {
  return phone.replace(/^(\d{2})(\d{4})(\d{4})$/, '$1 $2 $3');
}

export function formatDate(isoDate: string) {
  const [year, month, day] = isoDate.slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
