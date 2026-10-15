'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getReservation, getServices, retryCheckout, syncPayment } from '../../lib/api';
import { money } from '../../lib/format';
import type { Reservation, Service } from '../../lib/types';
import { whatsappUrl } from '../../lib/whatsapp';

const POLL_MS = 3000;
const MAX_POLLS = 20;

function when(iso: string) {
  const label = new Date(iso).toLocaleString('es-MX', {
    timeZone: 'America/Mexico_City',
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  });
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function PaymentResult({ reservationId, paymentId, returnStatus }: { reservationId: string; paymentId?: string; returnStatus?: string }) {
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState('');
  const [gaveUp, setGaveUp] = useState(false);
  const [retrying, setRetrying] = useState(false);
  // Mercado Pago regresa con status=approved solo si se cobró; rejected, null o failure significan que no.
  const notPaid = Boolean(returnStatus && returnStatus !== 'approved');

  useEffect(() => {
    getServices().then(setServices).catch(() => null);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let polls = 0;

    async function load() {
      try {
        // El regreso de Mercado Pago trae el id del pago: se verifica en el servidor por si el webhook aún no llega.
        if (paymentId && paymentId !== 'null') await syncPayment(paymentId).catch(() => null);
        const current = await getReservation(reservationId);
        if (cancelled) return;
        setReservation(current);
        if (current.status === 'PENDING_PAYMENT' && !notPaid) {
          if (polls++ < MAX_POLLS) setTimeout(load, POLL_MS);
          else setGaveUp(true);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'No encontramos tu reserva');
      }
    }

    load();
    return () => { cancelled = true; };
  }, [reservationId, paymentId, notPaid]);

  async function retry() {
    setRetrying(true);
    try {
      const { checkoutUrl } = await retryCheckout(reservationId);
      window.location.assign(checkoutUrl);
    } catch (e) {
      setRetrying(false);
      setError(e instanceof Error ? e.message : 'No pudimos reintentar el pago');
    }
  }

  const service = services.find((row) => row.id === reservation?.serviceId);
  const serviceName = service?.name ?? 'tu servicio';
  const details = reservation ? `${serviceName} · ${when(reservation.startsAt)}` : '';
  const help = whatsappUrl(`Hola SSENSUUM, tengo una duda con mi reserva ${reservationId.slice(0, 8)}: ${details}`);
  const pickAgainHref = reservation ? `/reservar?service=${reservation.serviceId}` : '/';

  let title = 'Verificando tu pago…';
  let message = 'Esto toma unos segundos. No cierres esta página.';
  let action = null;

  if (error) {
    title = 'No encontramos tu reserva';
    message = 'Si ya pagaste, escríbenos y lo revisamos de inmediato.';
    action = <a className="primaryButton" href={help} target="_blank" rel="noreferrer">Escribir por WhatsApp</a>;
  } else if (reservation?.status === 'CONFIRMED') {
    title = '¡Tu reserva está confirmada!';
    message = 'Recibimos tu anticipo. Te esperamos en Mexicaltzingo 2122-B, Col. Americana · estacionamiento en cajones 1, 2 y 3.';
    action = <a className="primaryButton" href="https://maps.app.goo.gl/2CLVeFkfyoiGDQqv6" target="_blank" rel="noreferrer">Cómo llegar</a>;
  } else if (reservation?.status === 'NEEDS_ATTENTION') {
    title = 'Recibimos tu pago';
    message = 'Tu horario se ocupó mientras pagabas. Te escribimos por WhatsApp para darte otro horario o devolverte el anticipo.';
    action = <a className="primaryButton" href={help} target="_blank" rel="noreferrer">Escribir por WhatsApp</a>;
  } else if (reservation?.status === 'EXPIRED' || reservation?.status === 'CANCELLED') {
    title = 'Tu apartado venció';
    message = 'No se completó el pago a tiempo y el horario se liberó. Puedes elegir otro.';
    action = <Link className="primaryButton" href={pickAgainHref}>Reservar de nuevo</Link>;
  } else if (reservation && (notPaid || gaveUp)) {
    const until = reservation.holdExpiresAt
      ? new Date(reservation.holdExpiresAt).toLocaleTimeString('es-MX', { timeZone: 'America/Mexico_City', hour: '2-digit', minute: '2-digit', hour12: false })
      : '';
    title = 'Tu pago no se completó';
    message = `No se hizo ningún cargo.${until ? ` Tu horario sigue apartado hasta las ${until}.` : ''} Puedes intentarlo de nuevo con otra tarjeta.`;
    action = (
      <>
        <button type="button" className="primaryButton" disabled={retrying} onClick={retry}>
          {retrying ? 'Abriendo Mercado Pago…' : `Intentar el pago de nuevo`}
        </button>
        <p className="summaryNote"><Link className="summaryLink" href={pickAgainHref}>Elegir otro horario</Link></p>
      </>
    );
  }

  return (
    <main className="bookingShell">
      <Link href="/" className="backLink">← Volver a la carta</Link>
      <div className="bookingPanel paymentResult">
        <div className="bookingTitle">
          <span className="kicker">Reserva</span>
          <h1>{title}</h1>
          <p>{message}</p>
        </div>
        {reservation ? (
          <section className="summary" data-testid="booking-summary">
            <dl>
              <div><dt>Servicio</dt><dd>{serviceName}</dd></div>
              <div><dt>Cuándo</dt><dd>{when(reservation.startsAt)}</dd></div>
              <div><dt>Anticipo</dt><dd>{money(reservation.depositAmount)}</dd></div>
            </dl>
          </section>
        ) : null}
        {action}
        {reservation?.status === 'CONFIRMED' ? (
          <p className="summaryNote"><a className="summaryLink" href={help} target="_blank" rel="noreferrer">¿Necesitas cambiar algo? Escríbenos</a></p>
        ) : null}
      </div>
    </main>
  );
}
