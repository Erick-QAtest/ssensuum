import type { Metadata } from 'next';
import { ReservationsPage } from '../../../features/reservations/ReservationsPage';

export const metadata: Metadata = { title: 'Reservas · SSENSUUM' };

export default function AdminReservationsPage() {
  return <ReservationsPage />;
}
