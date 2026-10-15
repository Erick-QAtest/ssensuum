import { BookingClient } from '../../features/booking/BookingClient';

export default function ReservationPage({ searchParams }: { searchParams: { service?: string; therapist?: string } }) {
  return <BookingClient serviceId={searchParams.service ?? ''} therapistId={searchParams.therapist} />;
}
