'use client';

import { useRef, useState } from 'react';
import { importCustomers } from '../../lib/api';
import type { CustomerImportResult } from '../../lib/types';

const COLUMN_LABELS: Record<string, string> = {
  phone: 'Teléfono',
  firstName: 'Nombre',
  lastName: 'Apellido',
  email: 'Correo',
  birthday: 'Cumpleaños',
};
const STATUS_LABELS = { duplicate: 'Duplicado', invalid: 'Error', warning: 'Aviso' };

export function ImportPanel({ onImported }: { onImported: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [review, setReview] = useState<CustomerImportResult | null>(null);
  const [done, setDone] = useState<CustomerImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const reset = () => {
    setFile(null);
    setReview(null);
    setError('');
    if (input.current) input.current.value = '';
  };

  const run = (dryRun: boolean) => {
    if (!file) return;
    setBusy(true);
    setError('');
    importCustomers(file, dryRun)
      .then((result) => {
        if (dryRun) {
          setReview(result);
          return;
        }
        setDone(result);
        reset();
        onImported();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <section className="adminCard" data-testid="import-panel">
      <h2>Importar clientes existentes</h2>
      <p className="muted">
        Sube tu archivo de Excel (.xlsx) o CSV. La primera fila debe tener los encabezados: se necesita una columna de teléfono y una de nombre; apellido, correo y cumpleaños son opcionales.
      </p>

      <div className="adminRow">
        <input
          ref={input}
          type="file"
          accept=".xlsx,.csv"
          aria-label="Archivo de clientes"
          data-testid="import-file"
          onChange={(event) => { setFile(event.target.files?.[0] ?? null); setReview(null); setDone(null); setError(''); }}
        />
        <button type="button" className="secondaryButton" data-testid="import-review" disabled={!file || busy} onClick={() => run(true)}>
          {busy && !review ? 'Revisando…' : 'Revisar archivo'}
        </button>
      </div>

      {error ? <div className="errorBox" role="alert">{error}</div> : null}
      {done ? <div className="successBox" role="status" data-testid="import-done">Se importaron {done.created} clientes de {done.fileName}.</div> : null}

      {review ? (
        <div data-testid="import-summary">
          <dl className="adminStats">
            <div><dt>Filas con datos</dt><dd>{review.totalRows}</dd></div>
            <div><dt>Se importarán</dt><dd data-testid="import-valid">{review.valid}</dd></div>
            <div><dt>Duplicados</dt><dd>{review.duplicates}</dd></div>
            <div><dt>Con error</dt><dd>{review.invalid}</dd></div>
            <div><dt>Con avisos</dt><dd>{review.warnings}</dd></div>
          </dl>
          <p className="muted">
            Columnas detectadas: {Object.entries(review.columns).map(([field, header]) => `${COLUMN_LABELS[field]} ← “${header}”`).join(' · ')}
          </p>

          {review.issues.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>Fila</th><th>Estado</th><th>Nombre</th><th>Teléfono</th><th>Detalle</th></tr></thead>
                <tbody>
                  {review.issues.map((issue) => (
                    <tr key={`${issue.row}-${issue.status}`} data-testid="import-issue">
                      <td>{issue.row}</td>
                      <td><span className={`adminBadge adminBadge-${issue.status}`}>{STATUS_LABELS[issue.status]}</span></td>
                      <td>{issue.name || '—'}</td>
                      <td>{issue.phone || '—'}</td>
                      <td>{issue.messages.join('. ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          {review.issuesTruncated ? <p className="muted">Se muestran las primeras {review.issues.length} filas con observaciones.</p> : null}
          <p className="muted">Los duplicados y las filas con error no se importan. Las filas con aviso se importan sin el dato señalado.</p>

          <div className="adminRow">
            <button type="button" className="primaryButton" data-testid="import-confirm" disabled={review.valid === 0 || busy} onClick={() => run(false)}>
              {busy ? 'Importando…' : `Importar ${review.valid} clientes`}
            </button>
            <button type="button" className="secondaryButton" disabled={busy} onClick={reset}>Cancelar</button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
