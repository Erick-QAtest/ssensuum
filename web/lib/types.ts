export type Service = {
  id: string;
  name: string;
  category: string;
  description: string;
  durationMinutes: number;
  publicPrice: number;
  memberPrice: number;
  deposit: number;
  therapistsRequired: number;
  details: string | null;
};

export type Therapist = {
  id: string;
  name: string;
  strengths: string;
  photoUrl: string;
  bio: string | null;
  isNew: boolean;
};

export type Customer = {
  id: string;
  phone: string;
  firstName: string;
  lastName: string;
  email: string | null;
  birthday: string | null;
  membershipExpiresOn: string | null;
  notes: string | null;
  createdAt: string;
};

export type CustomerImportIssue = {
  row: number;
  status: 'duplicate' | 'invalid' | 'warning';
  phone: string;
  name: string;
  messages: string[];
};

export type CustomerImportResult = {
  dryRun: boolean;
  fileName: string;
  columns: Partial<Record<'phone' | 'firstName' | 'lastName' | 'email' | 'birthday' | 'membershipExpiresOn' | 'notes', string>>;
  totalRows: number;
  valid: number;
  created: number;
  duplicates: number;
  invalid: number;
  warnings: number;
  issues: CustomerImportIssue[];
  issuesTruncated: boolean;
  preview: Pick<Customer, 'phone' | 'firstName' | 'lastName' | 'email' | 'birthday' | 'membershipExpiresOn' | 'notes'>[];
};

export type ReservationStatus = 'PENDING_PAYMENT' | 'CONFIRMED' | 'EXPIRED' | 'CANCELLED' | 'NEEDS_ATTENTION' | 'RESCHEDULED';

export type Reservation = {
  id: string;
  serviceId: string;
  therapistIds: string[];
  startsAt: string;
  endsAt: string;
  status: ReservationStatus;
  depositAmount: number;
  holdExpiresAt: string | null;
};

export type CheckoutRequest = {
  serviceId: string;
  therapistIds: string[];
  startsAt: string;
  firstName: string;
  phone: string;
};

export type AdminReservation = Reservation & {
  paymentId: string | null;
  serviceName: string;
  therapistNames: string[];
  customer: Customer | null;
};

export type PaymentMethod = 'efectivo' | 'tarjeta' | 'transferencia' | 'mercadopago';

export type TipEntry = { therapistId: string; amount: number };

export type ServiceRecordInput = {
  customerName: string;
  customerPhone: string;
  serviceId: string;
  therapistIds: string[];
  paidAt: string;
  amount: number;
  paymentMethod: PaymentMethod;
  tips: TipEntry[];
  tipMethod: PaymentMethod | null;
  notes: string | null;
};

export type ServiceRecord = ServiceRecordInput & {
  id: string;
  customerId: string | null;
  serviceName: string;
  therapistNames: string[];
  tipTotal: number;
  createdAt: string;
};

export type ServiceRecordSummary = {
  count: number;
  amount: number;
  tips: number;
  byPaymentMethod: Partial<Record<PaymentMethod, number>>;
  tipsByTherapist: { therapistId: string; therapistName: string; amount: number; count: number }[];
};

export type StaffMember = Therapist & {
  active: boolean;
  fullName: string | null;
  phone: string | null;
  email: string | null;
  birthday: string | null;
  hiredOn: string | null;
  emergencyContact: string | null;
  notes: string | null;
  documents: number;
  missingDocuments: { category: HrDocumentCategory; label: string }[];
  documentationComplete: boolean;
};

export type StaffProfileInput = {
  fullName: string;
  phone: string;
  email: string;
  birthday: string | null;
  hiredOn: string | null;
  emergencyContact: string;
  notes: string;
};

export type HrDocumentCategory = 'contrato' | 'autorizacion_imagen' | 'autorizacion_descuento' | 'identificacion' | 'comprobante' | 'certificado' | 'nomina' | 'otro' | 'plantilla';

export type HrDocument = {
  id: string;
  therapistId: string | null;
  category: HrDocumentCategory;
  categoryLabel: string;
  title: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
  uploadedAt: string;
};

export type PayrollLine = {
  recordId: string;
  paidAt: string;
  serviceName: string;
  customerName: string;
  gross: number;
  cleaning: number;
  tip: number;
  pay: number;
  // Fecha límite de pago: 48 horas después del servicio.
  dueAt: string;
  payoutAt: string | null;
  overdue: boolean;
};

export type PendingPayout = PayrollLine & { therapistId: string; therapistName: string };

export type PayrollAmounts = {
  services: number;
  gross: number;
  cleaning: number;
  cleaningToCollect: number;
  servicePay: number;
  tips: number;
  total: number;
  pending: number;
};

export type PayrollRow = PayrollAmounts & {
  therapistId: string;
  therapistName: string;
  cleaningCompensated: boolean;
  paidLines: number;
  lines: PayrollLine[];
};

export type WeeklyPayroll = {
  weekStart: string;
  weekEnd: string;
  staff: PayrollRow[];
  totals: PayrollAmounts;
};
