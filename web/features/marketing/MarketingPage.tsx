'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AdminNav } from '../../components/AdminNav';
import { getMarketingMeta } from '../../lib/api';
import type { MarketingMeta } from '../../lib/types';
import { AttributionPanel } from './AttributionPanel';
import { CalendarPanel, type PostDraft } from './CalendarPanel';
import { IdeasPanel } from './IdeasPanel';
import { MetricsPanel } from './MetricsPanel';

const TABS = [
  { id: 'atribucion', label: 'Atribución' },
  { id: 'calendario', label: 'Calendario' },
  { id: 'metricas', label: 'Métricas' },
  { id: 'ideas', label: 'Ideas' },
] as const;
type Tab = (typeof TABS)[number]['id'];

export function MarketingPage() {
  const [meta, setMeta] = useState<MarketingMeta | null>(null);
  const [tab, setTab] = useState<Tab>('atribucion');
  const [draft, setDraft] = useState<PostDraft | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getMarketingMeta().then(setMeta).catch((e: Error) => setError(e.message));
  }, []);

  const schedule = useCallback((next: PostDraft) => {
    setDraft(next);
    setTab('calendario');
  }, []);
  const draftUsed = useCallback(() => setDraft(null), []);

  return (
    <main className="bookingShell" data-testid="marketing-page">
      <Link href="/" className="backLink">← Volver al sitio</Link>
      <div className="bookingPanel">
        <div className="bookingTitle">
          <span className="kicker">Administración</span>
          <h1>Marketing</h1>
        </div>
        <AdminNav current="marketing" />
        <p className="muted">Contenido orgánico en Instagram, TikTok, X y Facebook: qué se publica, cómo crece cada red y cuántos clientes trae.</p>

        <div className="adminRow" role="tablist" aria-label="Secciones de marketing">
          {TABS.map((option) => (
            <button
              key={option.id}
              type="button"
              role="tab"
              aria-selected={tab === option.id}
              className={`secondaryButton ${tab === option.id ? 'selected' : ''}`}
              onClick={() => setTab(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>

        {error ? <div className="errorBox" role="alert">{error}</div> : null}
        {!meta && !error ? <p className="muted">Cargando…</p> : null}
        {meta && tab === 'atribucion' ? <AttributionPanel meta={meta} /> : null}
        {meta && tab === 'calendario' ? <CalendarPanel meta={meta} draft={draft} onDraftUsed={draftUsed} /> : null}
        {meta && tab === 'metricas' ? <MetricsPanel meta={meta} /> : null}
        {meta && tab === 'ideas' ? <IdeasPanel meta={meta} onSchedule={schedule} /> : null}
      </div>
    </main>
  );
}
