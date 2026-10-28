'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getMarketingAttribution } from '../../lib/api';
import type { MarketingAttribution, MarketingMeta } from '../../lib/types';
import { bioLink, count } from './marketing';

const PERIODS = [7, 30, 90];

function CopyLink({ url }: { url: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard?.writeText(url).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    }).catch(() => null);
  }
  return (
    <div className="marketingLink">
      <code>{url}</code>
      <button type="button" className="hrLink" onClick={copy}>{copied ? 'Copiado' : 'Copiar'}</button>
    </div>
  );
}

export function AttributionPanel({ meta }: { meta: MarketingMeta }) {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<MarketingAttribution | null>(null);
  const [error, setError] = useState('');
  const [origin, setOrigin] = useState('https://ssensuum.mx');

  useEffect(() => setOrigin(window.location.origin), []);

  useEffect(() => {
    setError('');
    getMarketingAttribution(days).then(setData).catch((e: Error) => setError(e.message));
  }, [days]);

  return (
    <>
      <section className="adminCard" data-testid="marketing-attribution">
        <div className="adminRow adminRowSpread">
          <h2>De dónde llegan</h2>
          <div className="adminRow marketingPeriods" role="group" aria-label="Periodo">
            {PERIODS.map((value) => (
              <button key={value} type="button" className={`secondaryButton ${days === value ? 'selected' : ''}`} aria-pressed={days === value} onClick={() => setDays(value)}>
                {value} días
              </button>
            ))}
          </div>
        </div>
        <p className="muted">
          Visitas y clics de los últimos {days} días según el enlace o la red con que llegaron. Los clientes cuentan por su origen:
          lo que trae el enlace al reservar o lo que se pregunta en Registro.
        </p>
        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        {!data && !error ? <p className="muted">Cargando…</p> : null}
        {data ? (
          <div className="adminTableWrap">
            <table className="adminTable marketingTable">
              <thead>
                <tr>
                  <th>Origen</th><th>Visitas</th><th>Clic en reservar</th><th>Inicio de pago</th><th>WhatsApp</th>
                  <th>Clientes nuevos</th><th>Conversión</th><th>Ya vinieron</th><th>Recurrentes</th><th>Miembros</th><th>En riesgo</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row) => {
                  const empty = !row.visits && !row.customers && !row.whatsappClicks;
                  return (
                    <tr key={row.source} className={empty ? 'marketingEmpty' : ''}>
                      <td>
                        <strong>{row.label}</strong>
                        {row.customers ? <Link className="adminSub" href={`/admin/clientes?source=${row.source}`}>Ver {row.customers} {row.customers === 1 ? 'cliente' : 'clientes'}</Link> : null}
                      </td>
                      <td>{count(row.visits)}</td>
                      <td>{count(row.reserveClicks)}</td>
                      <td>{count(row.checkoutStarts)}</td>
                      <td>{count(row.whatsappClicks)}</td>
                      <td>{count(row.newCustomers)}</td>
                      <td>{row.conversion === null ? '—' : `${row.conversion}%`}</td>
                      <td>{count(row.visited)}</td>
                      <td>{count(row.recurring)}</td>
                      <td>{count(row.members)}</td>
                      <td className={row.atRisk ? 'marketingAlert' : ''}>{count(row.atRisk)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
        <p className="adminSub">Conversión: clientes nuevos del periodo entre visitas del periodo.</p>
      </section>

      <section className="adminCard">
        <h2>Enlaces para cada red</h2>
        <p className="muted">
          Usa estos enlaces en la bio, en los stickers de enlace de las historias y en los mensajes. Así el sitio sabe de qué red llegó cada visita
          y la recuerda 90 días para atribuirle la reserva.
        </p>
        <div className="marketingLinks">
          {meta.channels.map((channel) => (
            <div key={channel.id}>
              <h3>{channel.label}</h3>
              <span className="adminSub">Sitio</span>
              <CopyLink url={bioLink(origin, channel.id)} />
              <span className="adminSub">Quiz para elegir terapeuta</span>
              <CopyLink url={bioLink(origin, channel.id, '/quiz')} />
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
