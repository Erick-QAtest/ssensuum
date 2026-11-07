'use client';

import { useEffect, useState } from 'react';
import { getOpsEvidence, reviewOpsEvidence } from '../../lib/api';
import type { OpsEvidenceRow } from '../../lib/types';

const DAYS_BACK = 7;

function isoDaysAgo(today: string, days: number) {
  const [year, month, day] = today.split('-').map(Number);
  const value = new Date(year, month - 1, day - days);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`;
}

function when(iso: string) {
  return new Date(iso).toLocaleString('es-MX', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
}

// Revisión: la foto de referencia junto a la de evidencia, para aprobarla o pedir que se repita.
export function ReviewPanel({ today }: { today: string }) {
  const [rows, setRows] = useState<OpsEvidenceRow[] | null>(null);
  const [onlyPending, setOnlyPending] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    getOpsEvidence(isoDaysAgo(today, DAYS_BACK), today).then(setRows).catch((e: Error) => setError(e.message));
  }, [today]);

  function review(row: OpsEvidenceRow, value: 'bien' | 'repetir') {
    let note: string | undefined;
    if (value === 'repetir') {
      const answer = window.prompt('¿Qué hay que repetir?');
      if (answer === null) return;
      if (!answer.trim()) {
        setError('Escribe qué hay que repetir.');
        return;
      }
      note = answer;
    }
    setBusy(row.id);
    setError('');
    reviewOpsEvidence(row.id, value, note)
      .then((saved) => setRows((current) => (current ?? []).map((item) => (item.id === saved.id ? saved : item))))
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(''));
  }

  const visible = (rows ?? []).filter((row) => !onlyPending || row.review === 'pendiente');

  return (
    <section className="adminCard" data-testid="ops-review">
      <div className="adminRow adminRowSpread">
        <h2>Revisión de evidencia</h2>
        <label className="hrCheck">
          <input type="checkbox" checked={onlyPending} onChange={(event) => setOnlyPending(event.target.checked)} />
          Solo sin revisar
        </label>
      </div>
      <p className="muted">Fotos de los últimos {DAYS_BACK} días. A la izquierda, la foto de referencia; a la derecha, la de evidencia. Se borran a los 60 días.</p>
      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {rows === null && !error ? <p className="muted">Cargando…</p> : null}
      {rows && !visible.length ? <p className="muted">{onlyPending ? 'No hay fotos por revisar.' : 'No hay fotos en estos días.'}</p> : null}
      <ul className="opsReviewList">
        {visible.map((row) => (
          <li key={row.id} className="opsReviewItem" data-testid="ops-review-item">
            <div className="adminRow adminRowSpread opsTaskHead">
              <div>
                <h3>{row.zoneName}{row.pointLabel ? ` · ${row.pointLabel}` : ''}</h3>
                <span className="adminSub">{row.taskLabel} · {when(row.uploadedAt)}</span>
              </div>
              <span className={`statusBadge ${row.review === 'bien' ? 'ok' : 'wait'}`}>{row.reviewLabel}</span>
            </div>
            <div className="opsCompare">
              {/* eslint-disable @next/next/no-img-element */}
              {row.referenceUrl ? <img src={row.referenceUrl} alt={`Referencia de ${row.zoneName}`} /> : <p className="muted">Sin foto de referencia</p>}
              {row.url ? <img src={row.url} alt={`Evidencia de ${row.zoneName}`} /> : <p className="muted">La foto ya se borró (más de 60 días).</p>}
              {/* eslint-enable @next/next/no-img-element */}
            </div>
            {row.reviewNote ? <p className="opsReason">Repetir: {row.reviewNote}</p> : null}
            <div className="adminRow">
              <button type="button" className="primaryButton" disabled={busy === row.id} onClick={() => review(row, 'bien')}>Bien</button>
              <button type="button" className="secondaryButton" disabled={busy === row.id} onClick={() => review(row, 'repetir')}>Repetir</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
