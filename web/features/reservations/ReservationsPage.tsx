'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AdminNav } from '../../components/AdminNav';
import { getAdminReservations } from '../../lib/api';
import { BUSINESS } from '../../lib/business';
import { money } from '../../lib/format';
import type { AdminReservation } from '../../lib/types';
import { localIsoDate } from '../booking/dates';

const RANGES = [
  { label: 'Hoy', offset: 0, days: 1 },
  { label: 'Mañana', offset: 1, days: 1 },
  { label: 'Próximos 7 días', offset: 0, days: 7 },
  { label: 'Últimos 7 días', offset: -7, days: 7 },
];

const STATUS: Record<string, { label: string; tone: string }> = {
  CONFIRMED: { label: 'Pagada', tone: 'ok' },
  PENDING_PAYMENT: { label: 'Pagando…', tone: 'wait' },
  NEEDS_ATTENTION: { label: 'Revisar: pagó y el horario se ocupó', tone: 'alert' },
};

const TZ = 'America/Mexico_City';

function dayLabel(iso: string) {
  const label = new Date(iso).toLocaleDateString('es-MX', { timeZone: TZ, weekday: 'long', day: 'numeric', month: 'long' });
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function timeLabel(iso: string) {
  return new Date(iso).toLocaleTimeString('es-MX', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hour12: false });
}

function formatPhone(phone: string) {
  return phone.replace(/^(\d{2})(\d{4})(\d{4})$/, '$1 $2 $3');
}

function customerWhatsapp(item: AdminReservation) {
  if (!item.customer) return null;
  const name = item.customer.firstName;
  const when = `${dayLabel(item.startsAt).toLowerCase()} a las ${timeLabel(item.startsAt)}`;
  let label = 'Recordatorio';
  let text = `Hola ${name}, te esperamos el ${when} para tu ${item.serviceName} en SSENSUUM, Mexicaltzingo 2122-B, Col. Americana (estacionamiento en cajones 1, 2 y 3). ¡Nos vemos!`;
  if (item.status === 'NEEDS_ATTENTION') {
    label = 'Resolver';
    text = `Hola ${name}, recibimos tu anticipo para ${item.serviceName}, pero ese horario se ocupó mientras pagabas. ¿Te acomodamos en otro horario o prefieres el reembolso completo?`;
  } else if (new Date(item.endsAt) < new Date()) {
    label = 'Pedir reseña';
    text = `Hola ${name}, gracias por visitarnos en SSENSUUM. Nos ayudaría muchísimo que nos contaras cómo te fue, toma menos de un minuto: ${BUSINESS.reviewUrl}\nY si algo no fue como esperabas, respóndenos aquí y lo resolvemos.`;
  }
  return { label, href: `https://wa.me/52${item.customer.phone}?text=${encodeURIComponent(text)}` };
}

export function ReservationsPage() {
  const [range, setRange] = useState(RANGES[2]);
  const [items, setItems] = useState<AdminReservation[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const start = new Date();
    start.setDate(start.getDate() + range.offset);
    setItems(null);
    getAdminReservations(localIsoDate(start), range.days)
      .then((rows) => { setItems(rows); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, [range]);

  const byDay = useMemo(() => {
    const groups = new Map<string, AdminReservation[]>();
    for (const item of items ?? []) {
      const key = dayLabel(item.startsAt);
      groups.set(key, [...(groups.get(key) ?? []), item]);
    }
    return [...groups.entries()];
  }, [items]);

  const paid = (items ?? []).filter((item) => item.status === 'CONFIRMED');
  const attention = (items ?? []).filter((item) => item.status === 'NEEDS_ATTENTION');

  return (
    <main className="bookingShell" data-testid="reservations-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Reservas</h1>
        </div>
        <AdminNav current="reservas" />

        <div className="adminRow" role="group" aria-label="Periodo">
          {RANGES.map((option) => (
            <button
              type="button"
              key={option.label}
              className={`secondaryButton ${range === option ? 'selected' : ''}`}
              onClick={() => setRange(option)}
            >
              {option.label}
            </button>
          ))}
        </div>

        {items ? (
          <div className="adminStats">
            <div><strong>{paid.length}</strong><span>pagadas</span></div>
            <div><strong>{money(paid.reduce((total, item) => total + item.depositAmount, 0))}</strong><span>en anticipos</span></div>
            <div className={attention.length ? 'alert' : ''}><strong>{attention.length}</strong><span>por resolver</span></div>
          </div>
        ) : null}

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        {items === null && !error ? <p className="muted">Cargando reservas…</p> : null}
        {items?.length === 0 ? <p className="muted">No hay reservas en este periodo.</p> : null}

        {byDay.map(([day, rows]) => (
          <section className="adminCard" key={day}>
            <h2>{day}</h2>
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Hora</th><th>Servicio</th><th>Cliente</th><th>Estado</th><th></th></tr></thead>
                <tbody>
                  {rows.map((item) => {
                    // Sin apartado = creada fuera del cobro en línea (p. ej. por API o QA).
                    const status = item.status === 'PENDING_PAYMENT' && !item.holdExpiresAt
                      ? { label: 'Sin anticipo', tone: 'wait' }
                      : STATUS[item.status] ?? { label: item.status, tone: 'wait' };
                    const whatsapp = customerWhatsapp(item);
                    return (
                      <tr key={item.id} data-testid="reservation-row">
                        <td><strong>{timeLabel(item.startsAt)}</strong></td>
                        <td>{item.serviceName}<small className="adminSub">{item.therapistNames.join(' + ')}</small></td>
                        <td>
                          {item.customer ? `${item.customer.firstName} ${item.customer.lastName}`.trim() : '—'}
                          {item.customer ? <small className="adminSub">{formatPhone(item.customer.phone)}</small> : null}
                        </td>
                        <td><span className={`statusBadge ${status.tone}`}>{status.label}</span><small className="adminSub">Anticipo {money(item.depositAmount)}</small></td>
                        <td>{whatsapp ? <a className="secondaryButton adminAction" href={whatsapp.href} target="_blank" rel="noreferrer">{whatsapp.label}</a> : null}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}
