import { PaymentResult } from '../../../features/payment/PaymentResult';

export default function ReservationResultPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { payment_id?: string; status?: string; collection_status?: string };
}) {
  return <PaymentResult reservationId={params.id} paymentId={searchParams.payment_id} returnStatus={searchParams.status ?? searchParams.collection_status} />;
}
