import type { Metadata } from 'next';
import { BookingClient } from '../../features/booking/BookingClient';

// Cada combinación de servicio y terapeuta es otra URL de la misma página: no se indexan.
export const metadata: Metadata = {
  title: 'Reserva tu hora · SSENSUUM',
  description: 'Elige terapeuta, día y hora en SSENSUUM, Col. Americana. Apartas con anticipo y cancelas sin costo hasta 3 horas antes.',
  alternates: { canonical: '/reservar' },
  robots: { index: false, follow: true },
};

type Params = { service?: string; therapist?: string; date?: string; time?: string };

export default function ReservationPage({ searchParams }: { searchParams: Params }) {
  return (
    <BookingClient
      serviceId={searchParams.service ?? ''}
      therapistId={searchParams.therapist}
      initialDate={searchParams.date}
      initialTime={searchParams.time}
    />
  );
}
