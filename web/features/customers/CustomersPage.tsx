'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { searchCustomers } from '../../lib/api';
import type { Customer } from '../../lib/types';
import { AdminNav } from '../../components/AdminNav';
import { localIsoDate } from '../booking/dates';
import { ImportPanel } from './ImportPanel';

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

function renewUrl(customer: Customer) {
  const text = `Hola ${customer.firstName}, tu membresía Private Club de SSENSUUM ya venció. Renuévala para seguir con masajes a $1,200 y tu masaje de cumpleaños de regalo. ¿Te la activamos?`;
  return `https://wa.me/52${customer.phone}?text=${encodeURIComponent(text)}`;
}

export function CustomersPage() {
  const [query, setQuery] = useState('');
  const [customers, setCustomers] = useState<Customer[] | null>(null);
  const [error, setError] = useState('');

  const load = useCallback((text: string) => {
    return searchCustomers(text)
      .then((rows) => { setCustomers(rows); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => load(query), 250);
    return () => clearTimeout(timer);
  }, [query, load]);

  return (
    <main className="bookingShell" data-testid="customers-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Clientes</h1>
        </div>
        <AdminNav current="clientes" />

        <ImportPanel onImported={() => load(query)} />

        <section className="adminCard">
          <div className="adminRow adminRowSpread">
            <h2>Registro</h2>
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
          {customers?.length === 0 ? <p className="muted">{query.trim() ? 'Ningún cliente coincide con la búsqueda.' : 'Aún no hay clientes registrados.'}</p> : null}

          {customers && customers.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Nombre</th><th>Teléfono</th><th>Membresía</th><th>Correo</th><th>Cumpleaños</th><th>Notas</th></tr></thead>
                <tbody>
                  {customers.map((customer) => (
                    <tr key={customer.id} data-testid="customer-row">
                      <td>{`${customer.firstName} ${customer.lastName}`.trim()}</td>
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
