'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { ApiError, getAvailability, getServices, getTherapists, paymentsEnabled, startCheckout, track } from '../../lib/api';
import { money } from '../../lib/format';
import { scheduleSummary } from '../../lib/schedule';
import type { Service, Therapist } from '../../lib/types';
import { whatsappUrl } from '../../lib/whatsapp';
import { localIsoDate, longDateLabel, next14Days, timeLabel } from './dates';
import { TherapistAvatar } from '../../components/TherapistAvatar';

// El quiz puede llegar con día y hora; solo se aceptan si caen dentro de los 14 días que se muestran.
function bookableDate(date?: string) {
  return date && next14Days().some((day) => localIsoDate(day) === date) ? date : '';
}

export function BookingClient({ serviceId, therapistId, initialDate, initialTime }: { serviceId: string; therapistId?: string; initialDate?: string; initialTime?: string }) {
  const [services, setServices] = useState<Service[]>([]);
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  // "Reservar con {nombre}" llega con el terapeuta ya elegido.
  const [therapistIds, setTherapistIds] = useState<string[]>(therapistId ? [therapistId] : []);
  const [noPreference, setNoPreference] = useState(!therapistId);
  const [dateIso, setDateIso] = useState(() => bookableDate(initialDate));
  const [slots, setSlots] = useState<string[]>([]);
  const [time, setTime] = useState(() => (bookableDate(initialDate) && /^\d{2}:\d{2}$/.test(initialTime ?? '') ? initialTime ?? '' : ''));
  const [showSummary, setShowSummary] = useState(false);
  const [error, setError] = useState('');
  const [slotsVersion, setSlotsVersion] = useState(0);
  const [firstName, setFirstName] = useState('');
  const [phone, setPhone] = useState('');
  const [paying, setPaying] = useState(false);
  const [payError, setPayError] = useState('');
  const [paymentsOff, setPaymentsOff] = useState(false);
  const summaryRef = useRef<HTMLElement>(null);

  // En celular el resumen aparece fuera de pantalla: se lleva al cliente hasta él.
  useEffect(() => {
    if (!showSummary) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    summaryRef.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }, [showSummary]);

  useEffect(() => {
    Promise.all([getServices(), getTherapists()])
      .then(([serviceRows, therapistRows]) => {
        setServices(serviceRows);
        setTherapists(therapistRows);
      })
      .catch(() => setError('No pudimos cargar la información. Intenta de nuevo en un momento.'));
    track('page_view', `reservar:${serviceId}`);
    paymentsEnabled().then((enabled) => setPaymentsOff(!enabled)).catch(() => setPaymentsOff(true));
  }, [serviceId]);

  const service = services.find((row) => row.id === serviceId);
  const selectedTherapists = therapists.filter((row) => therapistIds.includes(row.id));
  const days = useMemo(next14Days, []);

  useEffect(() => {
    if (!service || !dateIso) {
      setSlots([]);
      return;
    }
    getAvailability(service.id, dateIso, therapistIds.length === 1 ? therapistIds[0] : undefined)
      .then((rows) => {
        setSlots(rows);
        // Una hora que ya no está libre (o que llegó del quiz y se ocupó) se quita.
        setTime((current) => (current && !rows.includes(current) ? '' : current));
      })
      .catch((e: Error) => setError(e.message));
  }, [service, dateIso, therapistIds, slotsVersion]);

  if (!service) {
    return (
      <main className="bookingShell">
        <Link href="/" className="backLink">← Volver</Link>
        <div className="bookingPanel"><p>Cargando servicio…</p></div>
      </main>
    );
  }

  const therapistLabel = noPreference ? 'Sin preferencia' : selectedTherapists.map((row) => row.name).join(' + ');
  const confirmUrl = whatsappUrl([
    'Hola SSENSUUM, quiero reservar:',
    `• ${service.name}`,
    `• ${dateIso ? longDateLabel(dateIso) : ''}, ${time ? timeLabel(time) : ''}`,
    `• Terapeuta: ${therapistLabel}`,
    'Mi nombre es: ',
  ].join('\n'));

  const phoneDigits = phone.replace(/\D/g, '');
  const canPay = firstName.trim().length > 0 && phoneDigits.length >= 10 && !paying;

  async function pay() {
    if (!service) return;
    setPaying(true);
    setPayError('');
    track('checkout_start', service.id);
    try {
      const { checkoutUrl } = await startCheckout({
        serviceId: service.id,
        therapistIds: noPreference ? [] : therapistIds,
        // Guadalajara no tiene horario de verano: siempre UTC-6.
        startsAt: `${dateIso}T${time}:00-06:00`,
        firstName: firstName.trim(),
        phone,
      });
      window.location.assign(checkoutUrl);
    } catch (e) {
      setPaying(false);
      if (e instanceof ApiError && e.status === 503) {
        setPaymentsOff(true);
        return;
      }
      if (e instanceof ApiError && e.status === 409) {
        setTime('');
        setShowSummary(false);
        setSlotsVersion((version) => version + 1);
      }
      setPayError(e instanceof Error ? e.message : 'No pudimos iniciar el pago');
    }
  }

  const canContinue = Boolean(dateIso && time && (noPreference || therapistIds.length === service.therapistsRequired));

  return (
    <main className="bookingShell">
      <Link href="/" className="backLink">← Volver a la carta</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Reserva</span>
          <h1>{service.name}</h1>
          <p>{service.durationMinutes} min · anticipo <strong data-testid="deposit-amount">{money(service.deposit)}</strong></p>
        </div>

        {error ? <div className="errorBox">{error}</div> : null}

        <section className="step">
          <div className="stepNumber">01</div>
          <div className="stepContent">
            <h2>Elige terapeuta</h2>
            <button type="button" aria-pressed={noPreference} className={`secondaryButton ${noPreference ? 'selected' : ''}`} onClick={() => { setNoPreference(true); setTherapistIds([]); }}>Sin preferencia</button>
            <div className="therapistGrid bookingTherapists">
              {therapists.map((therapist) => (
                <button
                  type="button"
                  key={therapist.id}
                  data-testid="therapist-card"
                  aria-pressed={therapistIds.includes(therapist.id)}
                  className={`therapistChoice ${therapistIds.includes(therapist.id) ? 'selected' : ''}`}
                  onClick={() => {
                    setNoPreference(false);
                    setTherapistIds((current) => {
                      if (current.includes(therapist.id)) return current.filter((id) => id !== therapist.id);
                      if (service.therapistsRequired === 1) return [therapist.id];
                      if (current.length >= service.therapistsRequired) return current;
                      return [...current, therapist.id];
                    });
                  }}
                >
                  <TherapistAvatar therapist={therapist} className="avatar" />
                  <span><strong>{therapist.name}{therapist.isNew ? <span className="tag">Nuevo</span> : null}</strong>{therapist.strengths ? <small>{therapist.strengths}</small> : null}</span>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="step">
          <div className="stepNumber">02</div>
          <div className="stepContent">
            <h2>Elige día</h2>
            <div className="datesRow">
              {days.map((day) => {
                const iso = localIsoDate(day);
                return (
                  <button
                    type="button"
                    key={iso}
                    data-testid={`date-${iso}`}
                    aria-label={longDateLabel(iso)}
                    aria-pressed={dateIso === iso}
                    className={`dateButton ${dateIso === iso ? 'selected' : ''}`}
                    onClick={() => { setDateIso(iso); setTime(''); setShowSummary(false); }}
                  >
                    <span>{day.toLocaleDateString('es-MX', { weekday: 'short' })}</span>
                    <strong>{day.getDate()}</strong>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="step">
          <div className="stepNumber">03</div>
          <div className="stepContent">
            <h2>Elige hora</h2>
            {!dateIso ? <p className="muted">Selecciona primero un día.</p> : null}
            {dateIso && slots.length === 0 ? <p className="muted">No hay horarios disponibles con estos filtros.</p> : null}
            {selectedTherapists.map((row) => (scheduleSummary(row.schedule) ? <p key={row.id} className="muted" data-testid="therapist-schedule">{row.name} atiende: {scheduleSummary(row.schedule)}.</p> : null))}
            <div className="slotsGrid">
              {slots.map((slot) => (
                <button
                  type="button"
                  key={slot}
                  data-testid={`slot-${slot.replace(':', '-')}`}
                  aria-pressed={time === slot}
                  className={time === slot ? 'selected' : ''}
                  onClick={() => { setTime(slot); setShowSummary(false); }}
                >
                  {timeLabel(slot)}
                </button>
              ))}
            </div>
          </div>
        </section>

        <button className="primaryButton" disabled={!canContinue} onClick={() => { setShowSummary(true); track('booking_summary', service.id); }}>Continuar al resumen</button>

        {showSummary ? (
          <section className="summary" data-testid="booking-summary" ref={summaryRef}>
            <span className="kicker">Resumen</span>
            <h2>Tu experiencia</h2>
            <dl>
              <div><dt>Servicio</dt><dd>{service.name}</dd></div>
              <div><dt>Terapeuta</dt><dd>{therapistLabel}</dd></div>
              <div><dt>Día</dt><dd>{longDateLabel(dateIso)}</dd></div>
              <div><dt>Hora</dt><dd>{timeLabel(time)}</dd></div>
              <div><dt>Duración</dt><dd>{service.durationMinutes} min</dd></div>
              <div><dt>Total</dt><dd>{money(service.publicPrice)}</dd></div>
              <div><dt>Anticipo hoy</dt><dd>{money(service.deposit)}</dd></div>
              <div><dt>Restante el día de tu cita</dt><dd>{money(service.publicPrice - service.deposit)}</dd></div>
            </dl>
            {paymentsOff ? (
              <>
                <a className="primaryButton whatsappConfirm" href={confirmUrl} target="_blank" rel="noreferrer" onClick={() => track('whatsapp_click', 'reserva-confirmar')}>Confirmar por WhatsApp</a>
                <p className="summaryNote">Te respondemos por WhatsApp para confirmar tu horario y el anticipo de {money(service.deposit)}.</p>
              </>
            ) : (
              <>
                <div className="checkoutFields">
                  <label>
                    <span>Nombre</span>
                    <input value={firstName} onChange={(event) => setFirstName(event.target.value)} autoComplete="given-name" placeholder="¿Cómo te llamas?" required />
                  </label>
                  <label>
                    <span>WhatsApp</span>
                    <input type="tel" inputMode="tel" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel-national" placeholder="33 1234 5678" required aria-describedby="phone-hint" />
                  </label>
                </div>
                {/* El botón de pago está deshabilitado hasta tener nombre y 10 dígitos: se dice por qué. */}
                {!canPay && !paying ? <p className="summaryNote" id="phone-hint">Escribe tu nombre y tu WhatsApp a 10 dígitos para pagar el anticipo.</p> : null}
                {payError ? <div className="errorBox" role="alert">{payError}</div> : null}
                <button type="button" className="primaryButton checkoutButton" disabled={!canPay} onClick={pay}>
                  {paying ? 'Abriendo Mercado Pago…' : `Pagar anticipo ${money(service.deposit)}`}
                </button>
                <p className="summaryNote">
                  Pago seguro con Mercado Pago. El restante lo pagas en el club con tarjeta, transferencia, efectivo o terminal; si eres miembro, se ajusta a tu precio. Puedes cancelar o cambiar tu horario sin costo hasta 3 horas antes.
                  Al pagar aceptas los <Link href="/terminos" target="_blank">términos de reserva</Link> y el <Link href="/aviso-de-privacidad" target="_blank">aviso de privacidad</Link>.
                </p>
                <a className="summaryLink" href={confirmUrl} target="_blank" rel="noreferrer" onClick={() => track('whatsapp_click', 'reserva-alterna')}>¿Prefieres confirmar por WhatsApp?</a>
              </>
            )}
          </section>
        ) : null}
      </div>
    </main>
  );
}
