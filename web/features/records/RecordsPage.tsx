'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AdminNav } from '../../components/AdminNav';
import { deleteServiceRecord, getServiceRecords, getServices, getTherapists } from '../../lib/api';
import { money } from '../../lib/format';
import type { Service, ServiceRecord, ServiceRecordSummary, Therapist } from '../../lib/types';
import { localIsoDate } from '../booking/dates';
import { RecordForm } from './RecordForm';
import { PAYMENT_METHODS, formatPhone, methodLabel, paidAtLabel } from './records';

type Range = { label: string; from: () => Date; days: () => number };

const RANGES: Range[] = [
  { label: 'Hoy', from: () => new Date(), days: () => 1 },
  { label: 'Ayer', from: () => { const d = new Date(); d.setDate(d.getDate() - 1); return d; }, days: () => 1 },
  { label: 'Últimos 7 días', from: () => { const d = new Date(); d.setDate(d.getDate() - 6); return d; }, days: () => 7 },
  { label: 'Este mes', from: () => { const d = new Date(); d.setDate(1); return d; }, days: () => new Date().getDate() },
];

export function RecordsPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  const [range, setRange] = useState(RANGES[0]);
  const [items, setItems] = useState<ServiceRecord[] | null>(null);
  const [summary, setSummary] = useState<ServiceRecordSummary | null>(null);
  const [editing, setEditing] = useState<ServiceRecord | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getServices(), getTherapists()])
      .then(([serviceRows, therapistRows]) => { setServices(serviceRows); setTherapists(therapistRows); })
      .catch((e: Error) => setError(e.message));
  }, []);

  const load = useCallback(() => {
    return getServiceRecords(localIsoDate(range.from()), range.days())
      .then((body) => { setItems(body.items); setSummary(body.summary); setError(''); })
      .catch((e: Error) => setError(e.message));
  }, [range]);

  useEffect(() => {
    setItems(null);
    load();
  }, [load]);

  async function remove(record: ServiceRecord) {
    if (!window.confirm(`¿Borrar el registro de ${record.customerName} (${record.serviceName})?`)) return;
    try {
      await deleteServiceRecord(record.id);
      if (editing?.id === record.id) setEditing(null);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <main className="bookingShell" data-testid="records-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Registro de servicios</h1>
        </div>
        <AdminNav current="registro" />

        <RecordForm
          services={services}
          therapists={therapists}
          editing={editing}
          onSaved={() => { setEditing(null); load(); }}
          onCancel={() => setEditing(null)}
        />

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

        {summary ? (
          <div className="adminStats">
            <div><strong>{summary.count}</strong><span>servicios</span></div>
            <div>
              <strong>{money(summary.amount)}</strong>
              <span>cobrado</span>
              <small className="adminSub">
                {PAYMENT_METHODS.filter((method) => summary.byPaymentMethod[method.id])
                  .map((method) => `${method.label} ${money(summary.byPaymentMethod[method.id] ?? 0)}`).join(' · ') || '—'}
              </small>
            </div>
            <div><strong>{money(summary.tips)}</strong><span>en propinas</span></div>
          </div>
        ) : null}

        {error ? <div className="errorBox" role="alert">{error}</div> : null}

        {summary && summary.tipsByTherapist.length > 0 ? (
          <section className="adminCard" data-testid="tips-summary">
            <h2>Propinas por terapeuta</h2>
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Terapeuta</th><th>Servicios con propina</th><th>Total</th></tr></thead>
                <tbody>
                  {summary.tipsByTherapist.map((entry) => (
                    <tr key={entry.therapistId}>
                      <td>{entry.therapistName}</td>
                      <td>{entry.count}</td>
                      <td><strong>{money(entry.amount)}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        <section className="adminCard">
          <h2>Servicios registrados</h2>
          {items === null && !error ? <p className="muted">Cargando registro…</p> : null}
          {items?.length === 0 ? <p className="muted">No hay servicios registrados en este periodo.</p> : null}
          {items && items.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Cobro</th><th>Cliente</th><th>Servicio</th><th>Monto</th><th>Propina</th><th></th></tr></thead>
                <tbody>
                  {items.map((record) => (
                    <tr key={record.id} data-testid="record-row">
                      <td>{paidAtLabel(record.paidAt)}</td>
                      <td>{record.customerName}<small className="adminSub">{formatPhone(record.customerPhone)}</small></td>
                      <td>{record.serviceName}<small className="adminSub">{record.therapistNames.join(' + ')}</small></td>
                      <td><strong>{money(record.amount)}</strong><small className="adminSub">{methodLabel(record.paymentMethod)}</small></td>
                      <td>
                        {record.tipTotal ? money(record.tipTotal) : '—'}
                        {record.tipTotal ? <small className="adminSub">{methodLabel(record.tipMethod)}</small> : null}
                      </td>
                      <td className="recordActions">
                        <button type="button" className="secondaryButton adminAction" onClick={() => { setEditing(record); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>Editar</button>
                        <button type="button" className="linkButton" onClick={() => remove(record)}>Borrar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
