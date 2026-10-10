import { BookingClient } from '../../features/booking/BookingClient';

export default function ReservationPage({ searchParams }: { searchParams: { service?: string } }) {
  return <BookingClient serviceId={searchParams.service ?? ''} />;
}
