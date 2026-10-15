import { BookingClient } from '../../features/booking/BookingClient';

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
