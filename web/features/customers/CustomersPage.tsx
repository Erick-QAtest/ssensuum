'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getCustomerFunnel, searchCustomers } from '../../lib/api';
import type { Customer, CustomerWithStage, FunnelStage, FunnelSummary } from '../../lib/types';
import { AdminNav } from '../../components/AdminNav';
import { localIsoDate } from '../booking/dates';
import { CustomerProfileCard } from './CustomerProfileCard';
import { ImportPanel } from './ImportPanel';
import { STAGES, StageBadge } from './stages';

function formatPhone(phone: string) {
  return phone.replace(/^(\d{2})(\d{4})(\d{4})$/, '$1 $2 $3');
}

function membership(customer: Customer) {
  if (!customer.membershipExpiresOn) return null;
  const [year, month, day] = customer.membershipExpiresOn.split('-').map(Number);
  const label = new Date(year, month - 1, day).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
  const active = customer.membershipExpiresOn >= localIsoDate(new Date());
  return { active, label: active ? `Vigente hasta ${label}` : `Vencida ${label}` };
}

function shortDate(iso: string) {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
}

function FunnelCard({ funnel, stage, onSelect }: { funnel: FunnelSummary | null; stage: FunnelStage | null; onSelect: (stage: FunnelStage | null) => void }) {
  const max = Math.max(1, ...(funnel?.stages.map((entry) => entry.count) ?? []));
  return (
    <section className="adminCard" aria-labelledby="funnel-title">
      <div className="adminRow adminRowSpread">
        <h2 id="funnel-title">Funnel</h2>
        {stage ? <button type="button" className="hrLink" onClick={() => onSelect(null)}>Ver todos{funnel ? ` (${funnel.total})` : ''}</button> : null}
      </div>
      <p className="muted">Toca una etapa para ver solo a esos clientes.</p>
      {funnel ? (
        <ol className="funnelStages" data-testid="funnel-summary">
          {funnel.stages.map((entry) => (
            <li key={entry.stage}>
              <button
                type="button"
                className={`funnelStage stage-${STAGES[entry.stage].tone}`}
                aria-pressed={stage === entry.stage}
                onClick={() => onSelect(stage === entry.stage ? null : entry.stage)}
              >
                <strong>{entry.count}</strong>
                <span>{STAGES[entry.stage].label}</span>
                <small>{STAGES[entry.stage].hint}</small>
                <i aria-hidden="true" style={{ width: `${(entry.count / max) * 100}%` }} />
              </button>
            </li>
          ))}
        </ol>
      ) : <p className="muted">Cargando funnel…</p>}
    </section>
  );
}

function renewUrl(customer: Customer) {
  const text = `Hola ${customer.firstName}, tu membresía Private Club de SSENSUUM ya venció. Renuévala para seguir con masajes a $1,200 y tu masaje de cumpleaños de regalo. ¿Te la activamos?`;
  return `https://wa.me/52${customer.phone}?text=${encodeURIComponent(text)}`;
}

export function CustomersPage() {
  const [query, setQuery] = useState('');
  const [stage, setStage] = useState<FunnelStage | null>(null);
  const [customers, setCustomers] = useState<CustomerWithStage[] | null>(null);
  const [funnel, setFunnel] = useState<FunnelSummary | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState('');

  const load = useCallback((text: string, stageFilter: FunnelStage | null) => {
    return searchCustomers(text, stageFilter ?? undefined)
      .then((rows) => { setCustomers(rows); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, []);

  const loadFunnel = useCallback(() => {
    getCustomerFunnel().then(setFunnel).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => load(query, stage), 250);
    return () => clearTimeout(timer);
  }, [query, stage, load]);

  useEffect(loadFunnel, [loadFunnel]);

  return (
    <main className="bookingShell" data-testid="customers-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Clientes</h1>
        </div>
        <AdminNav current="clientes" />

        <ImportPanel onImported={() => { load(query, stage); loadFunnel(); }} />

        <FunnelCard funnel={funnel} stage={stage} onSelect={(next) => { setCustomers(null); setStage(next); }} />

        {selected ? <CustomerProfileCard customerId={selected} onClose={() => setSelected(null)} /> : null}

        <section className="adminCard">
          <div className="adminRow adminRowSpread">
            <h2>{stage ? STAGES[stage].label : 'Registro'}</h2>
            <select
              className="adminSearch adminSelect"
              aria-label="Filtrar por etapa"
              value={stage ?? ''}
              onChange={(event) => { setCustomers(null); setStage((event.target.value || null) as FunnelStage | null); }}
              data-testid="stage-filter"
            >
              <option value="">Todas las etapas</option>
              {funnel?.stages.map((entry) => <option key={entry.stage} value={entry.stage}>{`${STAGES[entry.stage].label} (${entry.count})`}</option>)}
            </select>
            <input
              type="search"
              className="adminSearch"
              placeholder="Buscar por nombre o teléfono"
              aria-label="Buscar clientes"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          {error ? <div className="errorBox" role="alert">{error}</div> : null}
          {customers === null && !error ? <p className="muted">Cargando clientes…</p> : null}
          {customers?.length === 0 ? <p className="muted">{query.trim() || stage ? 'Ningún cliente coincide con la búsqueda.' : 'Aún no hay clientes registrados.'}</p> : null}

          {customers && customers.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Nombre</th><th>Etapa</th><th>Visitas</th><th>Teléfono</th><th>Membresía</th><th>Correo</th><th>Cumpleaños</th><th>Notas</th></tr></thead>
                <tbody>
                  {customers.map((customer) => (
                    <tr key={customer.id} data-testid="customer-row">
                      <td>
                        <button type="button" className="hrLink" onClick={() => setSelected(customer.id)} aria-label={`Ver ficha de ${`${customer.firstName} ${customer.lastName}`.trim()}`}>
                          {`${customer.firstName} ${customer.lastName}`.trim() || 'Sin nombre'}
                        </button>
                      </td>
                      <td><StageBadge stage={customer.stage} /></td>
                      <td className="customerVisits">
                        {customer.visits}
                        {customer.lastVisit ? <span className="adminSub">Última: {shortDate(customer.lastVisit)}</span> : null}
                      </td>
                      <td>{formatPhone(customer.phone)}</td>
                      <td>{(() => {
                        const status = membership(customer);
                        if (!status) return '—';
                        return (
                          <>
                            <span className={`statusBadge ${status.active ? 'ok' : 'wait'}`}>{status.label}</span>
                            {!status.active ? <a className="adminSub" href={renewUrl(customer)} target="_blank" rel="noreferrer">Invitar a renovar</a> : null}
                          </>
                        );
                      })()}</td>
                      <td>{customer.email ?? '—'}</td>
                      <td>{customer.birthday ?? '—'}</td>
                      <td>{customer.notes ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          {customers && customers.length === 200 ? <p className="muted">Se muestran los primeros 200. Usa la búsqueda para encontrar a alguien más.</p> : null}
        </section>
      </div>
    </main>
  );
}
