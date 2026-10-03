import { BookingClient } from '../../components/BookingClient';

export default function ReservationPage({ searchParams }: { searchParams: { service?: string } }) {
  return <BookingClient serviceId={searchParams.service ?? ''} />;
}
