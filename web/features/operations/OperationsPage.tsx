'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AdminNav } from '../../components/AdminNav';
import { getOpsMeta } from '../../lib/api';
import type { OpsMeta } from '../../lib/types';
import { DayPanel } from './DayPanel';
import { ReviewPanel } from './ReviewPanel';
import { SuppliesPanel } from './SuppliesPanel';
import { ZonesPanel } from './ZonesPanel';

function shift(day: string, delta: number) {
  const [year, month, date] = day.split('-').map(Number);
  const next = new Date(year, month - 1, date + delta);
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${next.getFullYear()}-${pad(next.getMonth() + 1)}-${pad(next.getDate())}`;
}

function longDay(day: string) {
  const [year, month, date] = day.split('-').map(Number);
  return new Date(year, month - 1, date).toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' });
}

export function OperationsPage() {
  const [meta, setMeta] = useState<OpsMeta | null>(null);
  const [day, setDay] = useState('');
  const [tab, setTab] = useState<'dia' | 'insumos' | 'revision' | 'zonas'>('dia');
  const [error, setError] = useState('');

  useEffect(() => {
    getOpsMeta().then((value) => { setMeta(value); setDay(value.today); }).catch((e: Error) => setError(e.message));
  }, []);

  return (
    <main className="bookingShell" data-testid="operations-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Operación</h1>
        </div>
        <AdminNav current="operacion" />
        <p className="muted">Lo que recepción hace cada día: limpieza por zona, insumos, publicaciones y cierre.</p>

        <div className="adminRow" role="tablist" aria-label="Secciones de operación">
          <button type="button" role="tab" aria-selected={tab === 'dia'} className={`secondaryButton ${tab === 'dia' ? 'selected' : ''}`} onClick={() => setTab('dia')}>Día</button>
          <button type="button" role="tab" aria-selected={tab === 'insumos'} className={`secondaryButton ${tab === 'insumos' ? 'selected' : ''}`} onClick={() => setTab('insumos')}>Insumos</button>
          <button type="button" role="tab" aria-selected={tab === 'revision'} className={`secondaryButton ${tab === 'revision' ? 'selected' : ''}`} onClick={() => setTab('revision')}>Revisión</button>
          <button type="button" role="tab" aria-selected={tab === 'zonas'} className={`secondaryButton ${tab === 'zonas' ? 'selected' : ''}`} onClick={() => setTab('zonas')}>Zonas y puntos</button>
        </div>

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        {!meta && !error ? <p className="muted">Cargando…</p> : null}

        {meta && tab === 'dia' && day ? (
          <>
            <div className="adminRow marketingPeriods opsDayNav">
              <button type="button" className="secondaryButton" onClick={() => setDay(shift(day, -1))} aria-label="Día anterior">←</button>
              <strong className="marketingMonth">{longDay(day)}</strong>
              <button type="button" className="secondaryButton" onClick={() => setDay(shift(day, 1))} aria-label="Día siguiente">→</button>
              {day !== meta.today ? <button type="button" className="linkButton" onClick={() => setDay(meta.today)}>Hoy</button> : null}
            </div>
            <DayPanel day={day} today={meta.today} />
          </>
        ) : null}
        {meta && tab === 'insumos' ? <SuppliesPanel /> : null}
        {meta && tab === 'revision' ? <ReviewPanel today={meta.today} /> : null}
        {meta && tab === 'zonas' ? <ZonesPanel meta={meta} /> : null}
      </div>
    </main>
  );
}
